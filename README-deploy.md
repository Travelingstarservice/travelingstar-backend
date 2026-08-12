# Traveling Star Backend Deployment Runbook

## 1. Platform setup (Render)

- Runtime: Python 3.11
- Build command: `chmod +x build.sh && ./build.sh`
- Start command: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 2 --timeout 120`

> **Note:** Render automatically injects the `$PORT` environment variable. Do **not** set `PORT` manually.

## 2. Required environment variables

Set these as **secret** environment variables in the Render dashboard. Do not commit real values to source control.

- `ADMIN_PIN` — required, 4-digit PIN that is not a common weak value (e.g. `1234`). The app refuses to start without a valid value.
- `JWT_SECRET_KEY` — required, long random string (generate with `openssl rand -hex 32`). The app refuses to start if missing or a placeholder.
- `OWNER_RECOVERY_SECRET` — recommended, long random string used to recover locked admin access.
- `CORS_ALLOWED_ORIGINS` — set to your frontend URL (e.g. `https://your-frontend-domain.vercel.app`)

## 3. Database configuration

- **Default (no `DATABASE_URL`):** SQLite at `/tmp/travelingstar/database.db`.  
  **Warning:** `/tmp` is ephemeral on Render — all data is wiped on every restart or redeploy.
- **Production:** provision a Render PostgreSQL database and set `DATABASE_URL` to its connection string. The app and `psycopg2-binary` driver support PostgreSQL out of the box.

## 4. Deploy checks

1. Open backend root URL and confirm JSON response.
2. Call `POST /api/auth/login` with admin PIN and confirm token + role `admin`.
3. Call `GET /api/events/analytics` with `Authorization: ****** and confirm `200`.
4. Call `GET /api/events` and confirm public event list returns `200`.

## 5. Frontend integration

- Frontend env var must point to backend API:
  - `VITE_API_URL=https://your-render-backend.onrender.com/api`
- Frontend origin must be included in backend CORS:
  - `CORS_ALLOWED_ORIGINS=https://your-frontend-domain.vercel.app`

## 6. Security hardening

1. Use a private `ADMIN_PIN` that is not easy to guess and is not a known weak value.
2. Set `JWT_SECRET_KEY` to a high-entropy secret (e.g. `openssl rand -hex 32`).
3. Restrict CORS to only your production frontend URL.
4. Avoid sharing admin PIN in client-side docs or screenshots.
5. Configure `OWNER_RECOVERY_SECRET` so admin access can be recovered if sign-in gets locked.

## 7. Emergency admin recovery

If admin sign-in is locked and no active admin session exists, call recovery endpoint:

- Endpoint: `POST /api/auth/admin/access/recover`
- Header: `X-Owner-Recovery-Secret: <OWNER_RECOVERY_SECRET>`
- Body: `{ "new_password": "<your-new-4-digit-pin>" }`

Example:

```bash
curl -X POST "https://your-backend-domain/api/auth/admin/access/recover" \
  -H "Content-Type: application/json" \
  -H "X-Owner-Recovery-Secret: <OWNER_RECOVERY_SECRET>" \
  -d '{"new_password":"<your-pin>"}'
```
