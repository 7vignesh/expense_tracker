import { useState } from "react";
import type { Category, Expense } from "../types";
import { expensesApi } from "../api";
import { formatApiError } from "../types";

interface Props {
  expenses: Expense[];
  categories: Category[];
  onFiltersChanged: (filters: { category_id?: number; date_from?: string; date_to?: string }) => void;
  onDeleted: () => void;
}

export function ExpenseList({ expenses, categories, onFiltersChanged, onDeleted }: Props) {
  const [categoryId, setCategoryId] = useState<number | "">("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [error, setError] = useState<string | null>(null);

  function applyFilters() {
    onFiltersChanged({
      category_id: categoryId === "" ? undefined : Number(categoryId),
      date_from: dateFrom || undefined,
      date_to: dateTo || undefined,
    });
  }

  function clearFilters() {
    setCategoryId("");
    setDateFrom("");
    setDateTo("");
    onFiltersChanged({});
  }

  async function handleDelete(id: number) {
    if (!confirm("Delete this expense?")) return;
    setError(null);
    try {
      await expensesApi.remove(id);
      onDeleted();
    } catch (err: unknown) {
      setError(formatApiError((err as { error: string }).error));
    }
  }

  return (
    <div className="card">
      <h2>Expenses</h2>

      {/* Filters */}
      <div className="filters">
        <div>
          <label>Category</label>
          <select
            value={categoryId}
            onChange={(e) => setCategoryId(e.target.value === "" ? "" : Number(e.target.value))}
          >
            <option value="">All categories</option>
            {categories.map((c) => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
        </div>
        <div>
          <label>From</label>
          <input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} />
        </div>
        <div>
          <label>To</label>
          <input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} />
        </div>
        <button className="btn btn-primary" onClick={applyFilters}>Filter</button>
        <button className="btn btn-ghost" onClick={clearFilters}>Clear</button>
      </div>

      {error && <p className="error-msg">{error}</p>}

      {expenses.length === 0 ? (
        <p className="empty">No expenses found.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Date</th>
              <th>Description</th>
              <th>Category</th>
              <th>Amount</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {expenses.map((exp) => (
              <tr key={exp.id}>
                <td>{exp.date}</td>
                <td>{exp.description}</td>
                <td><span className="badge">{exp.category.name}</span></td>
                <td><strong>${exp.amount}</strong></td>
                <td>
                  <button
                    className="btn btn-danger"
                    style={{ padding: "4px 10px", fontSize: "0.8rem" }}
                    onClick={() => handleDelete(exp.id)}
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
