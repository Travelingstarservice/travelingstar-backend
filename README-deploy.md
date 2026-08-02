# Traveling Star Backend Deployment Runbook

## 1. Platform setup (Render)

- Runtime: Python 3.11
- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn app:app`

## 2. Required environment variables

- `ADMIN_PIN=2580`
- `JWT_SECRET_KEY=replace-with-a-long-random-secret`
- `CORS_ALLOWED_ORIGINS=https://your-frontend-domain.vercel.app`
- `PORT=5000`

## 3. Database configuration

- Local/simple setup: `DATABASE_URL=sqlite:///instance/database.db`
- Production recommendation: use managed Postgres and set `DATABASE_URL` to provider URL.

## 4. Deploy checks

1. Open backend root URL and confirm JSON response.
2. Call `POST /api/auth/login` with admin PIN and confirm token + role `admin`.
3. Call `GET /api/events/analytics` with `Authorization: Bearer <token>` and confirm `200`.
4. Call `GET /api/events` and confirm public event list returns `200`.

## 5. Frontend integration

- Frontend env var must point to backend API:
  - `VITE_API_URL=https://your-render-backend.onrender.com/api`
- Frontend origin must be included in backend CORS:
  - `CORS_ALLOWED_ORIGINS=https://your-frontend-domain.vercel.app`

## 6. Security hardening

1. Use a private `ADMIN_PIN` that is not easy to guess.
2. Rotate `JWT_SECRET_KEY` to a high-entropy secret.
3. Restrict CORS to only your production frontend URL.
4. Avoid sharing admin PIN in client-side docs or screenshots.
