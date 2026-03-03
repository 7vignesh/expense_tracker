import { useState } from "react";
import type { Category } from "../types";
import { expensesApi } from "../api";
import { formatApiError } from "../types";

interface Props {
  categories: Category[];
  onCreated: () => void;
}

const today = () => new Date().toISOString().slice(0, 10);

export function ExpenseForm({ categories, onCreated }: Props) {
  const [description, setDescription] = useState("");
  const [amount, setAmount] = useState("");
  const [date, setDate] = useState(today());
  const [categoryId, setCategoryId] = useState<number | "">("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!description.trim() || !amount || !date || categoryId === "") return;
    setError(null);
    setLoading(true);
    try {
      await expensesApi.create({
        description: description.trim(),
        amount,
        date,
        category_id: Number(categoryId),
      });
      setDescription("");
      setAmount("");
      setDate(today());
      setCategoryId("");
      onCreated();
    } catch (err: unknown) {
      setError(formatApiError((err as { error: string }).error));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="card">
      <h2>Add Expense</h2>
      <form onSubmit={handleSubmit}>
        <div className="row">
          <div className="col">
            <label htmlFor="desc">Description</label>
            <input
              id="desc"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="e.g. Lunch at Chipotle"
              maxLength={255}
              required
            />
          </div>
          <div className="col">
            <label htmlFor="amount">Amount ($)</label>
            <input
              id="amount"
              type="number"
              step="0.01"
              min="0.01"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              placeholder="0.00"
              required
            />
          </div>
        </div>
        <div className="row">
          <div className="col">
            <label htmlFor="date">Date</label>
            <input
              id="date"
              type="date"
              value={date}
              max={today()}
              onChange={(e) => setDate(e.target.value)}
              required
            />
          </div>
          <div className="col">
            <label htmlFor="cat">Category</label>
            <select
              id="cat"
              value={categoryId}
              onChange={(e) => setCategoryId(e.target.value === "" ? "" : Number(e.target.value))}
              required
            >
              <option value="">Select category…</option>
              {categories.map((c) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          </div>
        </div>
        {error && <p className="error-msg">{error}</p>}
        <button
          type="submit"
          className="btn btn-primary"
          disabled={loading || !description.trim() || !amount || !date || categoryId === ""}
        >
          {loading ? "Saving…" : "Add Expense"}
        </button>
      </form>
    </div>
  );
}
