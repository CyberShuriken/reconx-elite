import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { api, backendBaseUrl, formatApiErrorDetail } from "../api/client";
import AttackSurfaceMap from "../components/AttackSurfaceMap";
import FindingsPanel from "../components/FindingsPanel";
import LiveAgentLog from "../components/LiveAgentLog";
import ModelStatusGrid from "../components/ModelStatusGrid";
import ReportDownload from "../components/ReportDownload";
import ScanProgressBar from "../components/ScanProgressBar";
import { getTargetById, updateTargetNotes } from "../lib/supabase";

const balancedScanConfig = {
  selected_templates: ["cves", "exposures", "misconfiguration"],
  severity_filter: ["medium", "high", "critical"],
};

function getScanPhase(scan) {
  const meta = scan?.metadata_json || {};
  const phase = Number(meta.stage_index ?? 0);
  return Number.isFinite(phase) ? Math.max(0, Math.min(10, phase)) : 0;
}

function mapAgentLogEvents(events = []) {
  return events.map((event, index) => ({
    id: `${event.timestamp || "event"}-${index}`,
    timestamp: event.timestamp,
    event: event.event || "model_activity",
    model_role: event.role,
    action: event.task || event.status || event.type,
    status: event.status,
    message: event.error || event.message || `${event.role || "AI"} ${event.status || "updated"}`,
    tokens_used: event.tokens_used,
  }));
}

function mapVerificationFindings(findings = []) {
  return findings.map((finding) => ({
    id: finding.id,
    name: finding.type,
    title: finding.type,
    severity: finding.severity,
    endpoint: finding.endpoint,
    host: finding.endpoint,
    description: finding.description,
    remediation: finding.remediation,
    cvss_score: finding.cvss_score,
    poc: (finding.reproduction_steps || []).join("\n"),
  }));
}

function collectSecrets(jsAssets = []) {
  return jsAssets.flatMap((asset) => asset.secrets_json || []);
}

export default function SupabaseTargetPage() {
  const { targetId } = useParams();
  const [target, setTarget] = useState(null);
  const [backendTarget, setBackendTarget] = useState(null);
  const [verificationState, setVerificationState] = useState(null);
  const [notes, setNotes] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isStartingScan, setIsStartingScan] = useState(false);

  const ensureBackendTarget = useCallback(async (domain) => {
    const { data: targets } = await api.get("/targets");
    const existing = (targets || []).find((row) => row.domain === domain);
    if (existing) {
      return existing;
    }
    const { data } = await api.post("/targets", { domain });
    return data;
  }, []);

  const loadTargetWorkspace = useCallback(async () => {
    setIsLoading(true);
    try {
      const supabaseTarget = await getTargetById(targetId);
      setTarget(supabaseTarget);
      setNotes(supabaseTarget.notes || "");

      const linkedTarget = await ensureBackendTarget(supabaseTarget.domain);
      const [{ data: targetDetails }, { data: verification }] = await Promise.all([
        api.get(`/targets/${linkedTarget.id}`),
        api.get("/api/state", { params: { target_id: linkedTarget.id } }),
      ]);
      setBackendTarget(targetDetails);
      setVerificationState(verification);
      setError("");
    } catch (requestError) {
      setError(
        formatApiErrorDetail(requestError.response?.data?.detail || requestError.message) ||
          "Failed to load target workspace",
      );
    } finally {
      setIsLoading(false);
    }
  }, [ensureBackendTarget, targetId]);

  useEffect(() => {
    let cancelled = false;
    async function run() {
      if (!cancelled) {
        await loadTargetWorkspace();
      }
    }
    run();
    const interval = window.setInterval(run, 6000);
    return () => {
      cancelled = true;
      window.clearInterval(interval);
    };
  }, [loadTargetWorkspace]);

  const latestScan = backendTarget?.scans?.[0] || null;
  const scanPhase = getScanPhase(latestScan);
  const scanProgress = latestScan?.metadata_json?.progress_percent || 0;
  const scanStatus = latestScan?.status || "idle";
  const agentLogs = useMemo(
    () => mapAgentLogEvents(verificationState?.model_call_log || []),
    [verificationState],
  );
  const findings = useMemo(() => {
    const verificationFindings = mapVerificationFindings(verificationState?.findings || []);
    return verificationFindings.length ? verificationFindings : latestScan?.vulnerabilities || [];
  }, [latestScan, verificationState]);

  async function saveNotes() {
    setIsSaving(true);
    try {
      const updated = await updateTargetNotes(targetId, notes);
      setTarget(updated);
      setError("");
    } catch (requestError) {
      setError(requestError.message || "Could not save target notes");
    } finally {
      setIsSaving(false);
    }
  }

  async function startAutonomousScan() {
    setIsStartingScan(true);
    setError("");
    try {
      const linkedTarget = backendTarget || (await ensureBackendTarget(target.domain));
      await api.post(`/scan/${linkedTarget.id}/config`, balancedScanConfig);
      await loadTargetWorkspace();
    } catch (requestError) {
      setError(
        formatApiErrorDetail(requestError.response?.data?.detail || requestError.message) ||
          "Autonomous scan failed to start",
      );
    } finally {
      setIsStartingScan(false);
    }
  }

  if (isLoading && !target) {
    return (
      <main className="page-shell">
        <div className="panel-card">Loading target workspace...</div>
      </main>
    );
  }

  return (
    <main className="page-shell hosted-workspace">
      <header className="page-header hosted-hero">
        <div>
          <Link className="primary-button" to="/">
            Back to dashboard
          </Link>
          <p className="eyebrow">Autonomous target workspace</p>
          <h1>{target?.domain || "Target"}</h1>
          <p className="lede">
            Supabase stores hosted auth and target notes. The Python worker stack runs the
            balanced AI scan pipeline and reports.
          </p>
        </div>
        <div className="hosted-actions">
          <span className={`status-pill status-${scanStatus}`}>{scanStatus}</span>
          <button
            className="primary-button"
            disabled={isStartingScan || scanStatus === "pending" || scanStatus === "running"}
            onClick={startAutonomousScan}
            type="button"
          >
            {isStartingScan ? "Starting..." : "Start autonomous scan"}
          </button>
          {backendTarget ? (
            <a
              className="ghost-button link-button"
              href={`${backendBaseUrl}/reports/${backendTarget.id}/json`}
              rel="noreferrer"
              target="_blank"
            >
              JSON report
            </a>
          ) : null}
        </div>
      </header>

      {error ? <p className="error-text panel-card">{error}</p> : null}

      <section className="summary-strip">
        <article className="summary-card">
          <span>Backend target</span>
          <strong>{backendTarget?.id || "linking"}</strong>
        </article>
        <article className="summary-card">
          <span>Subdomains</span>
          <strong>{latestScan?.subdomains?.length || 0}</strong>
        </article>
        <article className="summary-card">
          <span>Endpoints</span>
          <strong>{latestScan?.endpoints?.length || 0}</strong>
        </article>
        <article className="summary-card highlight-card">
          <span>Findings</span>
          <strong>{findings.length}</strong>
        </article>
      </section>

      <section className="hosted-ops-grid">
        <ScanProgressBar
          currentPhase={scanPhase}
          phaseProgress={{ [scanPhase]: scanProgress }}
          phaseStatus={{
            [scanPhase]: scanStatus === "completed" ? "completed" : scanStatus === "failed" ? "error" : "running",
          }}
        />
        <LiveAgentLog logs={agentLogs} />
      </section>

      <section className="layout-grid">
        <article className="panel-card">
          <h2>Target notes</h2>
          <textarea
            className="notes-area"
            value={notes}
            onChange={(event) => setNotes(event.target.value)}
            placeholder="Capture scope notes, program rules, credentials, or next actions here."
            rows={8}
          />
          <button className="primary-button" disabled={isSaving} onClick={saveNotes} type="button">
            {isSaving ? "Saving..." : "Save notes"}
          </button>
        </article>

        <article className="panel-card">
          <h2>AI next action</h2>
          <p className="lede">{verificationState?.next_action || "Start a scan to initialize AI state."}</p>
          <ul className="stack-list">
            {(verificationState?.escalations || []).map((item, index) => (
              <li className="list-row" key={`escalation-${index}`}>
                <strong>Escalation</strong>
                <span>{item}</span>
              </li>
            ))}
            {(verificationState?.blockers || []).map((item, index) => (
              <li className="list-row" key={`blocker-${index}`}>
                <strong>Blocker</strong>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </article>
      </section>

      <section className="hosted-ops-grid">
        <FindingsPanel findings={findings} scanStatus={scanStatus} />
        <AttackSurfaceMap
          subdomains={latestScan?.subdomains || []}
          liveHosts={(latestScan?.subdomains || []).filter((row) => row.is_live)}
          endpoints={latestScan?.endpoints || []}
          jsFiles={latestScan?.javascript_assets || []}
          secrets={collectSecrets(latestScan?.javascript_assets || [])}
        />
      </section>

      <section className="hosted-ops-grid">
        <ModelStatusGrid />
        <ReportDownload
          scanId={latestScan?.id}
          targetId={backendTarget?.id}
          findings={findings}
          scanData={{ target: target?.domain, status: scanStatus, metadata: latestScan?.metadata_json }}
        />
      </section>
    </main>
  );
}
