# Traveling Star Deployment Guide

## 1. Backend deployment (Render)

### Recommended settings
- Runtime: Python 3.11
- Build command: `chmod +x build.sh && ./build.sh`
- Start command: `gunicorn app:app`
- Important: the frontend folder must be present inside the backend repo at `traveling-star-frontend/` for Render to find it.

### Environment variables
- `ADMIN_PIN=2580`
- `JWT_SECRET_KEY=replace-with-a-long-random-secret`
- `OWNER_RECOVERY_SECRET=replace-with-a-long-random-owner-secret`
- `CORS_ALLOWED_ORIGINS=https://your-frontend-domain.vercel.app`
- `PORT=5000`

### Notes
- The backend will build the frontend bundle automatically during deployment.
- The app serves the built frontend from the same deployment.

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
1. Open the deployed frontend URL.
2. Confirm the home page loads.
3. Register/login and use the dashboard.
4. Verify the API calls succeed from the deployed app.

## 4. Emergency admin recovery

Use only if admin access is locked and you do not have an active admin session.

- Endpoint: `POST /api/auth/admin/access/recover`
- Header: `X-Owner-Recovery-Secret: <OWNER_RECOVERY_SECRET>`
- JSON body: `{ "new_password": "2580" }`
