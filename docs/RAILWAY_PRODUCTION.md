# Railway Production Backend

ReconX Elite runs its full backend outside Vercel. Use Railway for the long-lived
FastAPI API, Celery worker, and one-off Alembic migration process.

## Services

Create three Railway services from the same GitHub repository and Dockerfile:

```text
Dockerfile: backend/Dockerfile
Build context: repository root
```

Set only `SERVICE_MODE` differently per service:

```text
api      SERVICE_MODE=api      Public networking enabled; Railway provides PORT.
worker   SERVICE_MODE=worker   No public networking.
migrate  SERVICE_MODE=migrate  Run manually or as a one-off deploy before api/worker.
```

The Docker image command switches behavior from `SERVICE_MODE`. The API binds to
`${PORT:-8000}` so it works on Railway and still runs locally on port 8000.

## Required API and Worker Variables

Set these on the Railway `api`, `worker`, and `migrate` services unless noted.
Use Railway shared variables if all three services live in one project.

```text
DATABASE_URL=postgresql+psycopg2://<user>:<pass>@<supabase-host>:5432/<db>
REDIS_URL=<upstash redis or rediss URL>

JWT_SECRET_KEY=<64-char random hex>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=120
REFRESH_TOKEN_EXPIRE_MINUTES=10080

CORS_ALLOWED_ORIGINS=https://<vercel-production-domain>
CORS_ALLOWED_ORIGIN_REGEX=https://.*\.vercel\.app
FRONTEND_URL=https://<vercel-production-domain>
HTTPS_BEHIND_PROXY=true
METRICS_ENABLED=false

SUPABASE_URL=<supabase-project-url>
SUPABASE_PUBLISHABLE_KEY=<supabase-publishable-or-anon-key>

OPENROUTER_KEY=<openrouter key>
OR_KEY_NEMOTRON_NANO=<openrouter key>
OR_KEY_NEMOTRON_SUPER=<openrouter key>
OR_KEY_QWEN_CODER=<openrouter key>
OR_KEY_GLM_45=<openrouter key>
OPENROUTER_API_KEY_SECONDARY=<openrouter key>
OPENROUTER_API_KEY_TERTIARY=<openrouter key>
OR_KEY_MINIMAX=<openrouter key>
OR_KEY_GPT_OSS_120B=<openrouter key>
OR_KEY_GPT_OSS_20B=<openrouter key>
OR_KEY_NEMOTRON_SUPER_ALT=<openrouter key>
GEMINI_API_KEY=<gemini key>
```

Optional production integrations can also be set on Railway:

```text
SLACK_WEBHOOK_URL=
DISCORD_WEBHOOK_URL=
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
JIRA_URL=
JIRA_USERNAME=
JIRA_API_TOKEN=
JIRA_PROJECT_KEY=
GITHUB_TOKEN=
GITHUB_REPOSITORY=
GITHUB_ASSIGNEE=
```

## Supabase Database Setup

Use Supabase Postgres as the application database and apply the backend Alembic
migrations. Do not use `supabase/reconx_hosted_schema.sql` for this production
stack; that SQL file was only for the removed Vercel-hosted adapter.

Deployment order:

1. Create Supabase project and copy the pooled or direct Postgres connection URL.
2. Convert the URL to the app format: `postgresql+psycopg2://...`.
3. Set `DATABASE_URL` on all Railway backend services.
4. Deploy/run the Railway `migrate` service with `SERVICE_MODE=migrate`.
5. Confirm Alembic finishes successfully before starting `api` and `worker`.

## Verification

Run the production environment preflight anywhere the Railway variables are
available:

```bash
./scripts/validate-production-env.sh
```

After deployment:

```bash
curl https://<railway-api-domain>/health
```

Expected:

```json
{"status":"ok","database":"connected"}
```

Then verify:

- Railway worker logs show Celery connected to Upstash Redis.
- Vercel frontend network requests target `https://<railway-api-domain>`.
- Login/register uses Supabase, then `POST /auth/supabase/exchange` returns the backend JWT pair.
- No OpenRouter, Gemini, database, JWT, Redis, or service-role secrets are present in Vercel.

## Connect Vercel to Railway

Copy the public Railway API domain after the `api` service deploys, then set it
on the Vercel frontend project:

```text
VITE_API_URL=https://<railway-api-domain>
```

Vercel must also have the Supabase frontend values:

```text
VITE_SUPABASE_URL=<supabase-project-url>
VITE_SUPABASE_PUBLISHABLE_KEY=<supabase-publishable-or-anon-key>
```
