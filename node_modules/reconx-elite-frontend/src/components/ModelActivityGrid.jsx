/**
 * ModelActivityGrid.jsx - AI model activity visualization for ReconX Elite.
 *
 * Features:
 * - Real-time model activity grid
 * - Shows which AI is working on which task
 * - Token usage tracking
 * - Color-coded by model role
 */

import React from 'react';

const MODEL_ROLES = {
  orchestrator: { name: 'Orchestrator', color: '#6366f1', icon: '🎛️' },
  recursive_recon: { name: 'Recon Specialist', color: '#8b5cf6', icon: '🔍' },
  context_profiler: { name: 'Context Profiler', color: '#a855f7', icon: '📊' },
  vuln_analyst: { name: 'Vuln Analyst', color: '#d946ef', icon: '⚡' },
  exploit_chain: { name: 'Exploit Chain', color: '#ec4899', icon: '🔗' },
  poc_generator: { name: 'PoC Generator', color: '#f43f5e', icon: '📝' },
  pattern_recognizer: { name: 'Pattern AI', color: '#f97316', icon: '🧩' },
  business_logic: { name: 'Business Logic', color: '#eab308', icon: '🏢' },
  report_writer: { name: 'Report Writer', color: '#22c55e', icon: '📄' },
  gemini_fallback: { name: 'Gemini Fallback', color: '#06b6d4', icon: '♊' },
};

const ModelActivityGrid = ({ activities = [] }) => {
  // Group activities by model role
  const groupedActivities = activities.reduce((acc, activity) => {
    const role = activity.model_role || 'unknown';
    if (!acc[role]) {
      acc[role] = [];
    }
    acc[role].push(activity);
    return acc;
  }, {});

  // Calculate stats
  const totalTokens = activities.reduce((sum, a) => sum + (a.tokens_used || 0), 0);
  const activeModels = Object.keys(groupedActivities).length;

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h3 style={styles.title}>🤖 AI Model Activity</h3>
        <div style={styles.stats}>
          <span style={styles.stat}>Active: {activeModels}</span>
          <span style={styles.stat}>Tokens: {totalTokens.toLocaleString()}</span>
        </div>
      </div>

      <div style={styles.grid}>
        {Object.entries(MODEL_ROLES).map(([roleKey, roleInfo]) => {
          const roleActivities = groupedActivities[roleKey] || [];
          const isActive = roleActivities.length > 0;
          const latestActivity = roleActivities[roleActivities.length - 1];

          return (
            <div
              key={roleKey}
              style={{
                ...styles.modelCard,
                borderColor: roleInfo.color,
                opacity: isActive ? 1 : 0.5,
              }}
            >
              <div style={styles.modelHeader}>
                <span style={styles.modelIcon}>{roleInfo.icon}</span>
                <span style={{ ...styles.modelName, color: roleInfo.color }}>
                  {roleInfo.name}
                </span>
                {isActive && <span style={styles.activeIndicator}>●</span>}
              </div>

              {isActive ? (
                <div style={styles.activityContent}>
                  <div style={styles.currentAction}>{latestActivity?.action || 'Processing...'}</div>
                  {latestActivity?.scan_id && (
                    <div style={styles.scanRef}>Scan #{latestActivity.scan_id.slice(-6)}</div>
                  )}
                  {latestActivity?.tokens_used > 0 && (
                    <div style={styles.tokenCount}>
                      {latestActivity.tokens_used.toLocaleString()} tokens
                    </div>
                  )}
                  {roleActivities.length > 1 && (
                    <div style={styles.activityCount}>+{roleActivities.length - 1} more</div>
                  )}
                </div>
              ) : (
                <div style={styles.inactiveText}>Idle</div>
              )}
            </div>
          );
        })}
      </div>

      {activities.length === 0 && (
        <div style={styles.emptyState}>No AI activity yet. Start a scan to see model activity.</div>
      )}
    </div>
  );
};

const styles = {
  container: {
    backgroundColor: '#1e293b',
    borderRadius: '12px',
    overflow: 'hidden',
    fontFamily: 'system-ui, -apple-system, sans-serif',
    color: '#f1f5f9',
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
  },
  stats: {
    display: 'flex',
    gap: '16px',
    fontSize: '13px',
    color: '#94a3b8',
  },
  stat: {
    fontWeight: 500,
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
    gap: '12px',
    padding: '16px',
  },
  modelCard: {
    padding: '14px',
    backgroundColor: '#0f172a',
    borderRadius: '8px',
    border: '2px solid',
    transition: 'all 0.2s ease',
  },
  modelHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    marginBottom: '8px',
  },
  modelIcon: {
    fontSize: '18px',
  },
  modelName: {
    fontSize: '13px',
    fontWeight: 600,
    flex: 1,
  },
  activeIndicator: {
    color: '#22c55e',
    fontSize: '10px',
    animation: 'pulse 1.5s infinite',
  },
  activityContent: {
    fontSize: '12px',
  },
  currentAction: {
    color: '#f1f5f9',
    fontWeight: 500,
    marginBottom: '4px',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
  },
  scanRef: {
    color: '#64748b',
    fontSize: '11px',
    fontFamily: 'monospace',
  },
  tokenCount: {
    color: '#94a3b8',
    fontSize: '11px',
    marginTop: '4px',
  },
  activityCount: {
    color: '#8b5cf6',
    fontSize: '11px',
    marginTop: '4px',
  },
  inactiveText: {
    color: '#64748b',
    fontSize: '12px',
    fontStyle: 'italic',
  },
  emptyState: {
    padding: '40px 20px',
    textAlign: 'center',
    color: '#64748b',
    fontStyle: 'italic',
  },
};

export default ModelActivityGrid;
