import { useCallback, useEffect, useState } from "react";
import type { Category, Expense, Summary } from "./types";
import { categoriesApi, expensesApi, type ExpenseFilters, tokenStore, registerUnauthorizedHandler } from "./api";
import { CategoryManager } from "./components/CategoryManager";
import { ExpenseForm } from "./components/ExpenseForm";
import { ExpenseList } from "./components/ExpenseList";
import { SummaryPanel } from "./components/SummaryPanel";
import { AuthForm } from "./components/AuthForm";
import "./styles.css";

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(() => !!tokenStore.get());
  const [categories, setCategories] = useState<Category[]>([]);
  const [expenses, setExpenses] = useState<Expense[]>([]);
  const [summary, setSummary] = useState<Summary>({ total: "0.00", by_category: {} });
  const [filters, setFilters] = useState<ExpenseFilters>({});
  const [globalError, setGlobalError] = useState<string | null>(null);

  useEffect(() => {
    registerUnauthorizedHandler(() => {
      setIsAuthenticated(false);
      setCategories([]);
      setExpenses([]);
      setSummary({ total: "0.00", by_category: {} });
    });
  }, []);

  const loadCategories = useCallback(async () => {
    try {
      setCategories(await categoriesApi.list());
    } catch {
      setGlobalError("Failed to load categories.");
    }
  }, []);

  const loadExpenses = useCallback(async (f: ExpenseFilters = {}) => {
    try {
      setExpenses(await expensesApi.list(f));
    } catch {
      setGlobalError("Failed to load expenses.");
    }
  }, []);

  const loadSummary = useCallback(async () => {
    try {
      setSummary(await expensesApi.summary());
    } catch {
      setGlobalError("Failed to load summary.");
    }
  }, []);

  useEffect(() => {
    if (!isAuthenticated) return;
    void loadCategories();
    void loadExpenses();
    void loadSummary();
  }, [isAuthenticated, loadCategories, loadExpenses, loadSummary]);

  function handleFiltersChanged(f: ExpenseFilters) {
    setFilters(f);
    void loadExpenses(f);
  }

  function handleExpenseChanged() {
    void loadExpenses(filters);
    void loadSummary();
  }

  function handleLogout() {
    tokenStore.clear();
    setIsAuthenticated(false);
    setCategories([]);
    setExpenses([]);
    setSummary({ total: "0.00", by_category: {} });
    setGlobalError(null);
  }

  if (!isAuthenticated) {
    return (
      <>
        <div className="bg-scene" aria-hidden="true">
          <div className="orb orb-1" />
          <div className="orb orb-2" />
          <div className="orb orb-3" />
        </div>
        <AuthForm onAuthenticated={() => setIsAuthenticated(true)} />
      </>
    );
  }

  return (
    <div className="container">
      {/* Animated background orbs */}
      <div className="bg-scene" aria-hidden="true">
        <div className="orb orb-1" />
        <div className="orb orb-2" />
        <div className="orb orb-3" />
      </div>

      <div className="page-header">
        <div className="page-header-icon">💸</div>
        <h1>Expense Tracker</h1>
        <button
          type="button"
          className="btn btn-ghost"
          style={{ marginLeft: "auto" }}
          onClick={handleLogout}
        >
          Sign Out
        </button>
      </div>

      {globalError && (
        <p className="error-msg" style={{ marginBottom: 16 }}>{globalError}</p>
      )}
      <SummaryPanel summary={summary} />
      <div className="row">
        <div className="col">
          <CategoryManager categories={categories} onChanged={loadCategories} />
        </div>
        <div className="col">
          <ExpenseForm categories={categories} onCreated={handleExpenseChanged} />
        </div>
      </div>
      <ExpenseList
        expenses={expenses}
        categories={categories}
        onFiltersChanged={handleFiltersChanged}
        onDeleted={handleExpenseChanged}
      />
    </div>
  );
}
