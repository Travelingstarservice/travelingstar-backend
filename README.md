# Traveling Star Backend

A Flask-based backend API for the Traveling Star Service transportation management system.

## Features

- **Authentication**: JWT-based authentication with admin/user roles
- **Rate Limiting**: Built-in rate limiting for API endpoints
- **Input Validation**: Comprehensive input validation and sanitization
- **Database Migrations**: Flask-Migrate for database schema management
- **Logging**: Structured logging with request tracking
- **CORS**: Configurable CORS support for frontend integration

## Project Structure

```
travelingstar-backend/
├── app.py                 # Main Flask application factory
├── config.py              # Configuration settings
├── extensions.py          # Flask extensions initialization
├── requirements.txt      # Python dependencies
├── routes/               # API route blueprints
│   ├── auth_routes.py    # Authentication endpoints
│   ├── booking_routes.py # Booking management
│   ├── event_routes.py   # Event management
│   ├── settings_routes.py # Admin settings
│   ├── dispatch_routes.py # Fleet dispatch
│   ├── payment_routes.py # Payment processing
│   ├── podcast_routes.py # Podcast generation
│   ├── ai_routes.py      # AI features
│   └── support_routes.py # Customer support
├── models/               # SQLAlchemy models
│   ├── user.py          # User model
│   ├── booking.py       # Booking model
│   ├── event.py         # Event model
│   ├── site_config.py   # Site configuration
│   ├── fleet_job.py     # Fleet dispatch jobs
│   └── support_message.py # Support messages
├── utils/                # Utility modules
│   ├── validators.py    # Input validation functions
│   ├── rate_limiter.py  # Rate limiting implementation
│   └── logger.py        # Logging configuration
├── migrations/           # Database migrations
├── logs/                # Application logs
└── tests/               # Test files
```

## Setup

### Prerequisites

- Python 3.11+
- pip
- Virtual environment (recommended)

### Installation

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set environment variables:
```bash
export ADMIN_PIN=2580
export JWT_SECRET_KEY=your-secret-key
export OWNER_RECOVERY_SECRET=your-recovery-secret
export DATABASE_URL=sqlite:///instance/database.db  # or PostgreSQL URL
```

4. Initialize database:
```bash
flask db upgrade
```

## Running the Application

### Development

```bash
python app.py
```

### Production

```bash
gunicorn app:app --bind 0.0.0.0:5000 --workers 1 --threads 2 --timeout 120
```

## API Endpoints

### Authentication

- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - User login
- `POST /api/auth/change-password` - Change password
- `GET /api/auth/me` - Get current user info
- `POST /api/auth/admin-password` - Change admin password
- `POST /api/auth/admin-password/strong` - Use strong password (enhanced security)
- `POST /api/auth/admin/access/lock` - Lock admin access
- `POST /api/auth/admin/access/unlock` - Unlock admin access
- `POST /api/auth/admin/access/recover` - Recover admin access

### Bookings

- `POST /api/bookings` - Create booking
- `GET /api/bookings` - List user bookings
- `GET /api/bookings/<id>` - Get booking details
- `PUT /api/bookings/<id>/status` - Update booking status (admin)
- `GET /api/bookings/admin/all` - List all bookings (admin)

### Events

- `GET /api/events` - List all events
- `POST /api/events` - Create event (admin)
- `GET /api/events/<id>` - Get event details
- `PUT /api/events/<id>` - Update event (admin)
- `DELETE /api/events/<id>` - Delete event (admin)
- `GET /api/events/analytics` - Event analytics (admin)

### Settings

- `GET /api/settings` - Get public settings
- `POST /api/settings` - Update settings (admin)
- `GET /api/settings/payments` - Get payment settings
- `POST /api/settings/payments` - Update payment settings (admin)

### Dispatch

- `GET /api/dispatch/config` - Get dispatch configuration
- `GET /api/dispatch/locator` - AI hotspot locator (admin)
- `GET /api/dispatch/promotions` - List promotions (admin)
- `POST /api/dispatch/promotions` - Create promotion (admin)

## Security Features

### Rate Limiting

- Authentication endpoints: 5 requests per minute
- General API endpoints: 10 requests per minute
- Automatic IP blocking for excessive requests

### Input Validation

- All user inputs are validated and sanitized
- Password strength validation available
- Email format validation
- Phone number format validation
- String length limits

### Authentication

- JWT token-based authentication
- Admin role-based access control
- Optional strong password support
- Admin lock/unlock functionality
- Recovery mechanism for admin access

## Database Migrations

### Create a new migration

```bash
flask db migrate -m "description of changes"
```

### Apply migrations

```bash
flask db upgrade
```

### Rollback migrations

```bash
flask db downgrade
```

## Logging

Logs are stored in the `logs/` directory:

- `general.log` - General application logs
- `error.log` - Error-level logs
- `structured.log` - JSON-formatted structured logs

Each log entry includes:
- Timestamp
- Log level
- Request ID
- Logger name
- Message
- Additional context

## Deployment

### Environment Variables

Required:
- `ADMIN_PIN` - Admin PIN (4 digits)
- `JWT_SECRET_KEY` - JWT secret key
- `OWNER_RECOVERY_SECRET` - Admin recovery secret

Optional:
- `DATABASE_URL` - Database connection string
- `CORS_ALLOWED_ORIGINS` - Allowed CORS origins
- `DB_POOL_SIZE` - Database connection pool size
- `DB_MAX_OVERFLOW` - Database connection pool overflow
- `DB_POOL_TIMEOUT` - Database connection pool timeout
- `DB_POOL_RECYCLE` - Database connection pool recycle time

### Render Deployment

The application is configured for Render deployment with automatic migrations:

```bash
# Deployment automatically runs:
flask db upgrade && gunicorn app:app --bind 0.0.0.0:$PORT
```

## Testing

Run tests with pytest:

```bash
pytest tests/ --cov=. --cov-report=html
```

## Troubleshooting

### Database Connection Issues

- Check `DATABASE_URL` environment variable
- Ensure database is accessible
- Verify database credentials

### Migration Issues

- Check `migrations/` directory exists
- Ensure Flask-Migrate is properly initialized
- Review migration files for errors

### Rate Limiting Issues

- Check `utils/rate_limiter.py` configuration
- Review rate limit logs in `logs/structured.log`
- Adjust rate limits in `utils/rate_limiter.py`

## License

Proprietary - Traveling Star Service