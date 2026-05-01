/**
 * AttackSurfaceMap.jsx - Attack surface visualization for ReconX Elite.
 *
 * Features:
 * - Total subdomains count
 * - Live hosts pie chart
 * - Open ports heat map
 * - JS files analyzed count
 * - Secrets found counter
 */

import React from 'react';

const AttackSurfaceMap = ({
  subdomains = [],
  liveHosts = [],
  ports = {},
  jsFiles = [],
  secrets = [],
  endpoints = [],
}) => {
  // Calculate statistics
  const totalSubdomains = subdomains.length;
  const liveHostCount = liveHosts.length;
  const deadHostCount = totalSubdomains - liveHostCount;
  const interestingHosts = liveHosts.filter((h) => h.is_interesting || h.tech_detected).length;

  const jsFileCount = jsFiles.length;
  const secretCount = secrets.length;
  const endpointCount = endpoints.length;

  // Port analysis
  const portCounts = {};
  Object.values(ports).forEach((hostPorts) => {
    hostPorts.forEach((port) => {
      portCounts[port] = (portCounts[port] || 0) + 1;
    });
  });

  const topPorts = Object.entries(portCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 6);

  // Stats cards data
  const stats = [
    { label: 'Subdomains', value: totalSubdomains, icon: '🌐', color: '#8b5cf6' },
    { label: 'Live Hosts', value: liveHostCount, icon: '🟢', color: '#22c55e' },
    { label: 'JS Files', value: jsFileCount, icon: '📜', color: '#f59e0b' },
    { label: 'Secrets', value: secretCount, icon: '🔑', color: '#ef4444' },
    { label: 'Endpoints', value: endpointCount, icon: '🔗', color: '#06b6d4' },
  ];

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h3 style={styles.title}>🗺️ Attack Surface Map</h3>
      </div>

      {/* Stats Grid */}
      <div style={styles.statsGrid}>
        {stats.map((stat, index) => (
          <div key={index} style={{ ...styles.statCard, borderColor: stat.color }}>
            <div style={{ ...styles.statIcon, backgroundColor: `${stat.color}20`, color: stat.color }}>
              {stat.icon}
            </div>
            <div style={{ ...styles.statValue, color: stat.color }}>
              {stat.value}
            </div>
            <div style={styles.statLabel}>{stat.label}</div>
          </div>
        ))}
      </div>

      {/* Host Status Distribution */}
      <div style={styles.section}>
        <h4 style={styles.sectionTitle}>Host Status Distribution</h4>
        <div style={styles.distribution}>
          <div style={styles.distributionBar}>
            {totalSubdomains > 0 && (
              <>
                <div
                  style={{
                    ...styles.distSegment,
                    backgroundColor: '#22c55e',
                    width: `${(liveHostCount / totalSubdomains) * 100}%`,
                  }}
                  title={`Live: ${liveHostCount}`}
                />
                <div
                  style={{
                    ...styles.distSegment,
                    backgroundColor: '#f59e0b',
                    width: `${(interestingHosts / totalSubdomains) * 100}%`,
                  }}
                  title={`Interesting: ${interestingHosts}`}
                />
                <div
                  style={{
                    ...styles.distSegment,
                    backgroundColor: '#64748b',
                    width: `${(deadHostCount / totalSubdomains) * 100}%`,
                  }}
                  title={`Dead: ${deadHostCount}`}
                />
              </>
            )}
          </div>
          <div style={styles.legend}>
            <span style={styles.legendItem}>
              <span style={{ ...styles.legendDot, backgroundColor: '#22c55e' }}></span>
              Live ({liveHostCount})
            </span>
            <span style={styles.legendItem}>
              <span style={{ ...styles.legendDot, backgroundColor: '#f59e0b' }}></span>
              Interesting ({interestingHosts})
            </span>
            <span style={styles.legendItem}>
              <span style={{ ...styles.legendDot, backgroundColor: '#64748b' }}></span>
              Dead ({deadHostCount})
            </span>
          </div>
        </div>
      </div>

      {/* Top Ports Heat Map */}
      {topPorts.length > 0 && (
        <div style={styles.section}>
          <h4 style={styles.sectionTitle}>🔥 Top Open Ports</h4>
          <div style={styles.portGrid}>
            {topPorts.map(([port, count]) => {
              const intensity = Math.min((count / liveHostCount) * 100, 100);
              return (
                <div
                  key={port}
                  style={{
                    ...styles.portCell,
                    backgroundColor: `rgba(239, 68, 68, ${intensity / 100})`,
                    borderColor: `rgba(239, 68, 68, ${Math.max(intensity / 100, 0.3)})`,
                  }}
                >
                  <div style={styles.portNumber}>{port}</div>
                  <div style={styles.portCount}>{count} hosts</div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Service Summary */}
      {liveHosts.length > 0 && (
        <div style={styles.section}>
          <h4 style={styles.sectionTitle}>Detected Services</h4>
          <div style={styles.servicesList}>
            {liveHosts.slice(0, 5).map((host, index) => (
              <div key={index} style={styles.serviceItem}>
                <span style={styles.serviceHost}>{host.domain || host.subdomain}</span>
                <span style={styles.serviceTech}>{host.tech || host.tech_detected || 'Unknown'}</span>
                <span
                  style={{
                    ...styles.serviceStatus,
                    backgroundColor: host.status === 200 ? '#22c55e20' : '#f59e0b20',
                    color: host.status === 200 ? '#22c55e' : '#f59e0b',
                  }}
                >
                  {host.status || '???'}
                </span>
              </div>
            ))}
          </div>
        </div>
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
    padding: '16px 20px',
    borderBottom: '1px solid #334155',
  },
  title: {
    margin: 0,
    fontSize: '16px',
    fontWeight: 600,
  },
  statsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(100px, 1fr))',
    gap: '12px',
    padding: '16px 20px',
    borderBottom: '1px solid #334155',
  },
  statCard: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    padding: '16px',
    backgroundColor: '#0f172a',
    borderRadius: '8px',
    border: '2px solid',
  },
  statIcon: {
    width: '40px',
    height: '40px',
    borderRadius: '50%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '20px',
    marginBottom: '8px',
  },
  statValue: {
    fontSize: '24px',
    fontWeight: 700,
    marginBottom: '4px',
  },
  statLabel: {
    fontSize: '12px',
    color: '#94a3b8',
    textTransform: 'uppercase',
  },
  section: {
    padding: '16px 20px',
    borderBottom: '1px solid #334155',
  },
  sectionTitle: {
    margin: '0 0 12px 0',
    fontSize: '14px',
    fontWeight: 600,
    color: '#cbd5e1',
  },
  distribution: {
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
  },
  distributionBar: {
    display: 'flex',
    height: '24px',
    borderRadius: '4px',
    overflow: 'hidden',
    backgroundColor: '#334155',
  },
  distSegment: {
    height: '100%',
    transition: 'width 0.3s ease',
  },
  legend: {
    display: 'flex',
    gap: '16px',
    fontSize: '12px',
    color: '#94a3b8',
    flexWrap: 'wrap',
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
  portGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(100px, 1fr))',
    gap: '8px',
  },
  portCell: {
    padding: '12px',
    borderRadius: '6px',
    border: '1px solid',
    textAlign: 'center',
  },
  portNumber: {
    fontSize: '18px',
    fontWeight: 700,
    color: '#f1f5f9',
  },
  portCount: {
    fontSize: '11px',
    color: '#cbd5e1',
  },
  servicesList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
  },
  serviceItem: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '10px 12px',
    backgroundColor: '#0f172a',
    borderRadius: '6px',
    fontSize: '13px',
  },
  serviceHost: {
    fontFamily: 'monospace',
    color: '#f1f5f9',
    flex: 1,
    overflow: 'hidden',
    textOverflow: 'ellipsis',
  },
  serviceTech: {
    color: '#94a3b8',
    marginLeft: '12px',
    fontSize: '12px',
  },
  serviceStatus: {
    padding: '2px 8px',
    borderRadius: '4px',
    fontSize: '11px',
    fontWeight: 600,
    marginLeft: '12px',
  },
};

export default AttackSurfaceMap;
