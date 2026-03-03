import { useState } from "react";
import type { Category } from "../types";
import { categoriesApi } from "../api";
import { formatApiError } from "../types";

interface Props {
  categories: Category[];
  onChanged: () => void;
}

export function CategoryManager({ categories, onChanged }: Props) {
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    setError(null);
    setLoading(true);
    try {
      await categoriesApi.create(name.trim());
      setName("");
      onChanged();
    } catch (err: unknown) {
      setError(formatApiError((err as { error: string }).error));
    } finally {
      setLoading(false);
    }
  }

  async function handleDelete(id: number, catName: string) {
    if (!confirm(`Delete category "${catName}"?`)) return;
    setError(null);
    try {
      await categoriesApi.remove(id);
      onChanged();
    } catch (err: unknown) {
      setError(formatApiError((err as { error: string }).error));
    }
  }

  return (
    <div className="card">
      <h2>Categories</h2>
      <form onSubmit={handleAdd} style={{ display: "flex", gap: 8, marginBottom: 14 }}>
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="New category name"
          style={{ marginBottom: 0, flex: 1 }}
          maxLength={100}
        />
        <button type="submit" className="btn btn-primary" disabled={loading || !name.trim()}>
          Add
        </button>
      </form>
      {error && <p className="error-msg">{error}</p>}
      <div className="tag-list">
        {categories.length === 0 && (
          <span style={{ color: "var(--muted)", fontSize: "0.85rem" }}>No categories yet.</span>
        )}
        {categories.map((cat) => (
          <span key={cat.id} className="tag">
            {cat.name}
            <button onClick={() => handleDelete(cat.id, cat.name)} title="Delete">×</button>
          </span>
        ))}
      </div>
    </div>
  );
}
