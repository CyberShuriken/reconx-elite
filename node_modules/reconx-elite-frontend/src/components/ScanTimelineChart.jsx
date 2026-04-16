import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

export default function ScanTimelineChart({ data }) {
  return (
    <div className="chart-wrap">
      <ResponsiveContainer width="100%" height={260}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
          <XAxis dataKey="idx" stroke="#93c5fd" />
          <YAxis stroke="#93c5fd" />
          <Tooltip />
          <Line type="monotone" dataKey="cumulativeMs" stroke="#a78bfa" strokeWidth={2} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
