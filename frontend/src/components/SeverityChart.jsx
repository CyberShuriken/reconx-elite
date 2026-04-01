import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

export default function SeverityChart({ data }) {
  return (
    <div className="chart-wrap">
      <ResponsiveContainer width="100%" height={260}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
          <XAxis dataKey="severity" stroke="#93c5fd" />
          <YAxis stroke="#93c5fd" />
          <Tooltip />
          <Bar dataKey="count" fill="#22d3ee" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
