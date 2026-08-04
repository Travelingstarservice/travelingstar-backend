# Traveling Star Deployment Guide

## 1. Backend deployment (Render)

### Recommended settings
- Runtime: Python 3.11
- Build command: `chmod +x build.sh && ./build.sh`
- Start command: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 2 --timeout 120`

### Environment variables

Set these as **secret** environment variables in the Render dashboard. Do not commit real values to `render.yaml`.

- `ADMIN_PIN` — required, 4-digit PIN, must not be a common weak value (e.g. `1234`). The app will refuse to start without a valid value.
- `JWT_SECRET_KEY` — required, long random string (e.g. `openssl rand -hex 32`). The app will refuse to start if this is missing or a placeholder.
- `OWNER_RECOVERY_SECRET` — recommended, long random string used to recover locked admin access.
- `CORS_ALLOWED_ORIGINS` — set to your frontend URL (e.g. `https://your-frontend-domain.vercel.app`)

> **Note:** Render automatically injects the `$PORT` environment variable. Do **not** set `PORT` manually.

### Database

- By default (no `DATABASE_URL` set), the app uses SQLite at `/tmp/travelingstar/database.db`.  
  **Warning:** `/tmp` is ephemeral on Render — all data is wiped on every restart or redeploy.  
  For persistent data, provision a Render PostgreSQL database and set `DATABASE_URL` to its connection string.

### Frontend serving

The backend API does not build the frontend. Deploy the frontend separately (e.g. Vercel) and set `CORS_ALLOWED_ORIGINS` to its URL.

## 2. Frontend deployment (Vercel)

### Project root
- Set the project root to the frontend folder.

### Build settings
- Build command: `npm run build`
- Output directory: `dist`

### Environment variable
- `VITE_API_URL=https://your-backend-url/api`

### Router config
- The Vite config already uses the correct base path for deployment.

## 3. Post-deploy check
1. Open the backend root URL and confirm a JSON `{"message": "Traveling Star API"}` response.
2. Call `POST /api/auth/login` with admin PIN and confirm token + role `admin`.
3. Open the deployed frontend URL and confirm the home page loads.
4. Verify the API calls succeed from the deployed frontend app.

## 4. Emergency admin recovery

Use only if admin access is locked and you do not have an active admin session.

- Endpoint: `POST /api/auth/admin/access/recover`
- Header: `X-Owner-Recovery-Secret: <OWNER_RECOVERY_SECRET>`
- JSON body: `{ "new_password": "<your-new-4-digit-pin>" }`
