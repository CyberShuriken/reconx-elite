# ReconX Elite Vercel Deployment

ReconX Elite uses Vercel for the static React frontend only.

## Production Project

- Use the Vercel project named `reconx-elite-frontend`.
- The duplicate Vercel project named `reconx-elite` should not receive production deploys.
- The Python API, Celery workers, Redis, and database must run outside Vercel.

## Required Vercel Environment Variables

Set these on `reconx-elite-frontend` for Production, Preview, and Development as needed:

```text
VITE_SUPABASE_URL
VITE_SUPABASE_PUBLISHABLE_KEY
VITE_API_BASE_URL
```

Do not add OpenRouter, Gemini, database, JWT, Redis, or service-role secrets to the frontend Vercel project.

## Expected Build Settings

```text
Install Command: cd frontend && npm install
Build Command: cd frontend && npm run build
Output Directory: frontend/dist
```

The root `vercel.json` mirrors these settings so accidental root deploys still build the frontend.
