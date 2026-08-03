import os
import subprocess
from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt, jwt_required

ai_bp = Blueprint('ai_bp', __name__)


def _is_admin():
    claims = get_jwt()
    return (claims.get('role') or '').lower() == 'admin'


def _workspace_paths():
    backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    frontend_root = os.path.abspath(os.path.join(backend_root, '..', 'traveling-star-frontend'))
    return backend_root, frontend_root


def _select_task(task):
    normalized = (task or '').strip().lower()

    backend_root, frontend_root = _workspace_paths()

    task_map = [
        (
            {'build frontend', 'frontend build', 'build site'},
            {
                'id': 'build-frontend',
                'label': 'Build frontend project',
                'cwd': frontend_root,
                'command': ['npm', 'run', 'build'],
            }
        ),
        (
            {'test backend', 'backend tests', 'run backend tests'},
            {
                'id': 'test-backend',
                'label': 'Run backend tests',
                'cwd': backend_root,
                'command': ['pytest', '-q'],
            }
        ),
        (
            {'git status', 'repo status', 'status'},
            {
                'id': 'repo-status',
                'label': 'Check backend repository status',
                'cwd': backend_root,
                'command': ['git', 'status', '--short'],
            }
        ),
        (
            {'show routes', 'list routes', 'api routes'},
            {
                'id': 'list-routes',
                'label': 'List API route files',
                'cwd': backend_root,
                'command': ['python', '-c', "from pathlib import Path; print('\\n'.join(sorted(str(p) for p in Path('routes').glob('*_routes.py'))))"],
            }
        ),
        (
            {'build pages', 'pages build', 'build static'},
            {
                'id': 'build-pages',
                'label': 'Build Pages project',
                'cwd': os.path.abspath(os.path.join(backend_root, 'travelingstarservice-pages')),
                'command': ['npm', 'run', 'build'],
            }
        )
    ]

    for aliases, task_data in task_map:
        if normalized in aliases:
            return task_data

    return None


@ai_bp.post('/terminal')
@jwt_required()
def ai_terminal():
    if not _is_admin():
        return jsonify({'error': 'admin access required'}), 403

    data = request.get_json() or {}
    task = data.get('task')
    execute = bool(data.get('execute', False))

    selected = _select_task(task)
    if not selected:
        return jsonify({
            'error': 'unsupported task',
            'supported_tasks': [
                'build frontend',
                'test backend',
                'git status',
                'show routes',
                'build pages'
            ]
        }), 400

    if not execute:
        return jsonify({
            'message': 'Task prepared. Set execute=true to run it.',
            'task': selected['id'],
            'label': selected['label'],
            'cwd': selected['cwd'],
            'command': selected['command']
        })

    if not os.path.isdir(selected['cwd']):
        return jsonify({'error': f"task directory missing: {selected['cwd']}"}), 400

    started_at = datetime.utcnow()
    try:
        completed = subprocess.run(
            selected['command'],
            cwd=selected['cwd'],
            check=False,
            capture_output=True,
            text=True,
            timeout=120
        )
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'task timed out after 120 seconds'}), 408
    except FileNotFoundError as exc:
        return jsonify({'error': f'command executable not found: {exc}'}), 400

    output = (completed.stdout or '').strip()
    errors = (completed.stderr or '').strip()

    return jsonify({
        'task': selected['id'],
        'label': selected['label'],
        'command': selected['command'],
        'cwd': selected['cwd'],
        'exit_code': completed.returncode,
        'stdout': output,
        'stderr': errors,
        'started_at': started_at.isoformat(),
        'finished_at': datetime.utcnow().isoformat()
    })
