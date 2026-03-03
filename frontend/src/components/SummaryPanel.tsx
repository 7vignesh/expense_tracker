import type { Summary } from "../types";

interface Props {
  summary: Summary;
}

export function SummaryPanel({ summary }: Props) {
  const entries = Object.entries(summary.by_category);

  return (
    <div className="card">
      <h2>Summary</h2>
      <div className="summary-grid">
        <div className="summary-card">
          <div className="label">Total Spent</div>
          <div className="value">${summary.total}</div>
        </div>
        <div className="summary-card">
          <div className="label">Categories</div>
          <div className="value">{entries.length}</div>
        </div>
      </div>
      {entries.length > 0 && (
        <table>
          <thead>
            <tr>
              <th>Category</th>
              <th>Total</th>
            </tr>
          </thead>
          <tbody>
            {entries.map(([name, total]) => (
              <tr key={name}>
                <td>{name}</td>
                <td><strong>${total}</strong></td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
