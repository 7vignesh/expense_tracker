/**
 * Domain types shared across the frontend.
 * These mirror the backend schemas exactly — any schema change must be
 * reflected here, which makes API contract drift visible at compile time.
 */

export interface Category {
  id: number;
  name: string;
  created_at: string;
}

export interface Expense {
  id: number;
  description: string;
  /** Decimal string, e.g. "12.50" */
  amount: string;
  date: string; // ISO date: "YYYY-MM-DD"
  category: Pick<Category, "id" | "name">;
  created_at: string;
}

export interface Summary {
  total: string;
  by_category: Record<string, string>;
}

export interface ApiError {
  error: string | Record<string, string[]>;
}

/** Flatten a marshmallow error shape to a single readable string. */
export function formatApiError(err: ApiError["error"]): string {
  if (typeof err === "string") return err;
  return Object.entries(err)
    .map(([field, msgs]) => `${field}: ${msgs.join(", ")}`)
    .join(" | ");
}
