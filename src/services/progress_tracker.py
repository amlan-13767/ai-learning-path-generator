"""
Progress Tracking Service
Phase 4: Progress Analytics & Insights

This service handles:
- Calculating progress metrics
- Generating progress reports
- Providing personalized insights
- Tracking time spent and completion rates
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from web_app import db
from web_app.models import UserLearningPath, LearningProgress, User
from src.ml.model_orchestrator import ModelOrchestrator
import json


class ProgressTracker:
    """
    Tracks and analyzes user learning progress.
    
    Metrics:
    - Completion percentage
    - Time spent
    - Current milestone
    - Estimated completion date
    - Streak days
    - Skills acquired
    """
    
    def __init__(self):
        """Initialize the progress tracker."""
        self.orchestrator = ModelOrchestrator()
    
    def get_progress_summary(
        self,
        user_id: int,
        learning_path_id: str
    ) -> Dict:
        """
        Get comprehensive progress summary.
        
        Args:
            user_id: User ID
            learning_path_id: Learning path ID
            
        Returns:
            Dictionary with progress metrics and insights
        """
        # Get learning path
        learning_path = UserLearningPath.query.filter_by(
            id=learning_path_id,
            user_id=user_id
        ).first()
        
        if not learning_path:
            return {
                'error': 'Learning path not found'
            }
        
        path_data = learning_path.path_data_json
        milestones = path_data.get('milestones', [])
        
        # Get progress entries
        progress_entries = LearningProgress.query.filter_by(
            user_learning_path_id=learning_path_id
        ).all()
        
        # Calculate metrics
        completion_percentage = self._calculate_completion_percentage(
            milestones,
            progress_entries
        )
        
        time_spent = self._calculate_time_spent(progress_entries)
        
        current_milestone = self._get_current_milestone(
            milestones,
            progress_entries
        )
        
        estimated_completion = self._estimate_completion_date(
            learning_path,
            progress_entries,
            milestones
        )
        
        streak_days = self._calculate_streak(
            user_id,
            learning_path_id
        )
        
        skills_acquired = self._get_skills_acquired(
            milestones,
            progress_entries
        )
        
        pace_analysis = self._analyze_pace(
            learning_path,
            progress_entries,
            milestones
        )
        
        # Generate personalized insights
        insights = self._generate_insights(
            completion_percentage=completion_percentage,
            time_spent=time_spent,
            pace_analysis=pace_analysis,
            streak_days=streak_days,
            path_data=path_data
        )
        
        return {
            'completion_percentage': completion_percentage,
            'completed_milestones': len([p for p in progress_entries if p.status == 'completed']),
            'total_milestones': len(milestones),
            'time_spent_hours': time_spent,
            'current_milestone': current_milestone,
            'estimated_completion_date': estimated_completion,
            'streak_days': streak_days,
            'skills_acquired': skills_acquired,
            'pace_analysis': pace_analysis,
            'insights': insights,
            'learning_path_title': path_data.get('title', 'Unknown'),
            'started_at': learning_path.created_at.isoformat() if learning_path.created_at else None
        }
    
    def _calculate_completion_percentage(
        self,
        milestones: List[Dict],
        progress_entries: List[LearningProgress]
    ) -> float:
        """Calculate completion percentage."""
        if not milestones:
            return 0.0
        
        completed_count = len([
            p for p in progress_entries
            if p.status == 'completed'
        ])
        
        return round((completed_count / len(milestones)) * 100, 1)
    
    def _calculate_time_spent(
        self,
        progress_entries: List[LearningProgress]
    ) -> float:
        """Calculate total time spent in hours."""
        total_hours = 0.0
        
        for progress in progress_entries:
            if progress.started_at:
                if progress.completed_at:
                    # Calculate time between start and completion
                    delta = progress.completed_at - progress.started_at
                    total_hours += delta.total_seconds() / 3600
                elif progress.status == 'in_progress':
                    # Calculate time from start to now
                    delta = datetime.utcnow() - progress.started_at
                    total_hours += delta.total_seconds() / 3600
        
        return round(total_hours, 1)
    
    def _get_current_milestone(
        self,
        milestones: List[Dict],
        progress_entries: List[LearningProgress]
    ) -> Optional[Dict]:
        """Get the current milestone user is working on."""
        # Find first in_progress milestone
        for progress in progress_entries:
            if progress.status == 'in_progress':
                milestone_index = int(progress.milestone_identifier)
                if 0 <= milestone_index < len(milestones):
                    return {
                        'index': milestone_index,
                        'title': milestones[milestone_index].get('title', 'Unknown'),
                        'estimated_hours': milestones[milestone_index].get('estimated_hours', 0)
                    }
        
        # If no in_progress, find first not_started
        completed_indices = {
            int(p.milestone_identifier)
            for p in progress_entries
            if p.status == 'completed'
        }
        
        for i, milestone in enumerate(milestones):
            if i not in completed_indices:
                return {
                    'index': i,
                    'title': milestone.get('title', 'Unknown'),
                    'estimated_hours': milestone.get('estimated_hours', 0)
                }
        
        return None
    
    def _estimate_completion_date(
        self,
        learning_path: UserLearningPath,
        progress_entries: List[LearningProgress],
        milestones: List[Dict]
    ) -> Optional[str]:
        """Estimate completion date based on current pace."""
        completed_count = len([p for p in progress_entries if p.status == 'completed'])
        
        if completed_count == 0:
            # No progress yet, use original duration
            duration_weeks = learning_path.path_data_json.get('duration_weeks', 8)
            estimated_date = learning_path.created_at + timedelta(weeks=duration_weeks)
            return estimated_date.strftime('%Y-%m-%d')
        
        # Calculate average time per milestone
        total_time = self._calculate_time_spent(progress_entries)
        avg_time_per_milestone = total_time / completed_count if completed_count > 0 else 0
        
        # Estimate remaining time
        remaining_milestones = len(milestones) - completed_count
        estimated_remaining_hours = remaining_milestones * avg_time_per_milestone
        
        # Convert to days (assuming 2 hours per day)
        estimated_remaining_days = estimated_remaining_hours / 2
        
        estimated_date = datetime.utcnow() + timedelta(days=estimated_remaining_days)
        return estimated_date.strftime('%Y-%m-%d')
    
    def _calculate_streak(
        self,
        user_id: int,
        learning_path_id: str
    ) -> int:
        """Calculate current learning streak in days."""
        # Get all progress updates ordered by date
        progress_entries = LearningProgress.query.filter_by(
            user_learning_path_id=learning_path_id
        ).order_by(LearningProgress.started_at.desc()).all()
        
        if not progress_entries:
            return 0
        
        # Check for activity in the last 24 hours
        yesterday = datetime.utcnow() - timedelta(days=1)
        recent_activity = any(
            p.started_at and p.started_at >= yesterday
            for p in progress_entries
        )
        
        if not recent_activity:
            return 0
        
        # Count consecutive days with activity
        streak = 1
        current_date = datetime.utcnow().date()
        
        for i in range(1, 365):  # Max 365 days
            check_date = current_date - timedelta(days=i)
            
            has_activity = any(
                p.started_at and p.started_at.date() == check_date
                for p in progress_entries
            )
            
            if has_activity:
                streak += 1
            else:
                break
        
        return streak
    
    def _get_skills_acquired(
        self,
        milestones: List[Dict],
        progress_entries: List[LearningProgress]
    ) -> List[str]:
        """Get list of skills acquired from completed milestones."""
        skills = []
        
        completed_indices = {
            int(p.milestone_identifier)
            for p in progress_entries
            if p.status == 'completed'
        }
        
        for i in completed_indices:
            if 0 <= i < len(milestones):
                milestone_skills = milestones[i].get('skills_gained', [])
                skills.extend(milestone_skills)
        
        return list(set(skills))  # Remove duplicates
    
    def _analyze_pace(
        self,
        learning_path: UserLearningPath,
        progress_entries: List[LearningProgress],
        milestones: List[Dict]
    ) -> Dict:
        """Analyze learning pace compared to plan."""
        # Calculate expected progress
        days_since_start = (datetime.utcnow() - learning_path.created_at).days
        duration_weeks = learning_path.path_data_json.get('duration_weeks', 8)
        total_days = duration_weeks * 7
        
        expected_percentage = min(100, (days_since_start / total_days) * 100)
        
        # Calculate actual progress
        actual_percentage = self._calculate_completion_percentage(milestones, progress_entries)
        
        # Determine pace
        pace_diff = actual_percentage - expected_percentage
        
        if pace_diff > 10:
            pace_status = 'ahead'
            pace_description = f'ahead of schedule by {abs(int(pace_diff))}%'
        elif pace_diff < -10:
            pace_status = 'behind'
            pace_description = f'behind schedule by {abs(int(pace_diff))}%'
        else:
            pace_status = 'on_track'
            pace_description = 'on track'
        
        return {
            'status': pace_status,
            'description': pace_description,
            'expected_percentage': round(expected_percentage, 1),
            'actual_percentage': actual_percentage,
            'difference': round(pace_diff, 1)
        }
    
    def _generate_insights(
        self,
        completion_percentage: float,
        time_spent: float,
        pace_analysis: Dict,
        streak_days: int,
        path_data: Dict
    ) -> List[str]:
        """Generate personalized insights using AI."""
        # Build context for AI
        context = f"""
Learning Progress Analysis:
- Completion: {completion_percentage}%
- Time Spent: {time_spent} hours
- Pace: {pace_analysis['description']}
- Streak: {streak_days} days
- Path: {path_data.get('title', 'Unknown')}
- Total Milestones: {len(path_data.get('milestones', []))}
"""
        
        prompt = f"""Generate 3-5 personalized, motivational insights for a learner based on their progress.

{context}

Provide insights that:
1. Acknowledge their progress
2. Motivate them to continue
3. Offer specific suggestions
4. Are encouraging and positive

Format as a JSON array of strings."""
        
        try:
            response = self.orchestrator.generate_response(
                prompt=prompt,
                temperature=0.7,
                use_cache=False
            )
            
            # Try to parse as JSON array
            if response.strip().startswith('['):
                insights = json.loads(response)
                return insights[:5]  # Max 5 insights
            else:
                # Split by newlines and clean up
                insights = [
                    line.strip('- •*').strip()
                    for line in response.split('\n')
                    if line.strip() and len(line.strip()) > 10
                ]
                return insights[:5]
        
        except Exception as e:
            print(f"Insight generation error: {e}")
            # Fallback insights
            return self._generate_fallback_insights(
                completion_percentage,
                pace_analysis,
                streak_days
            )
    
    def _generate_fallback_insights(
        self,
        completion_percentage: float,
        pace_analysis: Dict,
        streak_days: int
    ) -> List[str]:
        """Generate fallback insights without AI."""
        insights = []
        
        if completion_percentage > 0:
            insights.append(f"Great start! You've completed {completion_percentage}% of your learning path.")
        
        if pace_analysis['status'] == 'ahead':
            insights.append(f"You're {pace_analysis['description']}! Keep up the excellent pace!")
        elif pace_analysis['status'] == 'behind':
            insights.append("Don't worry about the pace - consistent progress is what matters most!")
        else:
            insights.append("You're right on track with your learning schedule!")
        
        if streak_days > 0:
            insights.append(f"🔥 {streak_days}-day streak! Consistency is key to mastery.")
        
        if completion_percentage < 25:
            insights.append("The beginning is always the hardest. You've got this!")
        elif completion_percentage > 75:
            insights.append("You're in the home stretch! Finish strong!")
        
        return insights
    
    def update_milestone_progress(
        self,
        user_id: int,
        learning_path_id: str,
        milestone_identifier: str,
        status: str,
        notes: Optional[str] = None
    ) -> Dict:
        """
        Update progress for a specific milestone.
        
        Args:
            user_id: User ID
            learning_path_id: Learning path ID
            milestone_identifier: Milestone identifier
            status: New status ('not_started', 'in_progress', 'completed')
            notes: Optional notes
            
        Returns:
            Result dictionary
        """
        # Get or create progress entry
        progress = LearningProgress.query.filter_by(
            user_learning_path_id=learning_path_id,
            milestone_identifier=milestone_identifier
        ).first()
        
        if not progress:
            progress = LearningProgress(
                user_learning_path_id=learning_path_id,
                milestone_identifier=milestone_identifier
            )
            db.session.add(progress)
        
        # Update status
        old_status = progress.status
        progress.status = status
        
        if notes:
            progress.notes = notes
        
        # Update timestamps
        if status == 'in_progress' and not progress.started_at:
            progress.started_at = datetime.utcnow()
        elif status == 'completed' and not progress.completed_at:
            progress.completed_at = datetime.utcnow()
        
        db.session.commit()
        
        return {
            'success': True,
            'old_status': old_status,
            'new_status': status,
            'milestone_identifier': milestone_identifier
        }
