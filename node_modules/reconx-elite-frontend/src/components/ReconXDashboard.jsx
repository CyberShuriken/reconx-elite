/**
 * ReconXDashboard.jsx - Main dashboard for ReconX Elite.
 *
 * Integrates all dashboard components with WebSocket connection.
 */

import React, { useState, useCallback } from 'react';
import useScanWebSocket from '../hooks/useScanWebSocket';
import ScanProgressBar from './ScanProgressBar';
import LiveAgentLog from './LiveAgentLog';
import ModelActivityGrid from './ModelActivityGrid';
import FindingsPanel from './FindingsPanel';
import AttackSurfaceMap from './AttackSurfaceMap';
import ReportDownload from './ReportDownload';

const ReconXDashboard = ({ scanId, initialData = {} }) => {
  const [phase, setPhase] = useState(initialData.currentPhase || 0);
  const [phaseStatus, setPhaseStatus] = useState(initialData.phaseStatus || 'idle');
  const [logs, setLogs] = useState(initialData.logs || []);
  const [modelActivities, setModelActivities] = useState(initialData.modelActivities || []);
  const [findings, setFindings] = useState(initialData.findings || []);
  const [attackSurface, setAttackSurface] = useState(initialData.attackSurface || {});
  const [scanComplete, setScanComplete] = useState(false);
  const [stats, setStats] = useState(initialData.stats || {});

  // WebSocket message handlers
  const onPhaseUpdate = useCallback((data) => {
    if (data.phase !== undefined) {
      setPhase(data.phase);
    }
    if (data.status) {
      setPhaseStatus(data.status);
    }
    if (data.progress !== undefined) {
      setStats((prev) => ({ ...prev, progress: data.progress }));
    }
  }, []);

  const onModelActivity = useCallback((data) => {
    setModelActivities((prev) => {
      const newActivities = [...prev, data];
      // Keep last 50 activities
      return newActivities.slice(-50);
    });
  }, []);

  const onFinding = useCallback((data) => {
    setFindings((prev) => {
      // Check if finding already exists
      const exists = prev.some((f) => f.id === data.id);
      if (exists) {
        return prev.map((f) => (f.id === data.id ? { ...f, ...data } : f));
      }
      return [...prev, data];
    });
  }, []);

  const onToolLog = useCallback((data) => {
    const logEntry = {
      id: Date.now() + Math.random(),
      timestamp: new Date().toISOString(),
      level: data.level || 'info',
      event: data.event || 'tool',
      message: data.message || data.output || JSON.stringify(data),
      tool: data.tool,
      hosts: data.hosts,
      phase: data.phase,
    };
    setLogs((prev) => [...prev.slice(-499), logEntry]);
  }, []);

  const onMessage = useCallback((data) => {
    // Handle stats updates
    if (data.type === 'stats_update') {
      setStats((prev) => ({ ...prev, ...data.data }));
    }
    // Handle attack surface updates
    if (data.type === 'attack_surface') {
      setAttackSurface((prev) => ({ ...prev, ...data.data }));
    }
  }, []);

  const onComplete = useCallback((data) => {
    setScanComplete(true);
    setPhaseStatus('completed');
    setStats((prev) => ({ ...prev, summary: data }));
  }, []);

  // WebSocket connection
  const { readyStateLabel, isConnected, reconnectCount } = useScanWebSocket(scanId, {
    onMessage,
    onPhaseUpdate,
    onModelActivity,
    onFinding,
    onToolLog,
    onComplete,
  });

  return (
    <div style={styles.container}>
      {/* Header */}
      <div style={styles.header}>
        <div>
          <h1 style={styles.title}>ReconX Elite</h1>
          <p style={styles.subtitle}>10-Phase Autonomous Security Pipeline</p>
        </div>
        <div style={styles.connectionStatus}>
          <span style={styles.statusBadge(isConnected)}>{readyStateLabel}</span>
          {reconnectCount > 0 && (
            <span style={styles.reconnectBadge}>Reconnects: {reconnectCount}</span>
          )}
        </div>
      </div>

      {/* Main Grid */}
      <div style={styles.mainGrid}>
        {/* Left Column - Progress & Logs */}
        <div style={styles.leftColumn}>
          <ScanProgressBar
            currentPhase={phase}
            phaseStatus={phaseStatus}
            progress={stats.progress || 0}
          />
          <LiveAgentLog logs={logs} maxHeight="400px" />
        </div>

        {/* Right Column - Model Activity & Findings */}
        <div style={styles.rightColumn}>
          <ModelActivityGrid activities={modelActivities} />
          <FindingsPanel findings={findings} scanStatus={phaseStatus} />
        </div>
      </div>

      {/* Bottom Section */}
      <div style={styles.bottomGrid}>
        <AttackSurfaceMap
          subdomains={attackSurface.subdomains || []}
          liveHosts={attackSurface.liveHosts || []}
          ports={attackSurface.ports || {}}
          jsFiles={attackSurface.jsFiles || []}
          secrets={attackSurface.secrets || []}
          endpoints={attackSurface.endpoints || []}
        />
        <ReportDownload
          scanId={scanId}
          findings={findings}
          scanData={{
            phase,
            status: phaseStatus,
            complete: scanComplete,
            stats,
          }}
        />
      </div>
    </div>
  );
};

const styles = {
  container: {
    padding: '20px',
    backgroundColor: '#0f172a',
    minHeight: '100vh',
    fontFamily: 'system-ui, -apple-system, sans-serif',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '24px',
    paddingBottom: '16px',
    borderBottom: '1px solid #334155',
  },
  title: {
    margin: 0,
    fontSize: '24px',
    fontWeight: 700,
    color: '#f1f5f9',
    background: 'linear-gradient(90deg, #6366f1, #8b5cf6)',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
  },
  subtitle: {
    margin: '4px 0 0 0',
    fontSize: '13px',
    color: '#94a3b8',
  },
  connectionStatus: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  },
  statusBadge: (isConnected) => ({
    padding: '6px 12px',
    backgroundColor: isConnected ? '#22c55e20' : '#f59e0b20',
    color: isConnected ? '#22c55e' : '#f59e0b',
    borderRadius: '4px',
    fontSize: '12px',
    fontWeight: 600,
    textTransform: 'uppercase',
  }),
  reconnectBadge: {
    padding: '4px 8px',
    backgroundColor: '#ef444420',
    color: '#ef4444',
    borderRadius: '4px',
    fontSize: '11px',
  },
  mainGrid: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: '20px',
    marginBottom: '20px',
  },
  leftColumn: {
    display: 'flex',
    flexDirection: 'column',
    gap: '20px',
  },
  rightColumn: {
    display: 'flex',
    flexDirection: 'column',
    gap: '20px',
  },
  bottomGrid: {
    display: 'grid',
    gridTemplateColumns: '2fr 1fr',
    gap: '20px',
  },
};

export default ReconXDashboard;
