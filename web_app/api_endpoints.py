"""
API endpoints for chat and milestone tracking functionality.
"""
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from web_app.models import db, UserLearningPath, MilestoneProgress, LearningProgress
from datetime import datetime

api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/me', methods=['GET'])
def current_user_api():
    if not current_user.is_authenticated:
        return jsonify({'authenticated': False}), 200
    return jsonify({
        'authenticated': True,
        'user': {
            'id': current_user.id,
            'username': current_user.username,
            'email': current_user.email,
            'display_name': current_user.display_name,
        }
    }), 200


@api_bp.route('/paths', methods=['GET'])
@login_required
def list_user_paths():
    paths = UserLearningPath.query.filter_by(
        user_id=current_user.id,
        is_archived=False
    ).order_by(UserLearningPath.created_at.desc()).all()
    return jsonify({'paths': [{
        'id': path.id,
        'title': path.title,
        'topic': path.topic,
        'created_at': path.created_at.isoformat() if path.created_at else None,
        'path': path.path_data_json,
    } for path in paths]}), 200


@api_bp.route('/paths/<path_id>', methods=['GET'])
@login_required
def get_user_path(path_id):
    path = UserLearningPath.query.filter_by(id=path_id, user_id=current_user.id).first()
    if path is None:
        return jsonify({'error': 'Learning path not found or access denied'}), 404
    progress = LearningProgress.query.filter_by(user_learning_path_id=path.id).all()
    milestone_progress = MilestoneProgress.query.filter_by(
        user_id=current_user.id,
        learning_path_id=path.id
    ).all()
    progress_by_key = {
        item.milestone_identifier: {
            'milestone_identifier': item.milestone_identifier,
            'status': item.status,
            'started_at': item.started_at.isoformat() if item.started_at else None,
            'completed_at': item.completed_at.isoformat() if item.completed_at else None,
        } for item in progress
    }
    for item in milestone_progress:
        if item.completed:
            progress_by_key[str(item.milestone_index)] = {
                'milestone_identifier': str(item.milestone_index),
                'status': 'completed',
                'started_at': None,
                'completed_at': item.completed_at.isoformat() if item.completed_at else None,
            }
    return jsonify({
        'path': path.path_data_json,
        'progress': list(progress_by_key.values())
    }), 200

@api_bp.route('/save-path', methods=['POST'])
@login_required
def save_path_json():
    """
    Save or update a learning path for the current user.
    Expects JSON: { path: <LearningPath dict> }
    Returns: { success, path_id }
    """
    try:
        payload = request.get_json(silent=True) or {}
        path_data = payload.get('path') or {}
        if not path_data or not isinstance(path_data, dict):
            return jsonify({'success': False, 'message': 'Invalid payload'}), 400

        path_id = path_data.get('id')
        if not path_id:
            import uuid as _uuid
            path_id = str(_uuid.uuid4())
            path_data['id'] = path_id

        # Upsert user path
        user_path = UserLearningPath.query.filter_by(
            id=path_id,
            user_id=current_user.id
        ).first()

        if user_path:
            user_path.path_data_json = path_data
            user_path.title = path_data.get('title', 'Untitled Path')
            user_path.topic = path_data.get('topic', 'General')
        else:
            user_path = UserLearningPath(
                id=path_id,
                user_id=current_user.id,
                path_data_json=path_data,
                title=path_data.get('title', 'Untitled Path'),
                topic=path_data.get('topic', 'General')
            )
            db.session.add(user_path)

        db.session.commit()

        # Ensure progress rows exist
        try:
            milestones = path_data.get('milestones', [])
            for i, _ in enumerate(milestones):
                exists = LearningProgress.query.filter_by(
                    user_learning_path_id=path_id,
                    milestone_identifier=str(i)
                ).first()
                if not exists:
                    db.session.add(LearningProgress(
                        user_learning_path_id=path_id,
                        milestone_identifier=str(i),
                        status='not_started'
                    ))
            db.session.commit()
        except Exception as _e:
            current_app.logger.warning(f"Failed to seed LearningProgress rows: {_e}")
            db.session.rollback()

        return jsonify({'success': True, 'path_id': path_id}), 200
    except Exception as e:
        current_app.logger.error(f"Error saving path: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Failed to save path'}), 500

@api_bp.route('/track-milestone', methods=['POST'])
@login_required
def track_milestone():
    """
    Track milestone completion status.
    Expects JSON: {path_id, milestone_index, completed}
    """
    try:
        data = request.get_json()
        path_id = data.get('path_id')
        milestone_index = data.get('milestone_index')
        completed = data.get('completed', False)
        
        if not path_id or milestone_index is None:
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400
        
        # Verify the path belongs to the user
        user_path = UserLearningPath.query.filter_by(
            id=path_id,
            user_id=current_user.id
        ).first()
        
        if not user_path:
            return jsonify({'success': False, 'message': 'Learning path not found or access denied'}), 404
        
        # Find or create milestone progress entry
        progress = MilestoneProgress.query.filter_by(
            user_id=current_user.id,
            learning_path_id=path_id,
            milestone_index=milestone_index
        ).first()
        
        if not progress:
            progress = MilestoneProgress(
                user_id=current_user.id,
                learning_path_id=path_id,
                milestone_index=milestone_index,
                completed=completed
            )
            db.session.add(progress)
        else:
            progress.completed = completed
            progress.completed_at = datetime.utcnow() if completed else None
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Milestone status updated successfully'
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error tracking milestone: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Failed to update milestone status'}), 500


@api_bp.route('/ask', methods=['POST'])
@login_required
def ask_question():
    """
    Chat endpoint for asking questions about the learning path.
    Uses advanced RAG search to provide contextual answers.
    Expects JSON: {question, path_id}
    """
    try:
        data = request.get_json()
        question = data.get('question', '').strip()
        path_id = data.get('path_id')
        
        if not question:
            return jsonify({
                'success': False,
                'message': 'Question cannot be empty'
            }), 400
        
        if not path_id:
            return jsonify({
                'success': False,
                'message': 'Path ID is required'
            }), 400
        
        # Verify the path belongs to the user
        user_path = UserLearningPath.query.filter_by(
            id=path_id,
            user_id=current_user.id
        ).first()
        
        if not user_path:
            return jsonify({
                'success': False,
                'message': 'Learning path not found or access denied'
            }), 404
        
        # Get the learning path data
        path_data = user_path.path_data_json
        topic = path_data.get('topic', 'this topic')
        
        # Imported lazily: the vector/ML stack must not be a hard requirement
        # for the Flask API process to start.
        from src.data.document_store import DocumentStore
        document_store = DocumentStore()
        
        # Search for relevant documents
        relevant_docs = document_store.advanced_rag_search(
            query=f"{topic}: {question}",
            collection_name="learning_resources",
            top_k=3,
            use_cache=True
        )
        
        # Build context from retrieved documents
        context = "\n\n".join([doc.page_content for doc in relevant_docs]) if relevant_docs else ""
        
        # Generate answer using the model orchestrator
        from src.ml.model_orchestrator import ModelOrchestrator
        orchestrator = ModelOrchestrator()
        orchestrator.init_language_model()
        
        prompt = f"""You are a helpful AI tutor for a learning path about {topic}.

User's question: {question}

Context from learning resources:
{context}

Please provide a clear, concise, and helpful answer to the user's question. Focus on being educational and encouraging. If the context doesn't contain relevant information, use your general knowledge about {topic} to provide a helpful response.

Answer:"""
        
        answer = orchestrator.generate_response(
            prompt=prompt,
            use_cache=False,
            temperature=0.7
        )
        
        return jsonify({
            'success': True,
            'data': {
                'answer': answer.strip(),
                'sources_count': len(relevant_docs)
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error processing question: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': 'An error occurred while processing your question'
        }), 500
