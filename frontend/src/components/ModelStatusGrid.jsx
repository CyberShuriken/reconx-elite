import { useEffect, useState } from "react";

import { api } from "../api/client";

// 10+ AI models per Master Prompt Section 2
const MODEL_ROSTER = [
  {
    role: "orchestrator",
    name: "Orchestrator",
    modelId: "nvidia/llama-3.1-nemotron-nano-8b-instruct:free",
    envVar: "OR_KEY_NEMOTRON_NANO",
    description: "Pipeline routing, phase transitions",
  },
  {
    role: "primary_analyst",
    name: "Primary Analyst",
    modelId: "meta-llama/llama-3.3-70b-instruct:free",
    envVar: "OPENROUTER_KEY",
    description: "IDOR test gen, severity rating",
  },
  {
    role: "deep_reasoner",
    name: "Deep Reasoner",
    modelId: "nvidia/llama-3.3-nemotron-super-49b-v1:free",
    envVar: "OR_KEY_NEMOTRON_SUPER",
    description: "JWT attack chains, SSRF escalation",
  },
  {
    role: "code_engine",
    name: "Code Engine",
    modelId: "qwen/qwen3-coder-480b-a35b-instruct:free",
    envVar: "OR_KEY_QWEN_CODER",
    description: "Payload generation, PoC scripts",
  },
  {
    role: "fast_classifier",
    name: "Fast Classifier",
    modelId: "thudm/glm-4-9b-chat:free",
    envVar: "OR_KEY_GLM_45",
    description: "Subdomain/host classification",
  },
  {
    role: "json_extractor",
    name: "JSON Extractor",
    modelId: "google/gemma-3-27b-it:free",
    envVar: "OPENROUTER_API_KEY_SECONDARY",
    description: "Structured output from tools",
  },
  {
    role: "header_analyst",
    name: "Header Analyst",
    modelId: "google/gemma-3-12b-it:free",
    envVar: "OPENROUTER_API_KEY_TERTIARY",
    description: "CORS, CSP, security headers",
  },
  {
    role: "js_analyst",
    name: "JS Analyst",
    modelId: "minimax/minimax-m1:extended",
    envVar: "OR_KEY_MINIMAX",
    description: "Large JS file analysis",
  },
  {
    role: "critical_reporter",
    name: "Critical Reporter",
    modelId: "microsoft/phi-4-reasoning-plus:free",
    envVar: "OR_KEY_GPT_OSS_120B",
    description: "High/Critical reports",
  },
  {
    role: "standard_reporter",
    name: "Standard Reporter",
    modelId: "microsoft/phi-4-mini-reasoning:free",
    envVar: "OR_KEY_GPT_OSS_20B",
    description: "Low/Medium reports",
  },
  {
    role: "deep_reasoner_fallback",
    name: "Deep Reasoner (Fallback)",
    modelId: "nvidia/llama-3.3-nemotron-super-49b-v1:free",
    envVar: "OR_KEY_NEMOTRON_SUPER_ALT",
    description: "Fallback for NEMOTRON_SUPER",
  },
];

export default function ModelStatusGrid() {
  const [modelStatus, setModelStatus] = useState(null);
  const [isVerifying, setIsVerifying] = useState(false);
  const [error, setError] = useState("");

  async function loadStatus() {
    try {
      const response = await api.get("/api/model-status");
      setModelStatus(response.data);
      setError("");
    } catch (_err) {
      setError("Failed to load model status");
    }
  }

  async function handleVerify() {
    setIsVerifying(true);
    setError("");
    try {
      await api.post("/api/verify-models");
      await loadStatus();
    } catch (_err) {
      setError("Verification failed");
    } finally {
      setIsVerifying(false);
    }
  }

  useEffect(() => {
    loadStatus();
    const interval = window.setInterval(loadStatus, 30000);
    return () => window.clearInterval(interval);
  }, []);

  if (!modelStatus) {
    return <div className="panel-card">Loading model status...</div>;
  }

  return (
    <div className="panel-card">
      <div className="panel-header" style={{ marginBottom: "1.5rem" }}>
        <div>
          <h2>AI Model Roster (10+ Models)</h2>
          <p className="table-subcopy">
            Provider: <strong>{modelStatus.provider || "OpenRouter"}</strong>
          </p>
        </div>
        <button
          className="primary-button"
          disabled={isVerifying}
          onClick={handleVerify}
          style={{ padding: "0.5rem 1rem", fontSize: "0.85rem" }}
          type="button"
        >
          {isVerifying ? "Verifying..." : "Verify All Models"}
        </button>
      </div>

      {error ? (
        <p className="error-text" style={{ marginBottom: "1rem" }}>
          {error}
        </p>
      ) : null}

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))",
          gap: "1rem",
        }}
      >
        {MODEL_ROSTER.map((model) => {
          const verification = modelStatus.statuses?.[model.role];
          const isOnline = verification?.status === "ONLINE";
          const isError = verification?.status === "ERROR";
          const isPending = verification?.status === "PENDING";

          return (
            <div
              key={model.role}
              style={{
                padding: "1rem",
                background: "var(--panel-strong)",
                border: `1px solid ${isOnline ? "#14532d" : isError ? "#7f1d1d" : "var(--border)"}`,
                borderRadius: "18px",
                display: "flex",
                flexDirection: "column",
                gap: "0.5rem",
                opacity: model.role.includes("fallback") ? 0.7 : 1,
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <strong style={{ fontSize: "0.95rem", color: "var(--ink)" }}>
                  {model.name}
                  {model.role.includes("fallback") && <span style={{ fontSize: "0.7rem", marginLeft: "4px" }}>(FB)</span>}
                </strong>
                <span
                  style={{
                    fontSize: "0.75rem",
                    padding: "2px 8px",
                    borderRadius: "999px",
                    background: isOnline ? "#14532d" : isError ? "#7f1d1d" : isPending ? "#594a42" : "#334155",
                    color: "#fff",
                  }}
                >
                  {verification?.status || "UNKNOWN"}
                </span>
              </div>
              <div style={{ fontSize: "0.75rem", color: "var(--muted)" }}>{model.description}</div>
              <code style={{ fontSize: "0.7rem", color: "var(--muted)", wordBreak: "break-all" }}>
                {model.modelId}
              </code>
              <div style={{ fontSize: "0.7rem", color: "var(--muted)" }}>
                ENV: <code>{model.envVar}</code>
              </div>
              <span className="table-subcopy">Calls made: {verification?.calls_made || 0}</span>
              {verification?.response && isOnline ? (
                <p style={{ fontSize: "0.75rem", fontStyle: "italic", marginTop: "4px", color: "#14532d" }}>
                  "{verification.response}"
                </p>
              ) : null}
              {verification?.error ? (
                <p style={{ fontSize: "0.75rem", color: "var(--danger)", marginTop: "4px" }}>
                  Error: {verification.error}
                </p>
              ) : null}
            </div>
          );
        })}
      </div>
    </div>
  );
}
