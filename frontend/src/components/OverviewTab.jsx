import { Bar, BarChart, CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

export default function OverviewTab({ summary, severityChartData, progressTimelineData }) {
  return (
    <>
      <div className="summary-grid">
        <div className="card metric">
          <h4>Subdomains</h4>
          <p>{summary.totalSubdomains}</p>
        </div>
        <div className="card metric">
          <h4>Live Hosts</h4>
          <p>{summary.liveHosts}</p>
        </div>
        <div className="card metric">
          <h4>Endpoints</h4>
          <p>{summary.endpoints}</p>
        </div>
        <div className="card metric">
          <h4>Vulnerabilities</h4>
          <p>{summary.vulnerabilities}</p>
        </div>
      </div>

      <div className="card">
        <h3>Vulnerabilities by Severity</h3>
        <div className="chart-wrap">
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={severityChartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
              <XAxis dataKey="severity" stroke="#93c5fd" />
              <YAxis stroke="#93c5fd" />
              <Tooltip />
              <Bar dataKey="count" fill="#22d3ee" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="card">
        <h3>Scan Progress Timeline</h3>
        <div className="chart-wrap">
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={progressTimelineData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
              <XAxis dataKey="idx" stroke="#93c5fd" />
              <YAxis stroke="#93c5fd" />
              <Tooltip />
              <Line type="monotone" dataKey="cumulativeMs" stroke="#a78bfa" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </>
  );
}
