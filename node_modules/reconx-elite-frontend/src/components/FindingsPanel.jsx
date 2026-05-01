/**
 * FindingsPanel.jsx - Real-time findings display for ReconX Elite.
 *
 * Features:
 * - Real-time updating list
 * - Severity badges (CRITICAL/HIGH/MEDIUM/LOW)
 * - Host + endpoint display
 * - One-line description
 * - Expandable full report view
 */

import React, { useState } from 'react';

const SEVERITY_STYLES = {
  critical: {
    bg: '#dc262620',
    border: '#dc2626',
    text: '#dc2626',
    icon: '🔴',
  },
  high: {
    bg: '#ea580c20',
    border: '#ea580c',
    text: '#ea580c',
    icon: '🟠',
  },
  medium: {
    bg: '#ca8a0420',
    border: '#ca8a04',
    text: '#ca8a04',
    icon: '🟡',
  },
  low: {
    bg: '#2563eb20',
    border: '#2563eb',
    text: '#2563eb',
    icon: '🔵',
  },
  info: {
    bg: '#64748b20',
    border: '#64748b',
    text: '#64748b',
    icon: '⚪',
  },
};

const FindingsPanel = ({ findings = [], scanStatus = 'idle' }) => {
  const [expandedId, setExpandedId] = useState(null);

  const toggleExpand = (id) => {
    setExpandedId(expandedId === id ? null : id);
  };

  const getSeverityStyle = (severity) => {
    return SEVERITY_STYLES[severity?.toLowerCase()] || SEVERITY_STYLES.info;
  };

  const countBySeverity = () => {
    const counts = { critical: 0, high: 0, medium: 0, low: 0, info: 0 };
    findings.forEach((f) => {
      const sev = f.severity?.toLowerCase() || 'info';
      counts[sev] = (counts[sev] || 0) + 1;
    });
    return counts;
  };

  const severityCounts = countBySeverity();
  const totalFindings = findings.length;

  // Sort by severity (critical first)
  const sortedFindings = [...findings].sort((a, b) => {
    const severityOrder = { critical: 0, high: 1, medium: 2, low: 3, info: 4 };
    const aOrder = severityOrder[a.severity?.toLowerCase()] || 4;
    const bOrder = severityOrder[b.severity?.toLowerCase()] || 4;
    return aOrder - bOrder;
  });

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h3 style={styles.title}>🐛 Findings</h3>
        <div style={styles.stats}>
          <span style={{ ...styles.stat, color: SEVERITY_STYLES.critical.text }}>
            {severityCounts.critical} Critical
          </span>
          <span style={{ ...styles.stat, color: SEVERITY_STYLES.high.text }}>
            {severityCounts.high} High
          </span>
          <span style={{ ...styles.stat, color: SEVERITY_STYLES.medium.text }}>
            {severityCounts.medium} Medium
          </span>
          <span style={{ ...styles.stat, color: SEVERITY_STYLES.low.text }}>
            {severityCounts.low} Low
          </span>
          <span style={styles.total}>Total: {totalFindings}</span>
        </div>
      </div>

      {scanStatus === 'running' && (
        <div style={styles.activeIndicator}>
          <span style={styles.pulse}></span>
          Actively discovering...
        </div>
      )}

      <div style={styles.findingsList}>
        {sortedFindings.length === 0 ? (
          <div style={styles.emptyState}>
            {scanStatus === 'running'
              ? 'Scanning for vulnerabilities...'
              : 'No findings yet. Start a scan to begin discovery.'}
          </div>
        ) : (
          sortedFindings.map((finding, index) => {
            const severity = finding.severity?.toLowerCase() || 'info';
            const style = getSeverityStyle(severity);
            const isExpanded = expandedId === finding.id || expandedId === index;

            return (
              <div
                key={finding.id || index}
                style={{
                  ...styles.finding,
                  backgroundColor: style.bg,
                  borderColor: style.border,
                }}
              >
                <div
                  style={styles.findingHeader}
                  onClick={() => toggleExpand(finding.id || index)}
                >
                  <div style={styles.findingMain}>
                    <span style={{ ...styles.severityBadge, color: style.text, borderColor: style.border }}>
                      {style.icon} {severity.toUpperCase()}
                    </span>
                    <span style={styles.findingName}>{finding.name || finding.title || 'Finding'}</span>
                  </div>
                  <div style={styles.findingMeta}>
                    <span style={styles.host}>{finding.host || finding.domain || ''}</span>
                    <span style={styles.expandIcon}>{isExpanded ? '▼' : '▶'}</span>
                  </div>
                </div>

                <div style={styles.findingDescription}>
                  {finding.description || finding.summary || 'No description available'}
                </div>

                {isExpanded && (
                  <div style={styles.expandedContent}>
                    {finding.endpoint && (
                      <div style={styles.detailRow}>
                        <span style={styles.detailLabel}>Endpoint:</span>
                        <code style={styles.detailValue}>{finding.endpoint}</code>
                      </div>
                    )}
                    {finding.template_id && (
                      <div style={styles.detailRow}>
                        <span style={styles.detailLabel}>Template:</span>
                        <code style={styles.detailValue}>{finding.template_id}</code>
                      </div>
                    )}
                    {finding.cvss_score && (
                      <div style={styles.detailRow}>
                        <span style={styles.detailLabel}>CVSS:</span>
                        <span style={styles.detailValue}>{finding.cvss_score}</span>
                      </div>
                    )}
                    {finding.cwe && (
                      <div style={styles.detailRow}>
                        <span style={styles.detailLabel}>CWE:</span>
                        <span style={styles.detailValue}>{finding.cwe}</span>
                      </div>
                    )}
                    {finding.remediation && (
                      <div style={styles.detailSection}>
                        <span style={styles.detailLabel}>Remediation:</span>
                        <p style={styles.remediationText}>{finding.remediation}</p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};

const styles = {
  container: {
    backgroundColor: '#1e293b',
    borderRadius: '12px',
    overflow: 'hidden',
    fontFamily: 'system-ui, -apple-system, sans-serif',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '16px 20px',
    borderBottom: '1px solid #334155',
    flexWrap: 'wrap',
    gap: '12px',
  },
  title: {
    margin: 0,
    fontSize: '16px',
    fontWeight: 600,
    color: '#f1f5f9',
  },
  stats: {
    display: 'flex',
    gap: '12px',
    fontSize: '12px',
    flexWrap: 'wrap',
  },
  stat: {
    fontWeight: 600,
  },
  total: {
    color: '#94a3b8',
    fontWeight: 500,
  },
  activeIndicator: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    padding: '8px 20px',
    backgroundColor: '#0f172a',
    color: '#22c55e',
    fontSize: '12px',
  },
  pulse: {
    width: '8px',
    height: '8px',
    borderRadius: '50%',
    backgroundColor: '#22c55e',
    animation: 'pulse 1.5s infinite',
  },
  findingsList: {
    maxHeight: '400px',
    overflowY: 'auto',
    padding: '12px',
  },
  emptyState: {
    padding: '40px 20px',
    textAlign: 'center',
    color: '#64748b',
    fontStyle: 'italic',
  },
  finding: {
    border: '1px solid',
    borderRadius: '8px',
    marginBottom: '8px',
    overflow: 'hidden',
    transition: 'all 0.2s ease',
  },
  findingHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '12px',
    cursor: 'pointer',
    userSelect: 'none',
  },
  findingMain: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    flex: 1,
    minWidth: 0,
  },
  severityBadge: {
    fontSize: '10px',
    fontWeight: 700,
    padding: '2px 6px',
    borderRadius: '4px',
    border: '1px solid',
    whiteSpace: 'nowrap',
  },
  findingName: {
    fontSize: '14px',
    fontWeight: 600,
    color: '#f1f5f9',
    whiteSpace: 'nowrap',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
  },
  findingMeta: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    color: '#94a3b8',
    fontSize: '12px',
  },
  host: {
    fontFamily: 'monospace',
    maxWidth: '200px',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
  },
  expandIcon: {
    fontSize: '10px',
    color: '#64748b',
  },
  findingDescription: {
    padding: '0 12px 12px 12px',
    fontSize: '13px',
    color: '#cbd5e1',
    lineHeight: '1.5',
  },
  expandedContent: {
    padding: '12px',
    backgroundColor: '#0f172a',
    borderTop: '1px solid #334155',
  },
  detailRow: {
    display: 'flex',
    gap: '8px',
    marginBottom: '8px',
    fontSize: '12px',
  },
  detailLabel: {
    color: '#94a3b8',
    fontWeight: 600,
    minWidth: '100px',
  },
  detailValue: {
    color: '#f1f5f9',
    fontFamily: 'monospace',
  },
  detailSection: {
    marginTop: '12px',
  },
  remediationText: {
    margin: '8px 0 0 0',
    fontSize: '12px',
    color: '#cbd5e1',
    lineHeight: '1.6',
  },
};

export default FindingsPanel;
