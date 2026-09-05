from datetime import datetime
import os
import json
from pathlib import Path

from flask import Blueprint, request, jsonify, session, current_app, send_from_directory, abort, Response, stream_with_context, make_response
from flask_login import current_user, login_required
from web_app.models import db, UserLearningPath, LearningProgress, ChatMessage, ResourceProgress
# Pre-existing bug: Queue was used by /api/generate-task and /api/task-status
# but never imported, so both raised NameError on every call.
from rq import Queue
import uuid
import time

# Define the blueprint
# JSON-only blueprint. The Jinja templates it used to render (index/dashboard/
# result/login) were the old purple UI and have been removed, so there is
# no template_folder any more.
bp = Blueprint('main', __name__)

# ResourceManager pulls in the heavy ML/vector stack, so it is imported
# lazily: the Flask API can then boot and be tested without LangChain.
def get_resource_manager():
    if not hasattr(current_app, 'resource_manager'):
        current_app.logger.info("Initializing ResourceManager for main_routes...")
        try:
            from src.data.resources import ResourceManager
            current_app.resource_manager = ResourceManager()
        except Exception as e:
            current_app.logger.error(f"Failed to initialize ResourceManager in main_routes: {e}")
            current_app.resource_manager = None
    return current_app.resource_manager

# ============================================
# API ENDPOINT FOR BACKGROUND TASK CREATION (RQ)
# ============================================

@bp.route('/api/generate-task', methods=['POST'])
@login_required
def generate_task():
    """
    Enqueues a learning path generation task to the RQ worker.
    Returns a task ID for the client to poll for status.
    """
    try:
        data = request.json
        topic = data.get('topic')
        if not topic:
            return jsonify({'error': 'Topic is required'}), 400

        # Get the Redis connection from the app context (will be set up in create_app)
        if getattr(current_app, 'redis', None) is None:
            current_app.logger.error('REDIS_URL not configured on web service; background queue unavailable')
            return jsonify({'error': 'Background queue unavailable', 'detail': 'REDIS_URL not configured on web service'}), 503
        redis_conn = current_app.redis
        q = Queue('learning-paths', connection=redis_conn)

        # Enqueue the job to the worker
        # The function to execute is passed as a string to avoid import issues
        job = q.enqueue('worker.tasks.generate_learning_path_for_worker', data)
        # Stamp the owner so /api/task-status cannot leak another user's result.
        job.meta['user_id'] = current_user.id
        job.save_meta()

        current_app.logger.info(f"Enqueued job {job.id} for topic '{topic}'")

        # Return the job ID to the client
        return jsonify({'task_id': job.id}), 202

    except Exception as e:
        current_app.logger.error(f"Error in /api/generate-task: {str(e)}")
        return jsonify({'error': 'Failed to create task'}), 500


@bp.route('/api/task-status/<task_id>', methods=['GET'])
@login_required
def task_status(task_id):
    """
    Checks the status of an RQ job.
    Returns the job status and, if finished, the result.
    """
    try:
        if getattr(current_app, 'redis', None) is None:
            return jsonify({'error': 'Background queue unavailable', 'detail': 'REDIS_URL not configured on web service'}), 503
        redis_conn = current_app.redis
        q = Queue('learning-paths', connection=redis_conn)
        job = q.fetch_job(task_id)

        if job is None or int(job.meta.get('user_id', -1)) != int(current_user.id):
            return jsonify({'status': 'not found'}), 404

        response = {
            'task_id': job.id,
            'status': job.get_status(),
        }

        if job.is_finished:
            response['result'] = job.result
        elif job.is_failed:
            response['error'] = str(job.exc_info)

        return jsonify(response)

    except Exception as e:
        current_app.logger.error(f"Error fetching task status for {task_id}: {str(e)}")
        return jsonify({'error': 'Failed to fetch task status'}), 500


# ============================================
# SERVER-SENT EVENTS (SSE) STREAMING ENDPOINT
# ============================================

@bp.route('/load_paths', methods=['GET'])
def load_paths():
    if request.method == 'GET':
        if current_user.is_authenticated:
            user_paths = UserLearningPath.query.filter_by(user_id=current_user.id).all()
            paths = [path.to_dict() for path in user_paths]
            return jsonify({'success': True, 'paths': paths})
        else:
            # Anonymous users have no saved paths
            return jsonify({'success': True, 'paths': []})

@bp.route('/upload_document', methods=['POST'])
def upload_document():
    resource_manager = get_resource_manager()
    if not resource_manager:
        return jsonify({'success': False, 'error': 'ResourceManager not available'}), 500
        
    if 'document' not in request.files:
        return jsonify({'success': False, 'error': 'No document part in the request'}), 400
    file = request.files['document']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No selected file'}), 400
    
    if file:
        filename = secure_filename(file.filename)
        # Ensure UPLOAD_FOLDER is configured on current_app by create_app
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads') 
        # Create absolute path for upload_folder if it's relative
        if not os.path.isabs(upload_folder):
            upload_folder = os.path.join(current_app.root_path, upload_folder)
        os.makedirs(upload_folder, exist_ok=True)
        
        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)
        
        try:
            resource_manager.add_document(file_path)
            return jsonify({'success': True, 'message': f'Document "{filename}" uploaded and processed successfully.'})
        except Exception as e:
            current_app.logger.error(f"Error processing uploaded document {filename}: {str(e)}")
            return jsonify({'success': False, 'error': f'Failed to process document: {str(e)}'}), 500
    return jsonify({'success': False, 'error': 'File upload failed for an unknown reason.'}), 500

@bp.route('/api/save_path', methods=['POST'])
def api_save_path():
    path_data = session.get('current_path')
    if not path_data:
        return jsonify({'success': False, 'error': 'No path in session to save.'}), 400
    
    # This is a placeholder. Actual saving will involve database operations with UserLearningPath model.
    # For now, let's simulate saving to a file or just acknowledge.
    # from flask_login import current_user
    # if not current_user.is_authenticated:
    #     return jsonify({'success': False, 'error': 'User must be logged in to save paths.'}), 401

    # path_title = path_data.get('title', 'Untitled Path')
    # file_name = f"{current_user.id}_{secure_filename(path_title)}.json"
    # save_dir = Path(current_app.root_path) / 'user_saved_paths'
    # save_dir.mkdir(exist_ok=True)
    # file_path = save_dir / file_name
    # with open(file_path, 'w') as f:
    #     json.dump(path_data, f, indent=4)

    # current_app.logger.info(f"Path '{path_title}' saved for user {current_user.id} to {file_path}")
    current_app.logger.info(f"Path save requested (placeholder): {path_data.get('title')}")
    return jsonify({'success': True, 'message': 'Path saved successfully (placeholder).'}) 

# Routes for progress tracking and path management
@bp.route('/update_progress', methods=['POST'])
@login_required
def update_progress():
    """Update the progress of a milestone in a learning path"""
    data = request.get_json()
    
    if not data or 'path_id' not in data or 'milestone_identifier' not in data or 'is_completed' not in data:
        return jsonify({'status': 'error', 'message': 'Missing required data'}), 400
    
    path_id = str(data['path_id'])
    milestone_identifier = str(data['milestone_identifier'])
    status = data['is_completed']

    valid_statuses = {'completed', 'in_progress', 'not_started'}
    if status not in valid_statuses:
        return jsonify({'status': 'error', 'message': 'Invalid status value'}), 400

    # Ensure the path belongs to the current user
    user_path = UserLearningPath.query.filter_by(
        id=path_id,
        user_id=current_user.id
    ).first()

    if not user_path:
        current_app.logger.warning(
            f"Progress update denied. Path {path_id} not found for user {current_user.id}"
        )
        return jsonify({'status': 'error', 'message': 'Learning path not found'}), 404

    # Ensure milestone index exists within path data
    path_data = user_path.path_data_json
    milestones = path_data.get('milestones', []) if path_data else []
    try:
        milestone_index = int(milestone_identifier)
    except ValueError:
        milestone_index = None

    if milestone_index is None or milestone_index < 0 or milestone_index >= len(milestones):
        return jsonify({'status': 'error', 'message': 'Invalid milestone identifier'}), 400

    # Find or create the progress entry
    progress = LearningProgress.query.filter_by(
        user_learning_path_id=path_id,
        milestone_identifier=milestone_identifier
    ).first()

    if not progress:
        progress = LearningProgress(
            user_learning_path_id=path_id,
            milestone_identifier=milestone_identifier
        )
        db.session.add(progress)

    old_status = progress.status
    progress.status = status

    if status == 'completed':
        progress.completed_at = datetime.utcnow()
        if not progress.started_at:
            progress.started_at = progress.completed_at
    elif status == 'in_progress':
        if not progress.started_at:
            progress.started_at = datetime.utcnow()
        progress.completed_at = None
    else:  # not_started
        progress.started_at = None
        progress.completed_at = None

    db.session.commit()

    # Recompute progress summary
    progress_entries = LearningProgress.query.filter_by(
        user_learning_path_id=path_id
    ).all()

    completed = sum(1 for p in progress_entries if p.status == 'completed')
    total = len(milestones)
    progress_percentage = int((completed / total) * 100) if total > 0 else 0

    current_app.logger.info(
        f"Progress updated for user {current_user.id}, path {path_id}, milestone {milestone_identifier}: {old_status} -> {status}"
    )

    return jsonify({
        'status': 'success',
        'message': 'Progress updated',
        'progress_percentage': progress_percentage,
        'completed': completed,
        'total': total
    })

@bp.route('/archive_path', methods=['POST'])
@login_required
def archive_path():
    """Archive or unarchive a learning path"""
    data = request.get_json()
    
    if not data or 'path_id' not in data:
        return jsonify({'status': 'error', 'message': 'Missing path_id'}), 400
    
    path_id = data['path_id']
    archive_action = data.get('archive', True)  # Default to archive if not specified
    
    # Find the path
    path = UserLearningPath.query.filter_by(
        user_id=current_user.id,
        id=path_id
    ).first()
    
    if not path:
        return jsonify({'status': 'error', 'message': 'Path not found'}), 404
    
    # Update archive status
    path.is_archived = archive_action
    db.session.commit()
    
    action_text = "archived" if archive_action else "unarchived"
    return jsonify({
        'status': 'success',
        'message': f'Path {action_text} successfully',
        'is_archived': archive_action
    })

@bp.route('/delete_path', methods=['POST'])
@login_required
def delete_path():
    """Permanently delete a learning path for the current user."""
    data = request.get_json() or {}
    path_id = data.get('path_id')
    if not path_id:
        return jsonify({'status': 'error', 'message': 'Missing path_id'}), 400

    # Locate path
    path = UserLearningPath.query.filter_by(user_id=current_user.id, id=path_id).first()
    if not path:
        return jsonify({'status': 'error', 'message': 'Path not found'}), 404

    # Remove from DB
    db.session.delete(path)
    db.session.commit()
    return jsonify({'status': 'success', 'message': 'Path deleted'})

import os
from openai import OpenAI

@bp.route('/chatbot_query', methods=['POST'])
def chatbot_query():
    """
    Enhanced chatbot endpoint with conversation memory, intent classification,
    and path modification capabilities.
    
    Note: Login not required - works for both authenticated and anonymous users.
    """
    if current_app.config.get('DEV_MODE'):
        # Return stub data in dev mode
        learning_path = f"# {request.json.get('topic', 'Untitled Topic')} Learning Path (Stub Data)\n\n"
        learning_path += "## Week 1: Getting Started\n"
        learning_path += "- Introduction to the topic\n"
        learning_path += "- Key concepts and terminology\n"
        learning_path += f"- Why {request.json.get('topic', 'Untitled Topic')} is important\n\n"
        learning_path += "## Week 2: Core Concepts\n"
        learning_path += "- Deep dive into fundamentals\n"
        learning_path += "- Practical examples\n"
        learning_path += "- Common challenges\n"
        return jsonify({
            'topic': request.json.get('topic', 'Untitled Topic'),
            'learning_path': learning_path,
            'timestamp': datetime.utcnow().isoformat(),
            'mode': 'dev'
        })
    
    data = request.get_json()
    user_message = data.get('message')
    learning_path_id = data.get('learning_path_id') or data.get('path_id')

    if not user_message:
        return jsonify({'error': 'No message provided'}), 400

    try:
        # STATELESS CHATBOT - No database dependencies
        # Works for both authenticated and anonymous users
        from openai import OpenAI
        
        # Initialize OpenAI client
        openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # Get learning path context if available
        path_context = ""
        milestones_info = ""
        
        if learning_path_id:
            path_data = session.get('current_path')
            if path_data:
                topic = path_data.get('topic', 'Unknown')
                title = path_data.get('title', 'Unknown')
                path_context = f"\n\nContext: The user is viewing a learning path titled '{title}' about '{topic}'."
                
                # Add milestone information if available
                milestones = path_data.get('milestones', [])
                if milestones:
                    milestones_info = "\n\nMilestones in this path:\n"
                    for i, milestone in enumerate(milestones, 1):
                        milestone_title = milestone.get('title', f'Milestone {i}')
                        milestone_desc = milestone.get('description', 'No description')
                        milestones_info += f"{i}. {milestone_title}: {milestone_desc}\n"
        
        # Build the system prompt
        system_prompt = f"""You are a helpful AI learning assistant for an AI Learning Path Generator application.
        
Your role:
- Answer questions about the user's learning path
- Provide guidance on milestones and learning topics
- Help users understand how to modify and adapt their learning path
- **IMPORTANT: When users ask you to generate/create/plan a learning path, you MUST help them do so**
- Be concise, friendly, and supportive
- If asked about specific milestones, reference the milestone information provided

Path Generation Requests:
When a user asks you to "generate a path", "create a learning path", "plan for me", or similar:
1. Acknowledge their career transition goal or learning objective
2. Ask clarifying questions if needed:
   - Current expertise level (beginner/intermediate/advanced)
   - Time commitment (hours per week)
   - Learning style preference (visual, hands-on, reading, project-based)
   - Any specific goals or deadlines
3. Once you have enough information, provide a clear summary like:
   "Great! I'll help you create a personalized learning path for [TOPIC]. Based on what you've told me:
   - Topic: [topic]
   - Expertise Level: [level]
   - Time Commitment: [hours/week]
   - Learning Style: [style]
   
   I'm now generating your customized learning path. This will take a moment..."
   
4. Then return a response with the format: "GENERATE_PATH: [topic] | [expertise_level] | [time_commitment] | [learning_style]"

Example: If user says "I want to transition from mechanical engineering to data analyst":
- Extract topic: "Career transition from Mechanical Engineering to Data Analyst"
- Ask about expertise level if not mentioned
- Ask about time commitment if not mentioned
- Then respond with generation confirmation

Modification Capabilities:
- Users can adjust the pace of their learning (spend more or less time on topics)
- Users can add supplementary materials or resources
- Users can skip or reorder milestones based on their needs
- Users can generate a new path with different parameters if needed
- Users can download the path and edit it manually

{path_context}{milestones_info}

When users ask about modifications:
1. Acknowledge their request
2. Provide specific, actionable guidance
3. Suggest concrete ways to adapt the path
4. Remind them they can generate a new path if major changes are needed"""
        
        # Generate response using OpenAI directly
        completion = openai_client.chat.completions.create(
            model=os.getenv('DEFAULT_MODEL', 'gpt-4o-mini'),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            max_tokens=400
        )
        
        response_text = completion.choices[0].message.content.strip()
        
        # Check if the chatbot is requesting path generation
        if "GENERATE_PATH:" in response_text:
            # Extract the generation command
            parts = response_text.split("GENERATE_PATH:")[1].strip().split("|")
            if len(parts) >= 4:
                topic = parts[0].strip()
                expertise_level = parts[1].strip()
                time_commitment = parts[2].strip()
                learning_style = parts[3].strip()
                
                # Remove the GENERATE_PATH command from the response
                user_facing_response = response_text.split("GENERATE_PATH:")[0].strip()
                
                return jsonify({
                    'reply': user_facing_response,
                    'intent': 'generate_path',
                    'confidence': 1.0,
                    'action': 'generate_path',
                    'parameters': {
                        'topic': topic,
                        'expertise_level': expertise_level.lower(),
                        'time_commitment': time_commitment,
                        'learning_style': learning_style.lower()
                    }
                })
        
        return jsonify({
            'reply': response_text,
            'intent': 'general_query',
            'confidence': 0.9
        })
        
    except Exception as e:
        print(f"Error in chatbot_query: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'reply': "Sorry, I encountered an error. Please try again.",
            'error': str(e)
        }), 500


# ============================================
# MEMORY-ENABLED CHATBOT WITH CONVERSATION TRACKING
# ============================================

@bp.route('/chatbot-memory', methods=['POST'])
@login_required
def chatbot_memory():
    """
    Enhanced chatbot with conversation memory and context tracking.
    
    Features:
    - Remembers conversation history (last 5 messages)
    - Tracks learning path context and progress
    - Saves all messages to database
    - Supports multi-turn conversations
    - Provides "Start New Conversation" functionality
    """
    start_time = time.time()
    
    try:
        data = request.get_json()
        user_message = data.get('message')
        path_id = data.get('path_id')
        reset_conversation = data.get('reset_conversation', False)
        
        if not user_message:
            return jsonify({'error': 'No message provided'}), 400
        
        # Get or create conversation ID
        if reset_conversation or 'conversation_id' not in session:
            conversation_id = str(uuid.uuid4())
            session['conversation_id'] = conversation_id
            print(f"🆕 Started new conversation: {conversation_id}")
        else:
            conversation_id = session['conversation_id']
            print(f"💬 Continuing conversation: {conversation_id}")
        
        # Get conversation history (last 5 messages)
        history = ChatMessage.get_conversation_history(conversation_id, limit=5)
        
        # Build conversation history for prompt
        history_text = ""
        if history:
            history_text = "\n\nRecent conversation:\n"
            for msg in history:
                role_label = "User" if msg.role == "user" else "Assistant"
                history_text += f"{role_label}: {msg.message}\n"
        
        # Get learning path context
        path_context = ""
        current_milestone = None
        completed_count = 0
        total_count = 0
        
        if path_id:
            # Try to get from database first
            user_path = UserLearningPath.query.filter_by(
                id=path_id,
                user_id=current_user.id
            ).first()
            
            if user_path:
                path_data = user_path.path_data_json
            else:
                # Fallback to session
                path_data = session.get('current_path')
            
            if path_data:
                title = path_data.get('title', 'Unknown')
                topic = path_data.get('topic', 'Unknown')
                milestones = path_data.get('milestones', [])
                total_count = len(milestones)
                
                # Get progress information
                if user_path:
                    progress_records = LearningProgress.query.filter_by(
                        user_learning_path_id=path_id
                    ).all()
                    
                    completed_count = sum(1 for p in progress_records if p.status == 'completed')
                    
                    # Find current milestone (first not completed)
                    for i, milestone in enumerate(milestones):
                        progress = next((p for p in progress_records if p.milestone_identifier == str(i)), None)
                        if not progress or progress.status != 'completed':
                            current_milestone = milestone.get('title', f'Milestone {i+1}')
                            break
                
                # Build context
                path_context = f"""
Learning Path Context:
- Title: {title}
- Topic: {topic}
- Progress: {completed_count}/{total_count} milestones completed
- Current Focus: {current_milestone or 'Getting started'}

Milestones:
"""
                for i, milestone in enumerate(milestones[:5], 1):  # Show first 5
                    status = "✅" if i <= completed_count else "⏳"
                    path_context += f"{status} {i}. {milestone.get('title', f'Milestone {i}')}\n"
                
                if len(milestones) > 5:
                    path_context += f"... and {len(milestones) - 5} more milestones\n"
        
        # Build enhanced system prompt
        system_prompt = f"""You are a helpful AI learning assistant with memory of our conversation.

Your role:
- Answer questions about the user's learning path
- Provide guidance based on their current progress
- Remember context from previous messages in this conversation
- Be concise, friendly, and supportive
- Reference specific milestones when relevant

{path_context}
{history_text}

Current user question: {user_message}

Provide a helpful, context-aware response that acknowledges our conversation history."""
        
        # Generate AI response
        from openai import OpenAI
        openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        completion = openai_client.chat.completions.create(
            model=os.getenv('DEFAULT_MODEL', 'gpt-4o-mini'),
            messages=[
                {"role": "system", "content": system_prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        response_text = completion.choices[0].message.content.strip()
        tokens_used = completion.usage.total_tokens
        
        # Calculate response time
        response_time_ms = int((time.time() - start_time) * 1000)
        
        # Build context object
        context_obj = {
            'path_id': path_id,
            'path_title': path_data.get('title') if path_data else None,
            'completed_milestones': completed_count,
            'total_milestones': total_count,
            'current_milestone': current_milestone
        } if path_id else None
        
        # Save user message to database
        user_msg = ChatMessage(
            user_id=current_user.id,
            learning_path_id=path_id,
            conversation_id=conversation_id,
            message=user_message,
            role='user',
            context=context_obj,
            tokens_used=0
        )
        db.session.add(user_msg)
        
        # Save assistant response to database
        assistant_msg = ChatMessage(
            user_id=current_user.id,
            learning_path_id=path_id,
            conversation_id=conversation_id,
            message=response_text,
            role='assistant',
            context=context_obj,
            tokens_used=tokens_used,
            response_time_ms=response_time_ms
        )
        db.session.add(assistant_msg)
        
        db.session.commit()
        
        print(f"💾 Saved conversation messages (tokens: {tokens_used}, time: {response_time_ms}ms)")
        
        return jsonify({
            'reply': response_text,
            'conversation_id': conversation_id,
            'tokens_used': tokens_used,
            'response_time_ms': response_time_ms,
            'context': {
                'completed': completed_count,
                'total': total_count,
                'current_milestone': current_milestone
            }
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error in chatbot_memory: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'reply': "Sorry, I encountered an error. Please try again.",
            'error': str(e)
        }), 500


@bp.route('/chatbot/reset', methods=['POST'])
@login_required
def reset_conversation():
    """Reset the current conversation and start fresh."""
    if 'conversation_id' in session:
        old_id = session['conversation_id']
        del session['conversation_id']
        print(f"🔄 Reset conversation: {old_id}")
    
    return jsonify({'success': True, 'message': 'Conversation reset'})


@bp.route('/chatbot/history', methods=['GET'])
@login_required
def get_conversation_history():
    """Get the current conversation history."""
    conversation_id = session.get('conversation_id')
    
    if not conversation_id:
        return jsonify({'messages': []})
    
    messages = ChatMessage.get_conversation_history(conversation_id, limit=20)
    
    return jsonify({
        'conversation_id': conversation_id,
        'messages': [{
            'role': msg.role,
            'message': msg.message,
            'timestamp': msg.timestamp.isoformat(),
            'tokens_used': msg.tokens_used
        } for msg in messages]
    })


@bp.route('/chatbot-stream', methods=['POST'])
@login_required
def chatbot_stream():
    """
    Streaming chatbot endpoint for real-time responses.
    Uses Server-Sent Events (SSE) for streaming.
    
    Benefits:
    - Users see responses in real-time (better UX)
    - Same cost as regular responses
    - Perceived performance improvement
    """
    from flask import Response, stream_with_context
    from src.data.document_store import DocumentStore
    from src.ml.model_orchestrator import ModelOrchestrator
    import json
    
    data = request.get_json()
    question = data.get('message') or data.get('question', '')
    learning_path_topic = data.get('learning_path_topic', 'a general topic')
    learning_path_title = data.get('learning_path_title', 'your current learning path')
    
    if not question:
        return jsonify({'error': 'Question is required'}), 400
    
    def generate():
        try:
            # Use HYBRID search for better results
            document_store = DocumentStore()
            relevant_docs = document_store.hybrid_search(
                query=question,
                collection_name="learning_resources",
                top_k=3  # Fewer docs = lower cost
            )
            
            context_texts = [doc.page_content for doc in relevant_docs] if relevant_docs else []
            
            # Create prompt
            prompt = f"""Answer this question about the learning path titled '{learning_path_title}' (topic: '{learning_path_topic}'):

Question: {question}

Context from learning resources:
{chr(10).join(context_texts) if context_texts else 'No additional context available.'}

Provide a clear, helpful answer."""
            
            # Stream the response
            orchestrator = ModelOrchestrator()
            for chunk in orchestrator.generate_response_stream(
                prompt=prompt,
                relevant_documents=context_texts,
                temperature=0.7
            ):
                # Send as Server-Sent Event
                yield f"data: {json.dumps({'chunk': chunk})}\n\n"
            
            # Send completion signal
            yield f"data: {json.dumps({'done': True})}\n\n"
            
        except Exception as e:
            print(f"Streaming error: {str(e)}")
            import traceback
            traceback.print_exc()
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'
        }
    )


@bp.route('/direct_chat', methods=['POST'])
def direct_chat():
    """
    Interactive chat endpoint supporting conversational AI and learning path operations.
    Modes: 'Chat' (general conversation) or 'Path' (interactive path generation/modification)
    """
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        mode = data.get('mode', 'Chat')
        
        if not user_message:
            return jsonify({'error': 'No message provided'}), 400
        
        current_app.logger.info(f"Chat request - Mode: {mode}, Message: {user_message[:100]}")
        
        # Path mode: Interactive learning path generation and modification
        if mode == 'Path':
            # Check if user is asking to create a new path
            create_keywords = ['create', 'generate', 'make', 'build', 'new path', 'learning path for']
            is_creation_request = any(keyword in user_message.lower() for keyword in create_keywords)
            
            if is_creation_request:
                # Extract topic from message using simple heuristics
                topic = user_message
                for keyword in create_keywords:
                    if keyword in user_message.lower():
                        parts = user_message.lower().split(keyword)
                        if len(parts) > 1:
                            topic = parts[1].strip().strip('.,!?')
                            # Clean up common words
                            topic = topic.replace('a learning path for', '').replace('learning path', '').strip()
                            break
                
                # If we have a valid topic, suggest using the form or provide guidance
                if len(topic) > 2:
                    response = f"""I can help you create a learning path for **{topic}**! 

Here's what I recommend:

**Option 1: Use the Form Above** (Recommended)
- Scroll up to the "Create Your Learning Path" form
- Enter "{topic}" as your topic
- Select your expertise level and learning style
- Get a fully structured path with resources in minutes

**Option 2: Let's Plan Together**
Tell me more about:
- Your current skill level (beginner/intermediate/advanced)
- How much time you can dedicate per week
- Your preferred learning style (visual, hands-on, reading, etc.)
- Any specific goals you have

Which option works better for you?"""
                else:
                    response = """I'd love to help you create a learning path! 

To get started, please tell me:
1. **What topic** do you want to learn?
2. **Your current level** (beginner, intermediate, or advanced)
3. **Time commitment** (hours per week)

Or you can use the form above to generate a complete path instantly!"""
            
            # Check for modification requests
            elif any(word in user_message.lower() for word in ['modify', 'change', 'update', 'adjust', 'edit']):
                response = """To modify your learning path, you have several options:

**1. Adjust the Pace**
- Take more time on challenging topics
- Speed through familiar concepts
- Extend or compress the timeline

**2. Add Resources**
- Supplement with your own materials
- Add practice projects
- Include additional courses

**3. Skip or Reorder**
- Skip milestones you already know
- Reorder based on your priorities
- Focus on specific areas

**4. Generate a New Path**
- Use the form above with different parameters
- Change topic, duration, or learning style

What specific modification would you like to make?"""
            
            else:
                # General path-related conversation
                client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
                system_prompt = """You are an AI Learning Path Specialist. Help users:
- Understand how to create effective learning paths
- Plan their learning journey
- Choose the right topics and resources
- Set realistic goals and timelines

Be encouraging, practical, and guide them to use the form above for generating complete paths.
Keep responses concise and actionable."""
                
                completion = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ],
                    temperature=0.7
                )
                response = completion.choices[0].message.content
        
        # Chat mode: General conversation with path generation capability
        else:
            client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
            system_prompt = """You are a friendly AI Learning Assistant. You help users:
- Answer questions about learning and education
- Provide study tips and motivation
- Explain how the learning path generator works
- Have general conversations about their learning goals
- **IMPORTANT: When users ask you to generate/create/plan a learning path, you MUST help them do so**

Path Generation Requests:
When a user asks you to "generate a path", "create a learning path", "plan for me", "transition to", or similar:
1. Acknowledge their career transition goal or learning objective
2. Ask clarifying questions if needed:
   - Current expertise level (beginner/intermediate/advanced)
   - Time commitment (hours per week, e.g., "10 hours per week")
   - Learning style preference (visual, hands-on, reading, project-based)
3. Once you have enough information, provide a summary and then add this special marker:
   "GENERATE_PATH: [topic] | [expertise_level] | [time_commitment] | [learning_style]"

Example: If user says "I want to transition from mechanical engineering to data analyst":
- Topic: "Career transition from Mechanical Engineering to Data Analyst"
- Ask about expertise level if not mentioned (default: beginner)
- Ask about time commitment if not mentioned (default: 10 hours per week)
- Ask about learning style if not mentioned (default: hands-on)
- Then respond with: "GENERATE_PATH: Career transition from Mechanical Engineering to Data Analyst | beginner | 10 hours per week | hands-on"

Be warm, supportive, and concise."""
            
            completion = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.8
            )
            response = completion.choices[0].message.content
            
            # Check if the chatbot is requesting path generation
            if "GENERATE_PATH:" in response:
                # Extract the generation command
                parts = response.split("GENERATE_PATH:")[1].strip().split("|")
                if len(parts) >= 4:
                    topic = parts[0].strip()
                    expertise_level = parts[1].strip()
                    time_commitment = parts[2].strip()
                    learning_style = parts[3].strip()
                    
                    # Remove the GENERATE_PATH command from the response
                    user_facing_response = response.split("GENERATE_PATH:")[0].strip()
                    
                    return jsonify({
                        'success': True,
                        'response': user_facing_response,
                        'action': 'generate_path',
                        'parameters': {
                            'topic': topic,
                            'expertise_level': expertise_level.lower(),
                            'time_commitment': time_commitment,
                            'learning_style': learning_style.lower()
                        }
                    })
        
        return jsonify({'success': True, 'response': response})
    
    except Exception as e:
        current_app.logger.error(f"Error in /direct_chat: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'response': "I apologize, but I encountered an error. Please try again or use the form above to generate your learning path."
        }), 500


@bp.route('/chat_with_memory', methods=['POST'])
def chat_with_memory():
    """
    Enhanced chatbot endpoint with persistent conversation memory.
    
    Features:
    - Maintains conversation context across multiple messages
    - Stores all messages in database for history
    - Supports both authenticated and guest users
    - Automatically manages conversation sessions
    - Includes path generation capabilities
    """
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        conversation_id = data.get('conversation_id')
        learning_path_id = data.get('learning_path_id')
        
        if not user_message:
            return jsonify({'error': 'No message provided'}), 400
        
        # Generate a new conversation ID if not provided
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
            current_app.logger.info(f"Starting new conversation: {conversation_id}")
        
        # Get conversation history (last 10 messages for context window management)
        history = ChatMessage.get_conversation_history(conversation_id, limit=10)
        
        # Build message history for OpenAI API
        messages_for_api = []
        for msg in history:
            messages_for_api.append({
                "role": msg.role,
                "content": msg.message
            })
        
        # Add system prompt
        system_prompt = """You are a friendly AI Learning Assistant for a personalized learning path generator.

Your capabilities:
- Answer questions about learning and education
- Provide study tips and motivation
- Help users create personalized learning paths
- **IMPORTANT: When users ask to generate/create/plan a learning path, help them do so**

Path Generation:
When a user requests path generation (e.g., "I want to transition from X to Y", "create a path for Z"):
1. Acknowledge their goal
2. Ask clarifying questions if needed:
   - Expertise level (beginner/intermediate/advanced)
   - Time commitment (hours per week)
   - Learning style (visual, hands-on, reading, project-based)
3. Once you have the information, respond with:
   "GENERATE_PATH: [topic] | [expertise_level] | [time_commitment] | [learning_style]"

Example:
User: "I want to transition from mechanical engineering to data analyst"
You: "Great! I'll help you transition to data analysis. A few quick questions:
- What's your current level with data analysis? (beginner/intermediate/advanced)
- How many hours per week can you dedicate?"
User: "Beginner, 10 hours per week"
You: "Perfect! Creating your personalized path now...
GENERATE_PATH: Career transition from Mechanical Engineering to Data Analyst | beginner | 10 hours per week | hands-on"

Be warm, supportive, and conversational. Remember context from previous messages."""
        
        # Prepend system message
        api_messages = [{"role": "system", "content": system_prompt}] + messages_for_api + [{"role": "user", "content": user_message}]
        
        # Call OpenAI API
        from openai import OpenAI
        import time
        
        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        
        start_time = time.time()
        completion = client.chat.completions.create(
            model=os.getenv('DEFAULT_MODEL', 'gpt-4o-mini'),
            messages=api_messages,
            temperature=0.7,
            max_tokens=500
        )
        response_time_ms = int((time.time() - start_time) * 1000)
        
        ai_reply = completion.choices[0].message.content.strip()
        tokens_used = completion.usage.total_tokens if hasattr(completion, 'usage') else 0
        
        # Save user message to database (if authenticated)
        if current_user.is_authenticated:
            user_msg = ChatMessage(
                user_id=current_user.id,
                learning_path_id=learning_path_id,
                message=user_message,
                role='user',
                conversation_id=conversation_id,
                timestamp=datetime.utcnow()
            )
            db.session.add(user_msg)
        
        # Check if AI wants to generate a path
        action = None
        parameters = None
        
        if "GENERATE_PATH:" in ai_reply:
            parts = ai_reply.split("GENERATE_PATH:")[1].strip().split("|")
            if len(parts) >= 4:
                topic = parts[0].strip()
                expertise_level = parts[1].strip()
                time_commitment = parts[2].strip()
                learning_style = parts[3].strip()
                
                # Remove the command from user-facing response
                ai_reply = ai_reply.split("GENERATE_PATH:")[0].strip()
                
                action = 'generate_path'
                parameters = {
                    'topic': topic,
                    'expertise_level': expertise_level.lower(),
                    'time_commitment': time_commitment,
                    'learning_style': learning_style.lower()
                }
        
        # Save AI response to database (if authenticated)
        if current_user.is_authenticated:
            ai_msg = ChatMessage(
                user_id=current_user.id,
                learning_path_id=learning_path_id,
                message=ai_reply,
                role='assistant',
                conversation_id=conversation_id,
                tokens_used=tokens_used,
                response_time_ms=response_time_ms,
                timestamp=datetime.utcnow()
            )
            db.session.add(ai_msg)
            db.session.commit()
        
        response_data = {
            'reply': ai_reply,
            'conversation_id': conversation_id,
            'tokens_used': tokens_used,
            'response_time_ms': response_time_ms
        }
        
        if action:
            response_data['action'] = action
            response_data['parameters'] = parameters
        
        return jsonify(response_data)
        
    except Exception as e:
        current_app.logger.error(f"Error in /chat_with_memory: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'reply': "I apologize, but I encountered an error. Please try again.",
            'error': str(e)
        }), 500


@bp.route('/clear_conversation', methods=['POST'])
def clear_conversation():
    """
    Clear a conversation and start fresh.
    Returns a new conversation ID.
    """
    try:
        new_conversation_id = str(uuid.uuid4())
        return jsonify({
            'success': True,
            'conversation_id': new_conversation_id,
            'message': 'Conversation cleared. Starting fresh!'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/job_market', methods=['GET'])
def job_market():
    """Return real-time job-market snapshot using OpenAI search."""
    topic = request.args.get('topic', 'Data Scientist')
    try:
        stats = get_job_market_stats(topic)
        return jsonify(stats)
    except Exception as e:
        current_app.logger.error(f"Job market route failed: {e}")
        # fallback static numbers
        return jsonify({
            "open_positions": "5,000+",
            "salary_range": "$120,000 - $160,000",
            "employers": ["Big Tech Co", "Innovative Startup", "Data Insights Inc"],
            "error": str(e)
        }), 500

# ============================================
# PROGRESS TRACKING API ENDPOINTS
# ============================================

@bp.route('/api/progress/save', methods=['POST'])
@login_required
def save_progress():
    """
    Save or update learning progress for a milestone.
    
    Expected JSON payload:
    {
        "path_id": "uuid-string",
        "milestone_identifier": "milestone-title-or-index",
        "status": "not_started" | "in_progress" | "completed"
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        path_id = data.get('path_id')
        milestone_identifier = data.get('milestone_identifier')
        status = data.get('status', 'not_started')
        
        if not path_id or not milestone_identifier:
            return jsonify({
                'success': False,
                'message': 'Missing required fields: path_id and milestone_identifier'
            }), 400
        
        # Validate status value
        valid_statuses = ['not_started', 'in_progress', 'completed']
        if status not in valid_statuses:
            return jsonify({
                'success': False,
                'message': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'
            }), 400
        
        # Verify the path belongs to the current user
        user_path = UserLearningPath.query.filter_by(
            id=path_id,
            user_id=current_user.id
        ).first()
        
        if not user_path:
            return jsonify({
                'success': False,
                'message': 'Learning path not found or access denied'
            }), 404
        
        # Find or create progress record
        progress = LearningProgress.query.filter_by(
            user_learning_path_id=path_id,
            milestone_identifier=milestone_identifier
        ).first()
        
        if not progress:
            progress = LearningProgress(
                user_learning_path_id=path_id,
                milestone_identifier=milestone_identifier
            )
            db.session.add(progress)
        
        # Update progress status
        old_status = progress.status
        progress.status = status
        
        # Update timestamps based on status
        if status == 'in_progress' and not progress.started_at:
            progress.started_at = datetime.utcnow()
        elif status == 'completed':
            progress.completed_at = datetime.utcnow()
            if not progress.started_at:
                progress.started_at = datetime.utcnow()
        elif status == 'not_started':
            # Reset timestamps if reverting to not started
            progress.started_at = None
            progress.completed_at = None
        
        # Commit changes
        db.session.commit()
        
        current_app.logger.info(
            f"Progress saved: User {current_user.id}, Path {path_id}, "
            f"Milestone {milestone_identifier}, Status {old_status} -> {status}"
        )
        
        return jsonify({
            'success': True,
            'message': 'Progress saved successfully',
            'data': {
                'status': progress.status,
                'started_at': progress.started_at.isoformat() if progress.started_at else None,
                'completed_at': progress.completed_at.isoformat() if progress.completed_at else None
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error saving progress: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Failed to save progress: {str(e)}'
        }), 500


@bp.route('/api/progress/load/<path_id>', methods=['GET'])
@login_required
def load_progress(path_id):
    """
    Load all progress records for a specific learning path.
    
    Returns array of progress objects:
    [
        {
            "milestone_identifier": "...",
            "status": "completed",
            "started_at": "2025-01-01T12:00:00",
            "completed_at": "2025-01-02T15:30:00"
        },
        ...
    ]
    """
    try:
        # Verify the path belongs to the current user
        user_path = UserLearningPath.query.filter_by(
            id=path_id,
            user_id=current_user.id
        ).first()
        
        if not user_path:
            return jsonify({
                'success': False,
                'message': 'Learning path not found or access denied'
            }), 404
        
        # Get all progress records for this path
        progress_records = LearningProgress.query.filter_by(
            user_learning_path_id=path_id
        ).all()
        
        # Format response
        progress_data = []
        for record in progress_records:
            progress_data.append({
                'milestone_identifier': record.milestone_identifier,
                'status': record.status,
                'started_at': record.started_at.isoformat() if record.started_at else None,
                'completed_at': record.completed_at.isoformat() if record.completed_at else None,
                'notes': record.notes
            })
        
        return jsonify({
            'success': True,
            'data': progress_data
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error loading progress: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Failed to load progress: {str(e)}'
        }), 500


@bp.route('/download/<path_id>')
@login_required
def download_path(path_id):
    """
    Generate and download a learning path as a formatted text file.
    """
    try:
        # Find the path
        user_path = UserLearningPath.query.filter_by(
            id=path_id,
            user_id=current_user.id
        ).first()

        if not user_path:
            # Ownership is enforced server-side: no fallback to session data.
            return jsonify({'success': False, 'error': 'Learning path not found'}), 404
        path_data = user_path.path_data_json

        # Generate formatted text content
        content = f"""# {path_data.get('title', 'Learning Path')}

## Overview
**Topic:** {path_data.get('topic', 'N/A')}
**Expertise Level:** {path_data.get('expertise_level', 'N/A').title()}
**Duration:** {path_data.get('duration_weeks', 'N/A')} weeks
**Total Hours:** {path_data.get('total_hours', 'N/A')}

## Goals
{chr(10).join(f"• {goal}" for goal in path_data.get('goals', []))}

## Milestones
"""

        for i, milestone in enumerate(path_data.get('milestones', []), 1):
            content += f"""

### Milestone {i}: {milestone.get('title', 'Untitled')}
**Duration:** {milestone.get('estimated_hours', 0)} hours

{milestone.get('description', 'No description')}

**Skills you'll gain:**
{chr(10).join(f"• {skill}" for skill in milestone.get('skills_gained', []))}

**Recommended Resources:**
"""
            for resource in milestone.get('resources', []):
                content += f"• {resource.get('description', 'N/A')} ({resource.get('type', 'N/A')})"
                if resource.get('url'):
                    content += f" - {resource['url']}"
                content += "\n"

        # Add job market data if available
        job_data = path_data.get('job_market_data')
        if job_data and not job_data.get('error'):
            content += f"""

## Job Market Insights
**Open Positions:** {job_data.get('open_positions', 'N/A')}
**Average Salary:** {job_data.get('average_salary', 'N/A')}
**Trending Employers:** {', '.join(job_data.get('trending_employers', []))}
"""

        # Generate filename
        safe_title = "".join(c for c in path_data.get('title', 'learning-path') if c.isalnum() or c in (' ', '-', '_')).rstrip()
        filename = f"{safe_title.replace(' ', '_')}.txt"

        # Create response
        response = make_response(content)
        response.headers['Content-Type'] = 'text/plain'
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'

        return response

    except Exception as e:
        current_app.logger.error(f"Error downloading path {path_id}: {str(e)}")
        return jsonify({'success': False, 'error': 'Error generating download'}), 500


@bp.route('/api/track-resource', methods=['POST'])
@login_required
def track_resource():
    """
    API endpoint to track resource completion progress.
    Stores completion status in database for persistent tracking.
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        path_id = data.get('path_id')
        milestone_index = data.get('milestone_index')
        resource_index = data.get('resource_index')
        completed = data.get('completed', False)
        resource_url = data.get('resource_url', '')
        
        if path_id is None or milestone_index is None or resource_index is None:
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Verify the path belongs to the user
        user_path = UserLearningPath.query.filter_by(
            id=path_id,
            user_id=current_user.id
        ).first()
        
        if not user_path:
            return jsonify({'error': 'Learning path not found or access denied'}), 404
        
        # Find or create resource progress entry
        progress = ResourceProgress.query.filter_by(
            user_id=current_user.id,
            learning_path_id=path_id,
            milestone_index=milestone_index,
            resource_index=resource_index
        ).first()
        
        if not progress:
            # Create new progress entry
            progress = ResourceProgress(
                user_id=current_user.id,
                learning_path_id=path_id,
                milestone_index=milestone_index,
                resource_index=resource_index,
                resource_url=resource_url,
                completed=completed,
                completed_at=datetime.utcnow() if completed else None
            )
            db.session.add(progress)
        else:
            # Update existing entry
            progress.completed = completed
            progress.completed_at = datetime.utcnow() if completed else None
            progress.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        current_app.logger.info(
            f"Resource progress tracked: User {current_user.id}, "
            f"Path {path_id}, M{milestone_index}:R{resource_index}, "
            f"Completed: {completed}"
        )
        
        return jsonify({
            'success': True,
            'completed': completed,
            'message': 'Progress saved successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error tracking resource progress: {str(e)}")
        return jsonify({'error': 'Failed to save progress'}), 500


@bp.route('/api/get-resource-progress/<path_id>', methods=['GET'])
@login_required
def get_resource_progress(path_id):
    """
    Get all resource progress for a learning path.
    Returns a dictionary of completed resources.
    """
    try:
        # Verify the path belongs to the user
        user_path = UserLearningPath.query.filter_by(
            id=path_id,
            user_id=current_user.id
        ).first()
        
        if not user_path:
            return jsonify({'error': 'Learning path not found or access denied'}), 404
        
        # Get all progress entries for this path
        progress_entries = ResourceProgress.query.filter_by(
            user_id=current_user.id,
            learning_path_id=path_id
        ).all()
        
        # Build response dictionary
        progress_data = {}
        for entry in progress_entries:
            key = f"m{entry.milestone_index}_r{entry.resource_index}"
            progress_data[key] = {
                'completed': entry.completed,
                'completed_at': entry.completed_at.isoformat() if entry.completed_at else None
            }
        
        return jsonify({
            'success': True,
            'progress': progress_data
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error fetching resource progress: {str(e)}")
        return jsonify({'error': 'Failed to fetch progress'}), 500
