/**
 * Typed API client.
 *
 * All network calls go through this module.  Components never use `fetch`
 * directly.  This makes it trivial to:
 *   - swap the base URL
 *   - add auth headers globally
 *   - mock the entire API layer in tests
 */

import type { Category, Expense, Summary } from "../types";

const BASE = "/api";

async function request<T>(
  path: string,
  options?: RequestInit
): Promise<T> {
  const response = await fetch(`${BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });

  if (response.status === 204) {
    return undefined as unknown as T;
  }

  const data = await response.json();

  if (!response.ok) {
    // Throw with the server's error payload so callers can display it
    throw data;
  }

  return data as T;
}

// ── Categories ────────────────────────────────────────────────────────────────

export const categoriesApi = {
  list: (): Promise<Category[]> =>
    request("/categories/"),

  create: (name: string): Promise<Category> =>
    request("/categories/", {
      method: "POST",
      body: JSON.stringify({ name }),
    }),

  remove: (id: number): Promise<void> =>
    request(`/categories/${id}`, { method: "DELETE" }),
};

// ── Expenses ──────────────────────────────────────────────────────────────────

export interface ExpenseFilters {
  category_id?: number;
  date_from?: string;
  date_to?: string;
}

export const expensesApi = {
  list: (filters?: ExpenseFilters): Promise<Expense[]> => {
    const params = new URLSearchParams();
    if (filters?.category_id !== undefined)
      params.set("category_id", String(filters.category_id));
    if (filters?.date_from) params.set("date_from", filters.date_from);
    if (filters?.date_to) params.set("date_to", filters.date_to);
    const qs = params.toString() ? `?${params}` : "";
    return request(`/expenses/${qs}`);
  },

  create: (payload: {
    description: string;
    amount: string;
    date: string;
    category_id: number;
  }): Promise<Expense> =>
    request("/expenses/", { method: "POST", body: JSON.stringify(payload) }),

  remove: (id: number): Promise<void> =>
    request(`/expenses/${id}`, { method: "DELETE" }),

  summary: (): Promise<Summary> => request("/expenses/summary"),
};
