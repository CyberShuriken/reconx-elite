/**
 * LiveAgentLog.jsx - Terminal-style agent log for ReconX Elite.
 *
 * Real-time scrolling feed showing:
 * - Tool executions (white)
 * - AI model decisions (cyan)
 * - Findings (red/orange/yellow/blue by severity)
 * - Phase transitions
 */

import React, { useRef, useEffect } from 'react';

const SEVERITY_COLORS = {
  critical: '#dc2626',
  high: '#ea580c',
  medium: '#ca8a04',
  low: '#2563eb',
  info: '#64748b',
};

const EVENT_COLORS = {
  tool: '#f8fafc',
  ai: '#22d3ee',
  phase: '#a855f7',
  finding: '#fbbf24',
  error: '#ef4444',
  warning: '#f97316',
};

const LiveAgentLog = ({ logs = [], maxLines = 100 }) => {
  const logEndRef = useRef(null);

  // Auto-scroll to bottom
  useEffect(() => {
    if (logEndRef.current) {
      logEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs]);

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  const getLogStyle = (log) => {
    const eventType = log.event || 'info';
    const severity = log.severity || log.severity_level;

    // Finding with severity
    if (eventType === 'finding' && severity) {
      return { color: SEVERITY_COLORS[severity] || SEVERITY_COLORS.info };
    }

    // Event type colors
    return { color: EVENT_COLORS[eventType] || EVENT_COLORS.info };
  };

  const getLogIcon = (log) => {
    const eventType = log.event;

    switch (eventType) {
      case 'tool_log':
        return '⚙️';
      case 'model_activity':
        return '🤖';
      case 'phase_update':
        return '📍';
      case 'finding':
        return '🐛';
      case 'scan_warning':
        return '⚠️';
      case 'scan_hard_stop':
        return '🛑';
      case 'scan_phase_transition':
        return '🔄';
      default:
        return '•';
    }
  };

  const formatMessage = (log) => {
    const { event, tool, model_role, phase, message, hosts, status } = log;

    if (event === 'tool_log' && tool) {
      return `${tool} ${status === 'running' ? 'started' : 'completed'}${hosts ? ` (${hosts} hosts)` : ''}`;
    }

    if (event === 'model_activity' && model_role) {
      return `AI [${model_role}]: ${log.action || 'processing'}`;
    }

    if (event === 'phase_update' && phase !== undefined) {
      return `Phase ${phase}: ${message || status}`;
    }

    if (event === 'finding') {
      return `[${log.severity?.toUpperCase() || 'FINDING'}] ${log.host || ''} ${message || ''}`;
    }

    return message || JSON.stringify(log);
  };

  // Limit logs to maxLines
  const displayLogs = logs.slice(-maxLines);

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h3 style={styles.title}>🖥️ Agent Log</h3>
        <span style={styles.status}>● Live</span>
      </div>

      <div style={styles.terminal}>
        <div style={styles.terminalHeader}>
          <span style={styles.dotRed}></span>
          <span style={styles.dotYellow}></span>
          <span style={styles.dotGreen}></span>
          <span style={styles.terminalTitle}>reconx-agent.log</span>
        </div>

        <div style={styles.logContent}>
          {displayLogs.length === 0 ? (
            <div style={styles.emptyState}>Waiting for scan activity...</div>
          ) : (
            displayLogs.map((log, index) => (
              <div key={index} style={styles.logLine}>
                <span style={styles.timestamp}>{formatTimestamp(log.timestamp)}</span>
                <span style={styles.icon}>{getLogIcon(log)}</span>
                <span style={{ ...styles.message, ...getLogStyle(log) }}>
                  {formatMessage(log)}
                </span>
              </div>
            ))
          )}
          <div ref={logEndRef} />
        </div>
      </div>

      <div style={styles.legend}>
        <span style={styles.legendItem}>
          <span style={{ ...styles.legendDot, backgroundColor: EVENT_COLORS.tool }}></span>
          Tool
        </span>
        <span style={styles.legendItem}>
          <span style={{ ...styles.legendDot, backgroundColor: EVENT_COLORS.ai }}></span>
          AI
        </span>
        <span style={styles.legendItem}>
          <span style={{ ...styles.legendDot, backgroundColor: SEVERITY_COLORS.critical }}></span>
          Critical
        </span>
        <span style={styles.legendItem}>
          <span style={{ ...styles.legendDot, backgroundColor: SEVERITY_COLORS.high }}></span>
          High
        </span>
        <span style={styles.legendItem}>
          <span style={{ ...styles.legendDot, backgroundColor: SEVERITY_COLORS.medium }}></span>
          Medium
        </span>
        <span style={styles.legendItem}>
          <span style={{ ...styles.legendDot, backgroundColor: SEVERITY_COLORS.low }}></span>
          Low
        </span>
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
  },
  title: {
    margin: 0,
    fontSize: '16px',
    fontWeight: 600,
    color: '#f1f5f9',
  },
  status: {
    fontSize: '12px',
    color: '#22c55e',
    fontWeight: 600,
  },
  terminal: {
    backgroundColor: '#0f172a',
    fontFamily: 'monospace',
  },
  terminalHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    padding: '12px 16px',
    backgroundColor: '#1e293b',
    borderBottom: '1px solid #334155',
  },
  dotRed: {
    width: '12px',
    height: '12px',
    borderRadius: '50%',
    backgroundColor: '#ef4444',
  },
  dotYellow: {
    width: '12px',
    height: '12px',
    borderRadius: '50%',
    backgroundColor: '#f59e0b',
  },
  dotGreen: {
    width: '12px',
    height: '12px',
    borderRadius: '50%',
    backgroundColor: '#22c55e',
  },
  terminalTitle: {
    marginLeft: '8px',
    fontSize: '12px',
    color: '#94a3b8',
  },
  logContent: {
    padding: '12px 16px',
    height: '300px',
    overflowY: 'auto',
    fontSize: '13px',
    lineHeight: '1.6',
  },
  emptyState: {
    color: '#64748b',
    textAlign: 'center',
    padding: '40px 0',
    fontStyle: 'italic',
  },
  logLine: {
    display: 'flex',
    alignItems: 'flex-start',
    gap: '8px',
    marginBottom: '4px',
    fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace',
  },
  timestamp: {
    color: '#64748b',
    fontSize: '11px',
    minWidth: '70px',
    flexShrink: 0,
  },
  icon: {
    fontSize: '12px',
    flexShrink: 0,
  },
  message: {
    flex: 1,
    wordBreak: 'break-word',
  },
  legend: {
    display: 'flex',
    gap: '16px',
    padding: '12px 20px',
    backgroundColor: '#1e293b',
    borderTop: '1px solid #334155',
    fontSize: '12px',
    color: '#94a3b8',
  },
  legendItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
  },
  legendDot: {
    width: '8px',
    height: '8px',
    borderRadius: '50%',
  },
};

export default LiveAgentLog;
