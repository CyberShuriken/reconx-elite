/**
 * ScanProgressBar.jsx - 10-phase progress visualization for ReconX Elite.
 *
 * Real-time progress bar showing:
 * - 10 phases (0-10) with names
 * - Current phase status
 * - Percentage complete per phase
 * - Color coding by status
 */

import React from 'react';

const PHASES = [
  { num: 0, name: 'Init', icon: '⚙️', color: '#6366f1' },
  { num: 1, name: 'Recon', icon: '🔍', color: '#8b5cf6' },
  { num: 2, name: 'Profile', icon: '📊', color: '#a855f7' },
  { num: 3, name: 'Ports', icon: '🚪', color: '#d946ef' },
  { num: 4, name: 'JS Analysis', icon: '📜', color: '#ec4899' },
  { num: 5, name: 'Parameters', icon: '🔗', color: '#f43f5e' },
  { num: 6, name: 'Vuln Test', icon: '⚡', color: '#f97316' },
  { num: 7, name: 'AI Analysis', icon: '🧠', color: '#eab308' },
  { num: 8, name: 'Logic Test', icon: '🧩', color: '#22c55e' },
  { num: 9, name: 'Correlate', icon: '📈', color: '#14b8a6' },
  { num: 10, name: 'Report', icon: '📄', color: '#06b6d4' },
];

const ScanProgressBar = ({ currentPhase = 0, phaseProgress = {}, phaseStatus = {} }) => {
  const getStatusColor = (phase) => {
    const status = phaseStatus[phase];
    if (status === 'completed') return '#22c55e';
    if (status === 'running') return PHASES[phase].color;
    if (status === 'error') return '#ef4444';
    if (status === 'waiting') return '#64748b';
    return '#334155'; // not started
  };

  const getStatusIcon = (phase) => {
    const status = phaseStatus[phase];
    if (status === 'completed') return '✓';
    if (status === 'running') return '⟳';
    if (status === 'error') return '✕';
    return phase;
  };

  const overallProgress = Math.round((currentPhase / 10) * 100);

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h3 style={styles.title}>Scan Progress</h3>
        <span style={styles.percentage}>{overallProgress}% Complete</span>
      </div>

      {/* Overall progress bar */}
      <div style={styles.overallBar}>
        <div
          style={{
            ...styles.overallFill,
            width: `${overallProgress}%`,
            background: `linear-gradient(90deg, #6366f1 0%, #06b6d4 100%)`,
          }}
        />
      </div>

      {/* Phase indicators */}
      <div style={styles.phasesContainer}>
        {PHASES.map((phase) => {
          const isActive = phase.num === currentPhase;
          const isCompleted = phase.num < currentPhase;
          const progress = phaseProgress[phase.num] || 0;

          return (
            <div
              key={phase.num}
              style={{
                ...styles.phase,
                borderColor: getStatusColor(phase.num),
                backgroundColor: isActive
                  ? `${PHASES[phase.num].color}20`
                  : isCompleted
                  ? '#22c55e20'
                  : 'transparent',
              }}
            >
              <div
                style={{
                  ...styles.phaseIcon,
                  backgroundColor: getStatusColor(phase.num),
                }}
              >
                {getStatusIcon(phase.num)}
              </div>
              <div style={styles.phaseInfo}>
                <span style={styles.phaseNum}>P{phase.num}</span>
                <span style={styles.phaseName}>{phase.name}</span>
                {isActive && (
                  <div style={styles.miniBar}>
                    <div
                      style={{
                        ...styles.miniFill,
                        width: `${progress}%`,
                        backgroundColor: phase.color,
                      }}
                    />
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Current phase details */}
      {currentPhase >= 0 && currentPhase <= 10 && (
        <div style={styles.currentPhase}>
          <span style={styles.currentLabel}>Current:</span>
          <span style={styles.currentName}>
            {PHASES[currentPhase].icon} Phase {currentPhase}: {PHASES[currentPhase].name}
          </span>
          <span style={styles.currentProgress}>
            {phaseProgress[currentPhase] || 0}%
          </span>
        </div>
      )}
    </div>
  );
};

const styles = {
  container: {
    backgroundColor: '#1e293b',
    borderRadius: '12px',
    padding: '20px',
    color: '#f1f5f9',
    fontFamily: 'system-ui, -apple-system, sans-serif',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '16px',
  },
  title: {
    margin: 0,
    fontSize: '18px',
    fontWeight: 600,
  },
  percentage: {
    fontSize: '16px',
    fontWeight: 700,
    color: '#06b6d4',
  },
  overallBar: {
    height: '8px',
    backgroundColor: '#334155',
    borderRadius: '4px',
    overflow: 'hidden',
    marginBottom: '20px',
  },
  overallFill: {
    height: '100%',
    borderRadius: '4px',
    transition: 'width 0.3s ease',
  },
  phasesContainer: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '8px',
    marginBottom: '16px',
  },
  phase: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    padding: '8px 12px',
    borderRadius: '8px',
    border: '2px solid',
    minWidth: '100px',
    transition: 'all 0.2s ease',
  },
  phaseIcon: {
    width: '24px',
    height: '24px',
    borderRadius: '50%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '12px',
    fontWeight: 'bold',
    color: '#fff',
  },
  phaseInfo: {
    display: 'flex',
    flexDirection: 'column',
    gap: '2px',
  },
  phaseNum: {
    fontSize: '10px',
    color: '#94a3b8',
    textTransform: 'uppercase',
  },
  phaseName: {
    fontSize: '12px',
    fontWeight: 600,
    color: '#f1f5f9',
  },
  miniBar: {
    height: '3px',
    backgroundColor: '#334155',
    borderRadius: '2px',
    overflow: 'hidden',
    marginTop: '4px',
    width: '60px',
  },
  miniFill: {
    height: '100%',
    borderRadius: '2px',
    transition: 'width 0.3s ease',
  },
  currentPhase: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    padding: '12px',
    backgroundColor: '#0f172a',
    borderRadius: '8px',
    borderLeft: '4px solid #06b6d4',
  },
  currentLabel: {
    fontSize: '12px',
    color: '#94a3b8',
    textTransform: 'uppercase',
  },
  currentName: {
    fontSize: '14px',
    fontWeight: 600,
    color: '#f1f5f9',
    flex: 1,
  },
  currentProgress: {
    fontSize: '16px',
    fontWeight: 700,
    color: '#06b6d4',
  },
};

export default ScanProgressBar;
