# Deploying Cur8 to production

## First-time hosting (free tier)

Use **Railway** for the backend + database + Redis, and **Vercel** for the frontend. Both have free tiers; you’ll get a backend URL like `https://cur8-backend.up.railway.app` and a frontend URL like `https://cur8.vercel.app`.

```mermaid
flowchart LR
  User --> Vercel[Vercel SPA]
  Vercel -->|API + cookies| Railway[Railway Backend]
  Railway --> Postgres[(Postgres)]
  Railway --> Redis[(Redis)]
  Railway -->|OAuth| Spotify[Spotify]
```

### Step 1: Backend on Railway

1. Sign up at [railway.app](https://railway.app) (GitHub login is fine).
2. **New project** → **Deploy from GitHub repo** (connect GitHub, choose `cur8`, select the `backend` folder as root, or deploy the whole repo and set root in settings).
3. In the project, add two services (or use “New” → “Database” and “Redis”):
   - **PostgreSQL** (one-click add). Railway gives you `DATABASE_URL`; add it to the backend service’s variables.
   - **Redis** (one-click add if available, or use **Upstash** free Redis: [upstash.com](https://upstash.com) → create Redis, copy `REDIS_URL`).
4. In the **backend service** (the one running your code):
   - Set **Root Directory** to `backend` if you deployed the whole repo.
   - Set **Build Command** to something like `pip install -r requirements.txt` (or use the Dockerfile; Railway can build from `backend/Dockerfile`).
   - Set **Start Command** to `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT`. (Railway sets `PORT`.)
   - Add **Variables** (env):
     - `ENVIRONMENT=production`
     - `SPOTIFY_CLIENT_ID` = (from Spotify Dashboard)
     - `SPOTIFY_REDIRECT_URI` = `https://<your-railway-backend-url>/auth/callback` (you’ll get the URL after first deploy)
     - `FRONTEND_URL` = `https://<your-vercel-url>` (from Step 2)
     - `ALLOWED_ORIGINS` = `https://<your-vercel-url>`
     - `DATABASE_URL` = (from Railway Postgres)
     - `REDIS_URL` = (from Railway Redis or Upstash)
     - `SESSION_SECRET` = run `openssl rand -hex 32` locally and paste
   - Deploy. Copy the public URL (e.g. `https://cur8-backend-production.up.railway.app`).
5. **Spotify Dashboard** → Your app → **Redirect URIs** → Add `https://<railway-backend-url>/auth/callback`. Save.
6. In Railway, **update** `SPOTIFY_REDIRECT_URI` and `FRONTEND_URL` / `ALLOWED_ORIGINS` if you used placeholders; redeploy if needed.

### Step 2: Frontend on Vercel

1. Sign up at [vercel.com](https://vercel.com) (GitHub login).
2. **Add New** → **Project** → Import your `cur8` repo.
3. **Configure:**
   - **Root Directory**: `frontend`
   - **Framework Preset**: Vite
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
   - **Environment variable**: `VITE_API_URL` = `https://<your-railway-backend-url>` (no trailing slash). Important: set this for Production (and Preview if you want).
4. Deploy. Copy the URL (e.g. `https://cur8-xxx.vercel.app`).
5. If you didn’t set `FRONTEND_URL` / `ALLOWED_ORIGINS` yet, set them in Railway to this Vercel URL and redeploy the backend.

### Step 3: Test

- Open the Vercel URL → you should see the app.
- Click login → redirects to Spotify → after auth, redirects back to the app. If you get a blank page or 401, check that `FRONTEND_URL` and `ALLOWED_ORIGINS` match the Vercel URL exactly (including `https://`).

### Free-tier limits (rough)

- **Railway**: Free trial credit; after that a few dollars/month for a small backend + Postgres. Check [railway.app/pricing](https://railway.app/pricing).
- **Vercel**: Free tier is generous for static sites.
- **Upstash Redis**: Free tier is enough for sessions and rate limiting.

**Alternatives:** Use **Render** instead of Railway (free tier for web + Postgres; Redis via Upstash). Or **Fly.io** for the backend + **Neon** (free Postgres) + **Upstash** Redis; frontend still on Vercel/Netlify.

---

## Checklist

### 1. Spotify Developer Dashboard
- Add **Redirect URI**: `https://<your-backend-host>/auth/callback` (e.g. `https://api.cur8.com/auth/callback`).
- Keep the same Client ID (no secret for PKCE).

### 2. Backend environment (production)
Set these where the backend runs (e.g. Railway, Render, Fly.io, or your server):

| Variable | Example | Notes |
|---------|---------|--------|
| `ENVIRONMENT` | `production` | Enables secure cookies. |
| `SPOTIFY_CLIENT_ID` | (same as dev) | From Spotify Dashboard. |
| `SPOTIFY_REDIRECT_URI` | `https://api.cur8.com/auth/callback` | Must match Spotify Dashboard. |
| `FRONTEND_URL` | `https://app.cur8.com` | Where the SPA lives; redirect after login. |
| `ALLOWED_ORIGINS` | `https://app.cur8.com` | Comma-separated; SPA origin(s). |
| `DATABASE_URL` | `postgresql://user:pass@host:5432/cur8` | Managed Postgres (Neon, Supabase, RDS, etc.). |
| `REDIS_URL` | `redis://...` or `rediss://...` | Managed Redis (Upstash, Redis Cloud, etc.). |
| `SESSION_SECRET` | Long random string | e.g. `openssl rand -hex 32`. |

### 3. Frontend build
The SPA must call your production API. At **build time** set:

- `VITE_API_URL=https://<your-backend-host>` (e.g. `https://api.cur8.com`).

**Docker (prod frontend):**
```bash
docker build -f frontend/Dockerfile.prod \
  --build-arg VITE_API_URL=https://api.cur8.com \
  -t cur8-frontend .
```

Then run the container (or serve the built `frontend/dist` with any static host).

### 4. Database migrations
Run once before or on first backend deploy:
```bash
alembic upgrade head
```
If the backend’s Docker CMD already runs `alembic upgrade head`, no extra step needed.

### 5. HTTPS
- Backend and frontend must be served over **HTTPS** in production.
- Use your platform’s SSL (Railway, Render, Vercel, etc.) or a reverse proxy (nginx + Let’s Encrypt).

### 6. Cookie / CORS
- Backend sets `secure=True` when `ENVIRONMENT=production`.
- `ALLOWED_ORIGINS` must include the exact SPA origin (scheme + host + port if non-default).
- Frontend must call the API with `credentials: 'include'` (already done).

---

## Example: single VPS with Docker Compose

1. Provision a server (e.g. Ubuntu) and install Docker + Docker Compose.
2. Create `.env.production` with all variables; use a managed Postgres and Redis or run them in compose.
3. Build and run:
   - Backend: existing Dockerfile; env includes `ENVIRONMENT=production`, `DATABASE_URL`, `REDIS_URL`, etc.
   - Frontend: build with `Dockerfile.prod` and `VITE_API_URL=https://your-domain.com` (or serve backend and SPA on same host with nginx routing).
4. Put nginx (or Caddy) in front: terminate SSL, proxy `/api` or `https://api.yourdomain.com` to backend, serve SPA or proxy `/` to frontend container.

## Example: split hosting (backend + DB/Redis on one platform, frontend on another)

- **Backend + DB + Redis:** e.g. Railway or Render (backend service + Postgres + Redis add-ons). Set env as above; note the backend URL.
- **Frontend:** Build with `VITE_API_URL=https://<backend-url>`, then deploy the `dist` folder to Vercel, Netlify, or Cloudflare Pages.
- **Spotify:** Redirect URI = backend URL + `/auth/callback`. **Allowed origins** = frontend URL.

---

## Quick reference

- Backend Dockerfile: `backend/Dockerfile` (runs migrations + uvicorn).
- Frontend prod Dockerfile: `frontend/Dockerfile.prod` (build + nginx).
- Root `docker-compose.yml` is for local dev; duplicate and adjust for prod (env, no dev mounts) if you use compose in prod.
