# ReconX Elite Vercel Frontend Deployment

ReconX Elite uses Vercel for the static React frontend only.

## Production Project

- Use the Vercel project named `reconx-elite-frontend`.
- The duplicate Vercel project named `reconx-elite` should not receive production deploys.
- The Python API, Celery workers, Redis, and database must run outside Vercel.
- Production API traffic must go to the Railway backend through `VITE_API_BASE_URL`.

## Required Vercel Environment Variables

Set these on `reconx-elite-frontend` for Production, Preview, and Development as needed:

```text
VITE_SUPABASE_URL
VITE_SUPABASE_PUBLISHABLE_KEY
VITE_API_BASE_URL
```

`VITE_API_BASE_URL` must be the Railway API origin, for example:

```text
https://reconx-elite-api.up.railway.app
```

Do not add OpenRouter, Gemini, database, JWT, Redis, or service-role secrets to the frontend Vercel project.

## Expected Build Settings

When the Vercel project uses `frontend` as the root directory:

```text
Install Command: npm install
Build Command: npm run build
Output Directory: dist
```

The root `vercel.json` mirrors these frontend-relative settings because this
project is imported with `frontend` as the Vercel root directory.

## API Boundary

The Vercel deployment is intentionally frontend-only. Do not add files under the
root `api/` directory for production; Vercel treats that directory as serverless
functions. The full API lives in FastAPI on Railway.
