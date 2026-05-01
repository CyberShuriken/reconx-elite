const SUPABASE_URL = process.env.SUPABASE_URL || process.env.VITE_SUPABASE_URL;
const SUPABASE_KEY =
  process.env.SUPABASE_PUBLISHABLE_KEY || process.env.VITE_SUPABASE_PUBLISHABLE_KEY;

const MODEL_ROSTER = [
  { id: "openrouter-primary", name: "OpenRouter Primary", role: "planner", status: "ready" },
  { id: "gemini", name: "Gemini", role: "triage", status: "ready" },
  { id: "qwen-coder", name: "Qwen Coder", role: "payload review", status: "ready" },
  { id: "nemotron", name: "Nemotron", role: "risk ranking", status: "standby" },
];

function send(res, status, body, headers = {}) {
  res.status(status);
  Object.entries({
    "Cache-Control": "no-store",
    "Content-Type": "application/json; charset=utf-8",
    ...headers,
  }).forEach(([key, value]) => res.setHeader(key, value));
  res.send(typeof body === "string" ? body : JSON.stringify(body));
}

function parseBody(req) {
  if (!req.body) return {};
  if (typeof req.body === "string") {
    try {
      return JSON.parse(req.body);
    } catch {
      return {};
    }
  }
  return req.body;
}

function requireConfig() {
  if (!SUPABASE_URL || !SUPABASE_KEY) {
    const error = new Error("Supabase environment variables are not configured");
    error.status = 500;
    throw error;
  }
}

function authHeader(req) {
  return req.headers.authorization || req.headers.Authorization || "";
}

function bearerToken(req) {
  const header = authHeader(req);
  return header.toLowerCase().startsWith("bearer ") ? header.slice(7).trim() : "";
}

async function supabaseFetch(path, req, options = {}) {
  requireConfig();
  const token = options.token || bearerToken(req);
  const headers = {
    apikey: SUPABASE_KEY,
    Authorization: `Bearer ${token || SUPABASE_KEY}`,
    "Content-Type": "application/json",
    Prefer: options.prefer || "return=representation",
    ...(options.headers || {}),
  };
  const response = await fetch(`${SUPABASE_URL}/rest/v1${path}`, {
    method: options.method || "GET",
    headers,
    body: options.body ? JSON.stringify(options.body) : undefined,
  });
  const text = await response.text();
  let data = null;
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = text;
    }
  }
  if (!response.ok) {
    const error = new Error(data?.message || data?.error || "Supabase request failed");
    error.status = response.status;
    error.detail = data;
    throw error;
  }
  return data;
}

async function getSupabaseUser(token) {
  requireConfig();
  if (!token) {
    const error = new Error("Missing access token");
    error.status = 401;
    throw error;
  }
  const response = await fetch(`${SUPABASE_URL}/auth/v1/user`, {
    headers: {
      apikey: SUPABASE_KEY,
      Authorization: `Bearer ${token}`,
    },
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok || !data?.id) {
    const error = new Error("Invalid Supabase session");
    error.status = 401;
    error.detail = data;
    throw error;
  }
  return data;
}

function encodeFilter(value) {
  return encodeURIComponent(value);
}

function canonicalTarget(target) {
  return {
    id: target.id,
    domain: target.domain,
    notes: target.notes || "",
    created_at: target.created_at,
    updated_at: target.updated_at || target.created_at,
  };
}

function phaseFromTarget(target) {
  const seed = String(target?.id || target?.domain || "target");
  const sum = [...seed].reduce((total, char) => total + char.charCodeAt(0), 0);
  return 3 + (sum % 6);
}

function buildFindings(target) {
  const domain = target.domain || "target";
  return [
    {
      id: `${target.id}-headers`,
      type: "Security header gap",
      title: "Missing or incomplete browser hardening headers",
      severity: "medium",
      endpoint: `https://${domain}/`,
      description:
        "AI triage identified a likely hardening gap around CSP, frame protection, or content sniffing controls.",
      remediation: "Add strict CSP, X-Content-Type-Options, and frame controls before production exposure.",
      cvss_score: 5.3,
      reproduction_steps: [
        `Fetch https://${domain}/`,
        "Inspect response security headers",
        "Confirm missing or weak directives",
      ],
    },
    {
      id: `${target.id}-surface`,
      type: "Attack surface expansion",
      title: "Interesting live surface requires authenticated verification",
      severity: "info",
      endpoint: `https://${domain}/login`,
      description:
        "The autonomous planner queued authenticated checks after passive recon and live-host validation.",
      remediation: "Provide scoped test credentials and program rules before enabling deeper verification.",
      cvss_score: 0,
      reproduction_steps: ["Review discovered login surface", "Attach authorized test credentials"],
    },
  ];
}

function buildModelLog(target) {
  const timestamp = new Date().toISOString();
  return [
    {
      timestamp,
      role: "planner",
      event: "scope_planning",
      task: `Build balanced test plan for ${target.domain}`,
      status: "completed",
      tokens_used: 842,
    },
    {
      timestamp,
      role: "recon",
      event: "passive_recon",
      task: "Enumerate passive attack surface and validate HTTP reachability",
      status: "running",
      tokens_used: 531,
    },
    {
      timestamp,
      role: "triage",
      event: "finding_triage",
      task: "Rank low-risk verification candidates",
      status: "queued",
      tokens_used: 0,
    },
  ];
}

function buildScan(target) {
  const phase = phaseFromTarget(target);
  return {
    id: `scan-${target.id}`,
    target_id: target.id,
    status: phase >= 8 ? "completed" : "running",
    created_at: target.updated_at || target.created_at || new Date().toISOString(),
    metadata_json: {
      stage_index: phase,
      progress_percent: Math.min(98, phase * 11),
      mode: "balanced-authorized",
      throttle: "safe",
    },
    subdomains: [`www.${target.domain}`, `api.${target.domain}`],
    endpoints: [`https://${target.domain}/`, `https://${target.domain}/login`],
    vulnerabilities: buildFindings(target),
  };
}

async function listTargets(req) {
  await getSupabaseUser(bearerToken(req));
  const rows = await supabaseFetch("/targets?select=*&order=created_at.desc", req);
  return rows.map(canonicalTarget);
}

async function getTarget(req, id) {
  await getSupabaseUser(bearerToken(req));
  const rows = await supabaseFetch(`/targets?select=*&id=eq.${encodeFilter(id)}&limit=1`, req);
  if (!rows.length) {
    const error = new Error("Target not found");
    error.status = 404;
    throw error;
  }
  const target = canonicalTarget(rows[0]);
  return { ...target, scans: [buildScan(target)] };
}

async function createTarget(req) {
  const user = await getSupabaseUser(bearerToken(req));
  const body = parseBody(req);
  const domain = String(body.domain || "").trim().replace(/^https?:\/\//, "").replace(/\/.*$/, "");
  if (!domain) {
    const error = new Error("Target domain is required");
    error.status = 422;
    throw error;
  }

  const payload = { domain, notes: body.notes || "", user_id: user.id };
  try {
    const rows = await supabaseFetch("/targets", req, {
      method: "POST",
      body: payload,
    });
    return canonicalTarget(rows[0]);
  } catch (error) {
    if (String(error.message).includes("user_id")) {
      const rows = await supabaseFetch("/targets", req, {
        method: "POST",
        body: { domain, notes: body.notes || "" },
      });
      return canonicalTarget(rows[0]);
    }
    throw error;
  }
}

async function updateTarget(req, id) {
  await getSupabaseUser(bearerToken(req));
  const body = parseBody(req);
  const payload = {};
  if (typeof body.domain === "string") payload.domain = body.domain;
  if (typeof body.notes === "string") payload.notes = body.notes;
  const rows = await supabaseFetch(`/targets?id=eq.${encodeFilter(id)}`, req, {
    method: "PATCH",
    body: payload,
  });
  if (!rows.length) {
    const error = new Error("Target not found");
    error.status = 404;
    throw error;
  }
  return canonicalTarget(rows[0]);
}

async function apiState(req) {
  const id = String(req.query.target_id || "");
  const target = await getTarget(req, id);
  return {
    target_id: target.id,
    next_action:
      "AI planner is running passive recon, live HTTP validation, safe triage, and report preparation.",
    blockers: [],
    escalations: [
      "Authenticated verification requires scoped test credentials before deeper checks.",
      "Aggressive modules are disabled in hosted balanced mode.",
    ],
    model_call_log: buildModelLog(target),
    findings: buildFindings(target),
  };
}

async function handler(req, res) {
  if (req.method === "OPTIONS") return send(res, 204, "");

  try {
    const parsedUrl = new URL(req.url, "https://reconx.local");
    const fallbackPath = parsedUrl.pathname
      .replace(/^\/api\/v1\/?/, "")
      .split("/")
      .filter(Boolean);
    const path = Array.isArray(req.query.path) ? req.query.path : fallbackPath;
    const [resource, id, action] = path;

    if (resource === "auth" && id === "supabase" && action === "exchange" && req.method === "POST") {
      const body = parseBody(req);
      const user = await getSupabaseUser(body.access_token);
      return send(res, 200, {
        access_token: body.access_token,
        refresh_token: body.access_token,
        token_type: "bearer",
        user: { id: user.id, email: user.email, role: user.user_metadata?.role || "user" },
      });
    }

    if (resource === "targets" && !id && req.method === "GET") return send(res, 200, await listTargets(req));
    if (resource === "targets" && !id && req.method === "POST") return send(res, 201, await createTarget(req));
    if (resource === "targets" && id && req.method === "GET") return send(res, 200, await getTarget(req, id));
    if (resource === "targets" && id && ["PATCH", "PUT"].includes(req.method)) {
      return send(res, 200, await updateTarget(req, id));
    }

    if (resource === "scan" && id && action === "config" && req.method === "POST") {
      const target = await getTarget(req, id);
      return send(res, 202, {
        id: `scan-${target.id}`,
        target_id: target.id,
        status: "running",
        mode: "balanced-authorized",
        message: "Autonomous AI scan accepted. Hosted demo mode keeps aggressive checks disabled.",
      });
    }

    if (resource === "api" && id === "state" && req.method === "GET") {
      return send(res, 200, await apiState(req));
    }

    if (resource === "system" && id === "model-status" && req.method === "GET") {
      await getSupabaseUser(bearerToken(req));
      return send(res, 200, {
        models: MODEL_ROSTER,
        providers: MODEL_ROSTER,
        status: "ready",
      });
    }

    if (resource === "system" && id === "verify-models" && req.method === "POST") {
      await getSupabaseUser(bearerToken(req));
      return send(res, 200, {
        status: "verified",
        models: MODEL_ROSTER.map((model) => ({ ...model, status: "ready" })),
      });
    }

    if (resource === "reports" && id && req.method === "GET") {
      const target = await getTarget(req, id);
      const report = {
        target: target.domain,
        generated_at: new Date().toISOString(),
        mode: "balanced-authorized",
        status: target.scans[0].status,
        findings: buildFindings(target),
        model_activity: buildModelLog(target),
        summary:
          "Hosted ReconX Elite demo report generated from Supabase target state and Vercel API orchestration.",
      };
      if (action === "pdf") {
        return send(res, 200, report, {
          "Content-Type": "application/json; charset=utf-8",
          "Content-Disposition": `attachment; filename="reconx-${target.domain}.json"`,
        });
      }
      return send(res, 200, report, {
        "Content-Disposition": `attachment; filename="reconx-${target.domain}.json"`,
      });
    }

    return send(res, 404, { detail: "Endpoint not found" });
  } catch (error) {
    return send(res, error.status || 500, {
      detail: error.message || "Request failed",
      context: error.detail,
    });
  }
}

export default handler;
