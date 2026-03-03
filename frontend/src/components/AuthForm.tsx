import { useState } from "react";
import { authApi } from "../api";
import { formatApiError } from "../types";

type Mode = "login" | "register";

interface Props {
  onAuthenticated: () => void;
}

export function AuthForm({ onAuthenticated }: Props) {
  const [mode, setMode] = useState<Mode>("login");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSuccessMsg(null);
    setLoading(true);

    try {
      if (mode === "register") {
        await authApi.register(username.trim(), password);
        // Auto-login after registration
        await authApi.login(username.trim(), password);
      } else {
        await authApi.login(username.trim(), password);
      }
      onAuthenticated();
    } catch (err: unknown) {
      setError(formatApiError((err as { error: string }).error));
    } finally {
      setLoading(false);
    }
  }

  function toggleMode() {
    setMode(m => (m === "login" ? "register" : "login"));
    setError(null);
    setSuccessMsg(null);
  }

  return (
    <div className="auth-overlay">
      <div className="auth-card">
        <div className="auth-logo">💸</div>
        <h1 className="auth-title">Expense Tracker</h1>
        <p className="auth-subtitle">
          {mode === "login" ? "Welcome back — sign in to continue" : "Create your account"}
        </p>

        <div className="auth-tabs">
          <button
            className={`auth-tab${mode === "login" ? " active" : ""}`}
            onClick={() => { setMode("login"); setError(null); }}
            type="button"
          >
            Sign In
          </button>
          <button
            className={`auth-tab${mode === "register" ? " active" : ""}`}
            onClick={() => { setMode("register"); setError(null); }}
            type="button"
          >
            Register
          </button>
        </div>

        <form onSubmit={handleSubmit} style={{ marginTop: 20 }}>
          <label htmlFor="auth-user">Username</label>
          <input
            id="auth-user"
            value={username}
            onChange={e => setUsername(e.target.value)}
            placeholder="e.g. alice"
            autoComplete="username"
            required
            minLength={3}
            maxLength={80}
          />

          <label htmlFor="auth-pass">Password</label>
          <input
            id="auth-pass"
            type="password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            placeholder={mode === "register" ? "At least 8 characters" : "Your password"}
            autoComplete={mode === "register" ? "new-password" : "current-password"}
            required
            minLength={mode === "register" ? 8 : 1}
          />

          {error && <p className="error-msg">{error}</p>}
          {successMsg && <p style={{ color: "var(--success)", fontSize: "0.85rem", marginTop: 6 }}>{successMsg}</p>}

          <button
            type="submit"
            className="btn btn-primary"
            style={{ width: "100%", marginTop: 8, padding: "11px" }}
            disabled={loading || !username.trim() || !password}
          >
            {loading ? "Please wait…" : mode === "login" ? "Sign In" : "Create Account"}
          </button>
        </form>

        <p className="auth-switch">
          {mode === "login" ? "Don't have an account?" : "Already have an account?"}{" "}
          <button type="button" className="auth-switch-btn" onClick={toggleMode}>
            {mode === "login" ? "Register" : "Sign In"}
          </button>
        </p>
      </div>
    </div>
  );
}
