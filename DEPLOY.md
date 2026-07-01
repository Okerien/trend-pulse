# Deploying Trend Pulse

Order matters: **backend first** (to get its URL), then the frontend (which bakes that URL in at build time), then the keep-alive.

Accounts you'll need (all free): **GitHub**, **Render**, **Vercel**, **cron-job.org**.

---

## 1. Push to GitHub

1. Create a new **empty** repo at https://github.com/new (no README, no .gitignore, no license). Name it e.g. `trend-pulse`.
2. From the project folder, connect and push (replace the URL with yours):

```bash
git remote add origin https://github.com/<you>/trend-pulse.git
git push -u origin main
```

If push asks for credentials, use your GitHub username + a **personal access token with `repo` scope** as the password (the token you made earlier had no scopes, so make a new one at https://github.com/settings/tokens if needed).

---

## 2. Backend → Render

1. https://dashboard.render.com → **New → Blueprint**.
2. Connect your GitHub and pick the `trend-pulse` repo. Render reads `backend/render.yaml` and proposes the `trend-pulse-api` web service.
3. Click **Apply**. It'll start building.
4. Open the service → **Environment** tab → add these values (from your `backend/.env`):
   - `GROQ_API_KEY`
   - `UPSTASH_REDIS_REST_URL`, `UPSTASH_REDIS_REST_TOKEN`
   - `GNEWS_API_KEY`
   - `GITHUB_TOKEN`
   - `FRONTEND_ORIGIN` → set to `*` for now (tighten to your Vercel URL in step 4)
   - (`TRENDPULSE_DEMO` is already `0`; leave `HUGGINGFACE_API_TOKEN`, `BRAVE_API_KEY`, `YOUTUBE_API_KEY` blank)
5. Save → it redeploys. When live, copy the URL: `https://trend-pulse-api.onrender.com`.
6. Test it: open `https://trend-pulse-api.onrender.com/health` → should show `{"status":"ok"}`.

---

## 3. Frontend → Vercel

1. https://vercel.com → **Add New → Project** → import the same GitHub repo.
2. **Important:** set **Root Directory** to `frontend` (click Edit next to it). Vercel auto-detects Vite.
3. Under **Environment Variables**, add:
   - `VITE_API_URL` = your Render URL from step 2 (e.g. `https://trend-pulse-api.onrender.com`)
4. **Deploy.** When done you get a URL like `https://trend-pulse.vercel.app`.

---

## 4. Tighten CORS (optional but recommended)

Back in Render → `trend-pulse-api` → Environment → set `FRONTEND_ORIGIN` to your Vercel URL (e.g. `https://trend-pulse.vercel.app`). Save → redeploy.

---

## 5. Keep-alive (beats Render's free-tier sleep)

Render's free tier sleeps after 15 min idle. Keep it warm:

1. https://cron-job.org → sign up → **Create cronjob**.
2. URL: `https://trend-pulse-api.onrender.com/health`
3. Schedule: **every 10 minutes**. Save.

This also keeps the in-memory cache warm between visits.

---

## Done

- App: `https://trend-pulse.vercel.app`
- Report share links and `/report?client=...` links work out of the box (SPA routing via `vercel.json`).
- Every push to `main` auto-redeploys both Render and Vercel.

### Optional custom domain
Point `trends.bendingwaters.com` at Vercel via a CNAME (Vercel → Project → Settings → Domains gives the exact record).
