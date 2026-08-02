import os
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from sqlalchemy import text
from extensions import jwt, db
from models.user import User

# Import all blueprints
from routes.auth_routes import auth_bp
from routes.event_routes import event_bp
from routes.booking_routes import booking_bp
from routes.settings_routes import settings_bp
from routes.support_routes import support_bp
from routes.podcast_routes import podcast_bp
from routes.payment_routes import payment_bp


def migrate_user_schema():
    with db.engine.begin() as conn:
        user_columns = {row[1] for row in conn.execute(text('PRAGMA table_info(user)'))}
        if 'role' not in user_columns:
            conn.execute(text("ALTER TABLE user ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'user'"))

        booking_columns = {row[1] for row in conn.execute(text('PRAGMA table_info(booking)'))}
        if 'date' not in booking_columns:
            conn.execute(text("ALTER TABLE booking ADD COLUMN date VARCHAR(50) NOT NULL DEFAULT '2026-08-01'"))

        event_columns = {row[1] for row in conn.execute(text('PRAGMA table_info(event)'))}
        if 'image' not in event_columns:
            conn.execute(text("ALTER TABLE event ADD COLUMN image VARCHAR(255) NULL"))


def seed_demo_admin():
    admin_email = 'admin@travelingstar.com'
    admin_password = os.getenv('ADMIN_PIN', '1234').strip()
    if len(admin_password) != 4 or not admin_password.isdigit():
        admin_password = '1234'
    admin = User.query.filter_by(email=admin_email).first()

    if admin is None:
        admin = User(email=admin_email, password=admin_password, role='admin')
        db.session.add(admin)
    else:
        admin.password = admin_password
        admin.role = 'admin'

    db.session.commit()


def create_app():
    app = Flask(__name__)
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
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(app.instance_path, 'database.db')}"

    # Extensions
    cors_origins = os.getenv('CORS_ALLOWED_ORIGINS', '*')
    CORS(app, resources={r"/api/*": {"origins": cors_origins}})
    jwt.init_app(app)
    db.init_app(app)

    with app.app_context():
        db.create_all()
        migrate_user_schema()
        seed_demo_admin()

    @app.get('/')
    def home():
        frontend_dist_dir = app.config['FRONTEND_DIST_DIR']
        index_path = os.path.join(frontend_dist_dir, 'index.html')
        if os.path.isfile(index_path):
            return send_from_directory(frontend_dist_dir, 'index.html')

        return jsonify({
            'message': 'Traveling Star API'
        })

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(event_bp, url_prefix='/api/events')
    app.register_blueprint(booking_bp, url_prefix='/api/bookings')
    app.register_blueprint(settings_bp, url_prefix='/api/settings')
    app.register_blueprint(support_bp, url_prefix='/api/support')
    app.register_blueprint(podcast_bp, url_prefix='/api/podcasts')
    app.register_blueprint(payment_bp, url_prefix='/api/payments')

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
