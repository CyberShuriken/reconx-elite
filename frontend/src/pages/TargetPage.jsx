import { Suspense, lazy, useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { apiRequest } from "../api";

const OverviewTab = lazy(() => import("../components/OverviewTab"));

export default function TargetPage() {
  const { targetId } = useParams();
  const token = localStorage.getItem("reconx_token");
  const [target, setTarget] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");
  const [endpointSearch, setEndpointSearch] = useState("");
  const [activeTab, setActiveTab] = useState("overview");
  const [selectedTemplates, setSelectedTemplates] = useState(["cves", "exposures"]);
  const [selectedSeverities, setSelectedSeverities] = useState(["high", "critical"]);
  const [severityFilter, setSeverityFilter] = useState("all");
  const [subdomainFilter, setSubdomainFilter] = useState("all");
  const templateOptions = ["cves", "exposures", "misconfiguration", "fuzzing"];
  const severityOptions = ["low", "medium", "high", "critical"];

  async function fetchTarget() {
    setIsLoading(true);
    try {
      const data = await apiRequest(`/targets/${targetId}`, { token });
      setTarget(data);
      setError("");
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    fetchTarget();
    const interval = setInterval(fetchTarget, 5000);
    return () => clearInterval(interval);
  }, [targetId]);

  async function triggerScan() {
    setError("");
    try {
      await apiRequest(`/scan/${targetId}`, { method: "POST", token });
      fetchTarget();
    } catch (err) {
      setError(err.message);
    }
  }

  async function triggerConfiguredScan() {
    setError("");
    try {
      await apiRequest(`/scan/${targetId}/config`, {
        method: "POST",
        token,
        body: {
          selected_templates: selectedTemplates,
          severity_filter: selectedSeverities,
        },
      });
      fetchTarget();
    } catch (err) {
      setError(err.message);
    }
  }

  function toggleItem(values, setValues, value) {
    if (values.includes(value)) {
      setValues(values.filter((v) => v !== value));
    } else {
      setValues([...values, value]);
    }
  }

  const latestScan = useMemo(() => {
    if (!target?.scans?.length) return null;
    return [...target.scans].sort((a, b) => b.id - a.id)[0];
  }, [target]);

  const scanSubdomains = latestScan?.subdomains || [];
  const scanEndpoints = latestScan?.endpoints || [];
  const scanVulns = latestScan?.vulnerabilities || [];
  const scanLogs = latestScan?.logs || [];

  const summary = useMemo(() => {
    const totalSubdomains = scanSubdomains.length;
    const liveHosts = scanSubdomains.filter((s) => s.is_live).length;
    const endpoints = scanEndpoints.length;
    const severities = { low: 0, medium: 0, high: 0, critical: 0, info: 0 };
    for (const vuln of scanVulns) {
      const sev = (vuln.severity || "info").toLowerCase();
      if (severities[sev] === undefined) severities.info += 1;
      else severities[sev] += 1;
    }
    return {
      totalSubdomains,
      liveHosts,
      endpoints,
      vulnerabilities: scanVulns.length,
      severities,
    };
  }, [scanSubdomains, scanEndpoints, scanVulns]);

  const severityChartData = useMemo(
    () => [
      { severity: "low", count: summary.severities.low },
      { severity: "medium", count: summary.severities.medium },
      { severity: "high", count: summary.severities.high },
      { severity: "critical", count: summary.severities.critical },
      { severity: "info", count: summary.severities.info },
    ],
    [summary]
  );

  const progressTimelineData = useMemo(() => {
    let cumulative = 0;
    return scanLogs.map((log, index) => {
      cumulative += log.duration_ms || 0;
      return {
        idx: index + 1,
        step: log.step,
        durationMs: log.duration_ms || 0,
        cumulativeMs: cumulative,
      };
    });
  }, [scanLogs]);

  const filteredSubdomains = scanSubdomains.filter((row) => {
    if (subdomainFilter === "live") return !!row.is_live;
    if (subdomainFilter === "dead") return !row.is_live;
    return true;
  });

  const filteredEndpoints = scanEndpoints.filter((e) =>
    e.url.toLowerCase().includes(endpointSearch.toLowerCase())
  );

  const filteredVulns = scanVulns.filter((v) => {
    if (severityFilter === "all") return true;
    return (v.severity || "").toLowerCase() === severityFilter;
  });

  if (isLoading) {
    return (
      <div className="container">
        <div className="row">
          <h1>Target Details</h1>
          <Link to="/">Back</Link>
        </div>
        <div className="skeleton-grid">
          <div className="skeleton-card" />
          <div className="skeleton-card" />
          <div className="skeleton-card" />
          <div className="skeleton-card" />
        </div>
        <div className="skeleton-block" />
      </div>
    );
  }

  return (
    <div className="container">
      <div className="row">
        <h1>Target Details</h1>
        <Link to="/">Back</Link>
      </div>
      {target && <h2>{target.domain}</h2>}
      {error && <p className="error card">Scan error: {error}</p>}
      <button onClick={triggerScan}>Trigger Default Scan</button>
      <div className="card">
        <h3>Advanced Nuclei Config</h3>
        <p>Select template categories:</p>
        <div className="row">
          {templateOptions.map((option) => (
            <label key={option}>
              <input
                type="checkbox"
                checked={selectedTemplates.includes(option)}
                onChange={() => toggleItem(selectedTemplates, setSelectedTemplates, option)}
              />
              {option}
            </label>
          ))}
        </div>
        <p>Select severity:</p>
        <div className="row">
          {severityOptions.map((option) => (
            <label key={option}>
              <input
                type="checkbox"
                checked={selectedSeverities.includes(option)}
                onChange={() => toggleItem(selectedSeverities, setSelectedSeverities, option)}
              />
              {option}
            </label>
          ))}
        </div>
        <button onClick={triggerConfiguredScan}>Trigger Configured Scan</button>
      </div>
      {latestScan && (
        <p>
          Latest scan #{latestScan.id} - <strong>{latestScan.status}</strong> (
          {latestScan.metadata_json?.step || "unknown"})
        </p>
      )}

      <div className="tabs-row">
        <button className={activeTab === "overview" ? "tab tab-active" : "tab"} onClick={() => setActiveTab("overview")}>
          Overview
        </button>
        <button className={activeTab === "recon" ? "tab tab-active" : "tab"} onClick={() => setActiveTab("recon")}>
          Recon Data
        </button>
        <button className={activeTab === "vulns" ? "tab tab-active" : "tab"} onClick={() => setActiveTab("vulns")}>
          Vulnerabilities
        </button>
      </div>

      {activeTab === "overview" && (
        <Suspense fallback={<div className="chart-skeleton" />}>
          <OverviewTab
            summary={summary}
            severityChartData={severityChartData}
            progressTimelineData={progressTimelineData}
          />
        </Suspense>
      )}

      {activeTab === "recon" && (
        <>
          <div className="card">
            <h3>Subdomains</h3>
            <div className="filters-row">
              <select value={subdomainFilter} onChange={(e) => setSubdomainFilter(e.target.value)}>
                <option value="all">All</option>
                <option value="live">Live only</option>
                <option value="dead">Dead only</option>
              </select>
            </div>
            <table>
              <thead>
                <tr>
                  <th>Hostname</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {filteredSubdomains.map((row) => (
                  <tr key={row.hostname}>
                    <td>{row.hostname}</td>
                    <td>{row.is_live ? "Live" : "Dead"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="card">
            <h3>Endpoints</h3>
            <input
              placeholder="Search endpoint..."
              value={endpointSearch}
              onChange={(e) => setEndpointSearch(e.target.value)}
            />
            <table>
              <thead>
                <tr>
                  <th>URL</th>
                </tr>
              </thead>
              <tbody>
                {filteredEndpoints.map((row) => (
                  <tr key={row.url}>
                    <td>{row.url}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      {activeTab === "vulns" && (
        <div className="card">
          <h3>Vulnerabilities</h3>
          <div className="filters-row">
            <select value={severityFilter} onChange={(e) => setSeverityFilter(e.target.value)}>
              <option value="all">All severities</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
              <option value="info">Info</option>
            </select>
          </div>
          <table>
            <thead>
              <tr>
                <th>Severity</th>
                <th>Template</th>
                <th>Matched URL</th>
                <th>Host</th>
                <th>Description</th>
              </tr>
            </thead>
            <tbody>
              {filteredVulns.map((row, idx) => (
                <tr key={`${row.template_id}-${idx}`}>
                  <td>{row.severity}</td>
                  <td>{row.template_id}</td>
                  <td>{row.matched_url || "-"}</td>
                  <td>{row.host || "-"}</td>
                  <td>{row.description || "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
