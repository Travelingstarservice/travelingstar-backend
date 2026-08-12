import os
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_migrate import Migrate
from sqlalchemy import inspect, text
from extensions import jwt, db
from models.user import User
from models.site_config import SiteConfig
from utils.logger import setup_logging

# Import all blueprints
from routes.auth_routes import auth_bp
from routes.event_routes import event_bp
from routes.booking_routes import booking_bp
from routes.settings_routes import settings_bp
from routes.support_routes import support_bp
from routes.podcast_routes import podcast_bp
from routes.payment_routes import payment_bp
from routes.ai_routes import ai_bp
from routes.dispatch_routes import dispatch_bp

# Initialize Flask-Migrate
migrate = Migrate()


def migrate_user_schema():
    """
    Legacy migration function for backward compatibility.
    New migrations should use Flask-Migrate.
    This function only runs for existing databases without proper migrations.
    """
    with db.engine.begin() as conn:
        inspector = inspect(conn)
        existing_tables = set(inspector.get_table_names())
        bool_default = '0' if conn.dialect.name == 'sqlite' else 'FALSE'

        if 'user' in existing_tables:
            user_columns = {col['name'] for col in inspector.get_columns('user')}
            if 'role' not in user_columns:
                conn.execute(text("ALTER TABLE \"user\" ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'user'"))
            if 'login_disabled' not in user_columns:
                conn.execute(text(f"ALTER TABLE \"user\" ADD COLUMN login_disabled BOOLEAN NOT NULL DEFAULT {bool_default}"))

        if 'booking' in existing_tables:
            booking_columns = {col['name'] for col in inspector.get_columns('booking')}
            if 'date' not in booking_columns:
                conn.execute(text("ALTER TABLE booking ADD COLUMN date VARCHAR(50) NOT NULL DEFAULT '2026-08-01'"))
            if 'status' not in booking_columns:
                conn.execute(text("ALTER TABLE booking ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'pending'"))
            if 'notes' not in booking_columns:
                conn.execute(text("ALTER TABLE booking ADD COLUMN notes TEXT"))
            if 'pickup_location' not in booking_columns:
                conn.execute(text("ALTER TABLE booking ADD COLUMN pickup_location VARCHAR(255)"))
            if 'dropoff_location' not in booking_columns:
                conn.execute(text("ALTER TABLE booking ADD COLUMN dropoff_location VARCHAR(255)"))
            if 'created_at' not in booking_columns:
                # SQLite doesn't support non-constant defaults in ALTER TABLE
                # Use a constant timestamp for migration
                conn.execute(text("ALTER TABLE booking ADD COLUMN created_at DATETIME NOT NULL DEFAULT '2026-08-07 00:00:00'"))
            if 'updated_at' not in booking_columns:
                conn.execute(text("ALTER TABLE booking ADD COLUMN updated_at DATETIME NOT NULL DEFAULT '2026-08-07 00:00:00'"))

        if 'event' in existing_tables:
            event_columns = {col['name'] for col in inspector.get_columns('event')}
            if 'image' not in event_columns:
                conn.execute(text("ALTER TABLE event ADD COLUMN image VARCHAR(255) NULL"))

        if 'fleet_job' in existing_tables:
            fleet_job_columns = {col['name'] for col in inspector.get_columns('fleet_job')}
            if 'job_app_source' not in fleet_job_columns:
                conn.execute(text("ALTER TABLE fleet_job ADD COLUMN job_app_source VARCHAR(80)"))
            if 'job_app_id' not in fleet_job_columns:
                conn.execute(text("ALTER TABLE fleet_job ADD COLUMN job_app_id VARCHAR(120)"))
            if 'job_app_url' not in fleet_job_columns:
                conn.execute(text("ALTER TABLE fleet_job ADD COLUMN job_app_url VARCHAR(500)"))
            if 'job_app_status' not in fleet_job_columns:
                conn.execute(text("ALTER TABLE fleet_job ADD COLUMN job_app_status VARCHAR(40)"))
            if 'earnings' not in fleet_job_columns:
                conn.execute(text("ALTER TABLE fleet_job ADD COLUMN earnings FLOAT"))
            if 'rating' not in fleet_job_columns:
                conn.execute(text("ALTER TABLE fleet_job ADD COLUMN rating FLOAT"))
            if 'tips' not in fleet_job_columns:
                conn.execute(text("ALTER TABLE fleet_job ADD COLUMN tips FLOAT"))


def seed_demo_admin():
    admin_email = 'admin@travelingstar.com'
    admin_password = os.getenv('ADMIN_PIN', '9404').strip()
    if len(admin_password) != 4 or not admin_password.isdigit():
        admin_password = '9404'
    admin = User.query.filter_by(email=admin_email).first()

    if admin is None:
        admin = User(email=admin_email, password=admin_password, role='admin')
        db.session.add(admin)
    else:
        admin.role = 'admin'
        if admin.login_disabled is None:
            admin.login_disabled = False

    db.session.commit()


def validate_sqlite_path(sqlite_path):
    sqlite_dir = os.path.dirname(sqlite_path) or '.'
    os.makedirs(sqlite_dir, exist_ok=True)

    dir_exists = os.path.isdir(sqlite_dir)
    dir_writable = os.access(sqlite_dir, os.W_OK)
    print(f"[startup] SQLITE_PATH={sqlite_path}")
    print(f"[startup] SQLITE_DIR={sqlite_dir} exists={dir_exists} writable={dir_writable}")

    if not dir_exists or not dir_writable:
        raise RuntimeError(
            f"SQLite directory is not writable: dir={sqlite_dir} path={sqlite_path}"
        )

    try:
        with open(sqlite_path, 'a'):
            pass
    except OSError as exc:
        raise RuntimeError(
            f"Cannot open SQLite file for write: path={sqlite_path} error={exc}"
        ) from exc


def parse_cors_origins(raw_value):
    value = (raw_value or '*').strip()
    if (value.startswith("'") and value.endswith("'")) or (value.startswith('"') and value.endswith('"')):
        value = value[1:-1].strip()

    if not value:
        return '*'
    if value == '*':
        return '*'

    origins = [origin.strip() for origin in value.split(',') if origin.strip()]
    return origins or '*'


def resolve_cors_origin(cors_origins, request_origin):
    if cors_origins == '*':
        return '*'
    if not request_origin:
        return None
    if isinstance(cors_origins, list) and request_origin in cors_origins:
        return request_origin
    return None


def create_app():
    app = Flask(__name__)
    os.makedirs(app.instance_path, exist_ok=True)

    backend_root = os.path.dirname(__file__)
    candidate_frontend_dirs = [
        os.path.abspath(os.path.join(backend_root, '..', 'traveling-star-frontend', 'dist')),
        os.path.abspath(os.path.join(backend_root, 'traveling-star-frontend', 'dist')),
    ]
    app.config['FRONTEND_DIST_DIR'] = next((path for path in candidate_frontend_dirs if os.path.isdir(path)), candidate_frontend_dirs[0])

    # Config
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'traveling-star-demo-secret-key-1234567890')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    database_url = os.getenv('DATABASE_URL')
    if database_url:
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
        # Keep connection usage predictable on hosted Postgres plans.
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'pool_pre_ping': True,
            'pool_recycle': int(os.getenv('DB_POOL_RECYCLE', '280')),
            'pool_size': int(os.getenv('DB_POOL_SIZE', '3')),
            'max_overflow': int(os.getenv('DB_MAX_OVERFLOW', '2')),
            'pool_timeout': int(os.getenv('DB_POOL_TIMEOUT', '30')),
        }
    else:
        default_sqlite_path = os.path.join(app.instance_path, 'database.db')
        if os.getenv('RENDER') == 'true':
            default_sqlite_path = '/tmp/travelingstar/database.db'
        sqlite_path = os.path.abspath(os.getenv('SQLITE_PATH', default_sqlite_path))
        validate_sqlite_path(sqlite_path)
        app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{sqlite_path}"

    # Extensions
    cors_origins = parse_cors_origins(os.getenv('CORS_ALLOWED_ORIGINS', '*'))
    app.config['CORS_ALLOWED_ORIGINS'] = cors_origins

    @app.after_request
    def add_api_cors_headers(response):
        if request.path.startswith('/api/'):
            origin = request.headers.get('Origin')
            allowed_origin = resolve_cors_origin(app.config['CORS_ALLOWED_ORIGINS'], origin)
            if allowed_origin:
                response.headers['Access-Control-Allow-Origin'] = allowed_origin
                if allowed_origin != '*':
                    response.headers['Vary'] = 'Origin'

            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = request.headers.get(
                'Access-Control-Request-Headers',
                'Content-Type, Authorization',
            )
            response.headers['Access-Control-Max-Age'] = '86400'

        return response

    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": cors_origins,
                "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
                "allow_headers": ["Content-Type", "Authorization"],
                "max_age": 86400,
            }
        },
    )
    jwt.init_app(app)
    db.init_app(app)
    migrate.init_app(app, db)

    # Setup comprehensive logging
    setup_logging(app)

    with app.app_context():
        app.config['DB_READY'] = False
        try:
            db.create_all()
            try:
                migrate_user_schema()
            except Exception as exc:
                app.logger.exception('Non-fatal schema migration step failed during startup: %s', exc)
            try:
                seed_demo_admin()
            except Exception as exc:
                app.logger.exception('Non-fatal admin seed step failed during startup: %s', exc)
            app.config['DB_READY'] = True
        except Exception as exc:
            app.logger.exception('Database initialization failed during startup: %s', exc)

    @app.get('/')
    def home():
        frontend_dist_dir = app.config['FRONTEND_DIST_DIR']
        index_path = os.path.join(frontend_dist_dir, 'index.html')
        if os.path.isfile(index_path):
            return send_from_directory(frontend_dist_dir, 'index.html')

        return jsonify({
            'message': 'Traveling Star API'
        })

    @app.get('/healthz')
    def healthz():
        payload = {
            'status': 'ok',
            'db_ready': bool(app.config.get('DB_READY', False))
        }
        try:
            db.session.execute(text('SELECT 1'))
            payload['db_connected'] = True
        except Exception as exc:
            app.logger.exception('Health check failed: %s', exc)
            payload['db_connected'] = False

        # Keep this as a liveness probe so Render can keep the process up
        # even if the database is temporarily unavailable.
        return jsonify(payload), 200

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(event_bp, url_prefix='/api/events')
    app.register_blueprint(booking_bp, url_prefix='/api/bookings')
    app.register_blueprint(settings_bp, url_prefix='/api/settings')
    app.register_blueprint(support_bp, url_prefix='/api/support')
    app.register_blueprint(podcast_bp, url_prefix='/api/podcasts')
    app.register_blueprint(payment_bp, url_prefix='/api/payments')
    app.register_blueprint(ai_bp, url_prefix='/api/ai')
    app.register_blueprint(dispatch_bp, url_prefix='/api/dispatch')

    @app.route('/<path:path>')
    def serve_frontend(path):
        frontend_dist_dir = app.config['FRONTEND_DIST_DIR']
        if not os.path.isdir(frontend_dist_dir):
            return jsonify({'message': 'Traveling Star API'}), 404

        candidate_path = os.path.join(frontend_dist_dir, path)
        if os.path.isfile(candidate_path):
            return send_from_directory(frontend_dist_dir, path)

        return send_from_directory(frontend_dist_dir, 'index.html')

    return app


app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)), debug=False)
