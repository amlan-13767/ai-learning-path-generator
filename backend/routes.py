"""
API Routes for task management
"""
import os
import uuid
import json
from flask import Blueprint, request, jsonify
from flask_login import current_user, login_required
from web_app import db
from web_app.models import LearningProgress, UserLearningPath
from rq import Queue
from datetime import datetime
import redis

api_bp = Blueprint('rq_api', __name__)

# Redis connection
# Note: decode_responses=False is required for RQ (job results are pickled bytes, not strings)
REDIS_URL = os.getenv('REDIS_URL')
if REDIS_URL and REDIS_URL.startswith(('redis://', 'rediss://')):
    if REDIS_URL.startswith('rediss://'):
        # TLS endpoint: allow self-signed certs if provider uses them
        redis_client = redis.from_url(REDIS_URL, decode_responses=False, ssl_cert_reqs=None)
    else:
        # Non-TLS endpoint: do not pass TLS-only kwargs
        redis_client = redis.from_url(REDIS_URL, decode_responses=False)
else:
    redis_client = redis.Redis(
        host=os.getenv('REDIS_HOST', 'localhost'),
        port=int(os.getenv('REDIS_PORT', 6379)),
        db=int(os.getenv('REDIS_DB', 0)),
        decode_responses=False
    )


def _job_error(job):
    """Return a user-safe message while keeping tracebacks in worker logs."""
    details = job.exc_info or ''
    if 'credit_balance_exhausted' in details or 'insufficient_quota' in details or 'no credits remaining' in details.lower():
        return 'OpenAI API credits are exhausted. Add credits to the OpenAI account or configure a funded API key, then try again.'
    return 'Learning path generation failed. Check the worker logs and try again.'


def _save_path_for_user(path_data, user_id):
    path_id = path_data.get('id') or str(uuid.uuid4())
    path_data['id'] = path_id
    user_path = UserLearningPath.query.filter_by(id=path_id, user_id=user_id).first()
    if user_path is None:
        user_path = UserLearningPath(
            id=path_id,
            user_id=user_id,
            path_data_json=path_data,
            title=path_data.get('title', 'Untitled Path'),
            topic=path_data.get('topic', 'General')
        )
        db.session.add(user_path)
    else:
        user_path.path_data_json = path_data
        user_path.title = path_data.get('title', 'Untitled Path')
        user_path.topic = path_data.get('topic', 'General')
    db.session.flush()
    for index, _ in enumerate(path_data.get('milestones', [])):
        exists = LearningProgress.query.filter_by(
            user_learning_path_id=path_id,
            milestone_identifier=str(index)
        ).first()
        if exists is None:
            db.session.add(LearningProgress(
                user_learning_path_id=path_id,
                milestone_identifier=str(index),
                status='not_started'
            ))
    db.session.commit()
    return path_data


def _owned_job(job):
    return job is not None and int(job.meta.get('user_id', -1)) == int(current_user.id)

@api_bp.route('/generate', methods=['POST'])
@login_required
def generate_path():
    """
    Queue a learning path generation task using RQ.
    Returns the job ID immediately.
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['topic', 'expertise_level', 'duration_weeks', 'time_commitment']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Enqueue job on RQ queue
        q = Queue('learning-paths', connection=redis_client)
        job = q.enqueue('worker.tasks.generate_learning_path_for_worker', data)
        job.meta['user_id'] = current_user.id
        job.save_meta()
        
        return jsonify({
            "task_id": job.id,
            "status": "queued",
            "message": "Learning path generation started"
        }), 202
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route('/status/<task_id>', methods=['GET'])
@login_required
def get_status(task_id):
    """
    Get the current status of an RQ job
    """
    try:
        q = Queue('learning-paths', connection=redis_client)
        job = q.fetch_job(task_id)
        if not _owned_job(job):
            return jsonify({"error": "Task not found"}), 404
        
        resp = {
            "task_id": job.id,
            "status": job.get_status()
        }
        if job.is_finished:
            resp["result"] = job.result
        if job.is_failed:
            resp["error"] = _job_error(job)
        return jsonify(resp), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route('/result/<task_id>', methods=['GET'])
@login_required
def get_result(task_id):
    """
    Get the final result of an RQ job
    """
    try:
        q = Queue('learning-paths', connection=redis_client)
        job = q.fetch_job(task_id)
        if not _owned_job(job):
            return jsonify({"error": "Task not found"}), 404
        
        if not job.is_finished:
            return jsonify({
                "error": "Task not yet complete",
                "status": job.get_status()
            }), 202

        if job.is_failed:
            return jsonify({
                "error": _job_error(job),
                "status": job.get_status()
            }), 502
        
        path_data = _save_path_for_user(job.result, current_user.id)
        return jsonify(path_data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
