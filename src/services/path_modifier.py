"""
Path Modification Service
Phase 3: Dynamic Learning Path Updates

This service handles:
- Modifying learning paths based on user requests
- Adding/removing/updating resources
- Splitting/merging milestones
- Adjusting difficulty and duration
- Tracking all modifications
"""

from typing import Dict, List, Optional, Any
import json
import copy
from datetime import datetime
from web_app import db
from web_app.models import UserLearningPath, PathModification
from src.ml.model_orchestrator import ModelOrchestrator


class PathModifier:
    """
    Handles dynamic modifications to learning paths.
    
    Modification Types:
    - add_resource: Add a new resource to a milestone
    - remove_resource: Remove a resource from a milestone
    - modify_milestone: Update milestone properties
    - split_milestone: Split one milestone into multiple
    - merge_milestones: Combine multiple milestones
    - adjust_difficulty: Make content easier or harder
    - adjust_duration: Change time estimates
    """
    
    def __init__(self):
        """Initialize the path modifier."""
        self.orchestrator = ModelOrchestrator()
    
    def modify_path(
        self,
        learning_path_id: str,
        user_id: int,
        modification_request: str,
        entities: Dict,
        chat_message_id: Optional[int] = None
    ) -> Dict:
        """
        Modify a learning path based on user request.
        
        Args:
            learning_path_id: Learning path ID
            user_id: User ID
            modification_request: User's modification request
            entities: Extracted entities from intent classification
            chat_message_id: Optional chat message ID that triggered this
            
        Returns:
            Dictionary with modification result
        """
        # Get the learning path
        learning_path = UserLearningPath.query.get(learning_path_id)
        if not learning_path or learning_path.user_id != user_id:
            return {
                'success': False,
                'error': 'Learning path not found or access denied'
            }
        
        # Get current path data
        path_data = learning_path.path_data_json
        
        # Determine modification type and generate changes
        modification_plan = self._generate_modification_plan(
            modification_request,
            entities,
            path_data
        )
        
        if not modification_plan['success']:
            return modification_plan
        
        # Apply the modification
        try:
            modified_path = self._apply_modification(
                path_data,
                modification_plan
            )
            
            # Validate the modified path
            if not self._validate_path(modified_path):
                return {
                    'success': False,
                    'error': 'Modified path failed validation'
                }
            
            # Save the modification
            old_path_data = copy.deepcopy(path_data)
            learning_path.path_data_json = modified_path
            learning_path.last_accessed_at = datetime.utcnow()
            
            # Record the modification
            path_modification = PathModification(
                learning_path_id=learning_path_id,
                user_id=user_id,
                chat_message_id=chat_message_id,
                modification_type=modification_plan['type'],
                target_path=modification_plan.get('target_path'),
                change_description=modification_plan['description'],
                old_value=old_path_data,
                new_value=modified_path
            )
            
            db.session.add(path_modification)
            db.session.commit()
            
            return {
                'success': True,
                'modification_type': modification_plan['type'],
                'description': modification_plan['description'],
                'changes': modification_plan.get('changes', {}),
                'modified_path': modified_path
            }
            
        except Exception as e:
            db.session.rollback()
            print(f"Path modification error: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': f'Failed to apply modification: {str(e)}'
            }
    
    def _generate_modification_plan(
        self,
        request: str,
        entities: Dict,
        current_path: Dict
    ) -> Dict:
        """
        Generate a modification plan using AI.
        
        Args:
            request: User's modification request
            entities: Extracted entities
            current_path: Current learning path data
            
        Returns:
            Modification plan dictionary
        """
        # Build prompt for AI to generate modification plan
        prompt = f"""You are a learning path modification assistant. Generate a specific modification plan.

User request: "{request}"

Extracted entities: {json.dumps(entities, indent=2)}

Current learning path summary:
- Title: {current_path.get('title', 'Unknown')}
- Total milestones: {len(current_path.get('milestones', []))}
- Duration: {current_path.get('duration_weeks', 'Unknown')} weeks

Milestones:
{self._format_milestones_for_prompt(current_path.get('milestones', []))}

Generate a modification plan that includes:
1. Modification type (add_resource, remove_resource, modify_milestone, split_milestone, adjust_difficulty, etc.)
2. Target (which milestone/resource to modify)
3. Specific changes to make
4. Human-readable description of the change

Be specific and actionable."""
        
        schema = """
{
  "success": true,
  "type": "string (modification type)",
  "target_path": "string (JSON path to target, e.g., 'milestones[2]')",
  "description": "string (human-readable description)",
  "changes": {
    "action": "string (add, remove, update, split, etc.)",
    "target_index": "integer or null (milestone index)",
    "data": "object (specific changes to apply)"
  }
}
"""
        
        try:
            response = self.orchestrator.generate_structured_response(
                prompt=prompt,
                output_schema=schema,
                temperature=0.4,
                use_cache=False  # Don't cache modifications
            )
            
            plan = json.loads(response)
            return plan
            
        except Exception as e:
            print(f"Modification plan generation error: {e}")
            return {
                'success': False,
                'error': f'Failed to generate modification plan: {str(e)}'
            }
    
    def _apply_modification(self, path_data: Dict, plan: Dict) -> Dict:
        """
        Apply the modification plan to the path data.
        
        Args:
            path_data: Current path data
            plan: Modification plan
            
        Returns:
            Modified path data
        """
        modified_path = copy.deepcopy(path_data)
        changes = plan.get('changes', {})
        action = changes.get('action', '')
        
        if plan['type'] == 'add_resource':
            modified_path = self._add_resource(modified_path, changes)
        
        elif plan['type'] == 'remove_resource':
            modified_path = self._remove_resource(modified_path, changes)
        
        elif plan['type'] == 'modify_milestone':
            modified_path = self._modify_milestone(modified_path, changes)
        
        elif plan['type'] == 'split_milestone':
            modified_path = self._split_milestone(modified_path, changes)
        
        elif plan['type'] == 'adjust_difficulty':
            modified_path = self._adjust_difficulty(modified_path, changes)
        
        elif plan['type'] == 'adjust_duration':
            modified_path = self._adjust_duration(modified_path, changes)
        
        return modified_path
    
    def _add_resource(self, path_data: Dict, changes: Dict) -> Dict:
        """Add a resource to a milestone."""
        milestone_index = changes.get('target_index')
        new_resources = changes.get('data', {}).get('resources', [])
        
        if milestone_index is not None and 0 <= milestone_index < len(path_data.get('milestones', [])):
            if 'resources' not in path_data['milestones'][milestone_index]:
                path_data['milestones'][milestone_index]['resources'] = []
            
            path_data['milestones'][milestone_index]['resources'].extend(new_resources)
        
        return path_data
    
    def _remove_resource(self, path_data: Dict, changes: Dict) -> Dict:
        """Remove a resource from a milestone."""
        milestone_index = changes.get('target_index')
        resource_index = changes.get('data', {}).get('resource_index')
        
        if milestone_index is not None and resource_index is not None:
            milestones = path_data.get('milestones', [])
            if 0 <= milestone_index < len(milestones):
                resources = milestones[milestone_index].get('resources', [])
                if 0 <= resource_index < len(resources):
                    resources.pop(resource_index)
        
        return path_data
    
    def _modify_milestone(self, path_data: Dict, changes: Dict) -> Dict:
        """Modify milestone properties."""
        milestone_index = changes.get('target_index')
        updates = changes.get('data', {})
        
        if milestone_index is not None and 0 <= milestone_index < len(path_data.get('milestones', [])):
            milestone = path_data['milestones'][milestone_index]
            
            # Apply updates
            for key, value in updates.items():
                if key in milestone:
                    milestone[key] = value
        
        return path_data
    
    def _split_milestone(self, path_data: Dict, changes: Dict) -> Dict:
        """Split a milestone into multiple smaller milestones."""
        milestone_index = changes.get('target_index')
        new_milestones = changes.get('data', {}).get('new_milestones', [])
        
        if milestone_index is not None and new_milestones:
            milestones = path_data.get('milestones', [])
            if 0 <= milestone_index < len(milestones):
                # Remove original milestone and insert new ones
                milestones.pop(milestone_index)
                for i, new_milestone in enumerate(new_milestones):
                    milestones.insert(milestone_index + i, new_milestone)
        
        return path_data
    
    def _adjust_difficulty(self, path_data: Dict, changes: Dict) -> Dict:
        """Adjust difficulty of content."""
        milestone_index = changes.get('target_index')
        difficulty_change = changes.get('data', {}).get('difficulty')  # 'easier' or 'harder'
        
        if milestone_index is not None:
            milestone = path_data['milestones'][milestone_index]
            
            if difficulty_change == 'easier':
                # Reduce estimated hours, add more beginner resources
                current_hours = milestone.get('estimated_hours', 10)
                milestone['estimated_hours'] = max(2, int(current_hours * 0.7))
            
            elif difficulty_change == 'harder':
                # Increase estimated hours, add advanced resources
                current_hours = milestone.get('estimated_hours', 10)
                milestone['estimated_hours'] = int(current_hours * 1.3)
        
        return path_data
    
    def _adjust_duration(self, path_data: Dict, changes: Dict) -> Dict:
        """Adjust overall duration."""
        new_duration = changes.get('data', {}).get('duration_weeks')
        
        if new_duration:
            path_data['duration_weeks'] = new_duration
            
            # Recalculate total hours
            total_hours = sum(
                m.get('estimated_hours', 0)
                for m in path_data.get('milestones', [])
            )
            path_data['total_hours'] = total_hours
        
        return path_data
    
    def _validate_path(self, path_data: Dict) -> bool:
        """
        Validate that the modified path has all required fields.
        
        Args:
            path_data: Path data to validate
            
        Returns:
            True if valid, False otherwise
        """
        required_fields = ['title', 'description', 'milestones']
        
        for field in required_fields:
            if field not in path_data:
                return False
        
        # Validate milestones
        for milestone in path_data.get('milestones', []):
            if 'title' not in milestone or 'description' not in milestone:
                return False
        
        return True
    
    def _format_milestones_for_prompt(self, milestones: List[Dict]) -> str:
        """Format milestones for AI prompt."""
        formatted = []
        for i, milestone in enumerate(milestones):
            formatted.append(
                f"{i+1}. {milestone.get('title', 'Untitled')} "
                f"({milestone.get('estimated_hours', '?')} hours)"
            )
        return '\n'.join(formatted)
    
    def get_modification_history(
        self,
        learning_path_id: str,
        limit: int = 10
    ) -> List[PathModification]:
        """
        Get modification history for a learning path.
        
        Args:
            learning_path_id: Learning path ID
            limit: Maximum number of modifications to return
            
        Returns:
            List of PathModification objects
        """
        return PathModification.query.filter(
            PathModification.learning_path_id == learning_path_id
        ).order_by(
            PathModification.timestamp.desc()
        ).limit(limit).all()
    
    def undo_modification(
        self,
        modification_id: int,
        user_id: int
    ) -> Dict:
        """
        Undo a previous modification.
        
        Args:
            modification_id: Modification ID to undo
            user_id: User ID (for authorization)
            
        Returns:
            Result dictionary
        """
        modification = PathModification.query.get(modification_id)
        
        if not modification or modification.user_id != user_id:
            return {
                'success': False,
                'error': 'Modification not found or access denied'
            }
        
        if modification.is_reverted:
            return {
                'success': False,
                'error': 'Modification already reverted'
            }
        
        # Restore old value
        learning_path = UserLearningPath.query.get(modification.learning_path_id)
        if learning_path:
            learning_path.path_data_json = modification.old_value
            modification.is_reverted = True
            db.session.commit()
            
            return {
                'success': True,
                'message': 'Modification reverted successfully'
            }
        
        return {
            'success': False,
            'error': 'Learning path not found'
        }
