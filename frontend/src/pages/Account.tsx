import { startTransition, useState, type FormEvent } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { ArrowRight, Check, ShieldCheck } from "lucide-react";
import { api } from "../api";
import { Brand, ErrorBox, PageHeading, useAuth } from "../shared";

export function AuthPage({ mode }: { mode: string }) {
  const { accept } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [error, setError] = useState<unknown>(null),
    [busy, setBusy] = useState(false),
    [message, setMessage] = useState(""),
    [link, setLink] = useState("");
  const signup = mode === "signup",
    login = mode === "login",
    reset = mode === "reset-password",
    verify = mode === "verify-email";
  const title = signup
    ? "Your next chapter starts here."
    : login
      ? "Welcome back."
      : reset
        ? "A fresh start."
        : verify
          ? "Verify your email."
          : "Forgot your password?";
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    const fields = new FormData(event.currentTarget);
    try {
      const result = await api(
        "/auth/" + mode,
        "POST",
        verify || reset
          ? {
              token: new URLSearchParams(location.search).get("token") || "",
              password: fields.get("password") || "",
            }
          : signup || login
            ? {
                full_name: fields.get("full_name"),
                email: fields.get("email"),
                password: fields.get("password"),
                remember: fields.get("remember") === "on",
              }
            : { email: fields.get("email") },
      );
      if (signup || login) {
        accept(result);
        navigate(signup ? "/onboarding" : location.state?.from || "/dashboard");
      } else {
        setMessage(result.message);
        setLink(result.development_link || "");
      }
    } catch (e) {
      setError(e);
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="auth-page">
      <div className="auth-story">
        <Brand />
        <div>
          <div className="eyebrow">AMBITION, MEET DIRECTION.</div>
          <h1>
            A better prepared you.
            <br />
            <span>One practice at a time.</span>
          </h1>
          <p>
            Company-focused mocks, thoughtful coding challenges, and a clear
            picture of your progress.
          </p>
          <div className="auth-points">
            {[
              "Find your company. Learn the pattern.",
              "Practice original, carefully written questions.",
              "Turn every attempt into your next step.",
            ].map((t) => (
              <p key={t}>
                <Check size={18} />
                {t}
              </p>
            ))}
          </div>
        </div>
        <small>
          Independent practice. Never an official company assessment.
        </small>
      </div>
      <div className="auth-form-wrap">
        <div className="auth-form">
          <span className="eyebrow">
            PREPFAANG / {signup ? "JOIN US" : "YOUR WORKSPACE"}
          </span>
          <h1>{title}</h1>
          <p>
            {signup
              ? "Create an account and make room for what’s next."
              : login
                ? "Pick up where you left off."
                : verify
                  ? "Confirm your email to complete account verification."
                  : "We’ll help you get back to your preparation."}
          </p>
          <ErrorBox error={error} />
          {typeof location.state?.securityMessage === "string" && (
            <p className="success-text" role="status">
              {location.state.securityMessage}
            </p>
          )}
          {message ? (
            <div className="success">
              <ShieldCheck />
              <p>{message}</p>
              {link && <a href={link}>Open development email link</a>}
              <Link to="/login">Back to sign in</Link>
            </div>
          ) : (
            <form onSubmit={submit}>
              {signup && (
                <label>
                  Full name
                  <input
                    name="full_name"
                    autoComplete="name"
                    required
                    minLength={2}
                    maxLength={120}
                    placeholder="Your full name"
                  />
                </label>
              )}
              {!reset && !verify && (
                <label>
                  Email address
                  <input
                    name="email"
                    type="email"
                    autoComplete="email"
                    required
                    placeholder="you@example.com"
                  />
                </label>
              )}
              {(signup || login || reset) && (
                <label>
                  {reset ? "New password" : "Password"}
                  <input
                    name="password"
                    type="password"
                    minLength={10}
                    maxLength={128}
                    required
                    autoComplete={login ? "current-password" : "new-password"}
                    placeholder="At least 10 characters"
                  />
                </label>
              )}
              {(signup || login) && (
                <div className="form-row">
                  <label className="check-label">
                    <input name="remember" type="checkbox" defaultChecked />
                    Remember me
                  </label>
                  {login && <Link to="/forgot-password">Forgot password?</Link>}
                </div>
              )}
              <button className="btn full" disabled={busy}>
                {busy
                  ? "Please wait…"
                  : signup
                    ? "Create account"
                    : login
                      ? "Sign in"
                      : reset
                        ? "Reset password"
                        : verify
                          ? "Verify email"
                          : "Send reset link"}
                <ArrowRight size={18} />
              </button>
            </form>
          )}
          <div className="auth-switch">
            {signup ? (
              <>
                Already have an account? <Link to="/login">Sign in</Link>
              </>
            ) : login ? (
              <>
                New to PrepFaang? <Link to="/signup">Create an account</Link>
              </>
            ) : (
              <Link to="/login">Return to sign in</Link>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export function Onboarding({ embedded = false }: { embedded?: boolean }) {
  const { user, refresh } = useAuth();
  const nav = useNavigate();
  const [error, setError] = useState<unknown>(null),
    [busy, setBusy] = useState(false),
    [saved, setSaved] = useState(false);
  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    const f = Object.fromEntries(new FormData(e.currentTarget));
    try {
      await api("/users/profile", "PUT", {
        ...f,
        target_companies: String(f.target_companies || "")
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean),
        target_roles: String(f.target_roles || "")
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean),
        onboarding_complete: true,
      });
      await refresh();
      if (!embedded) nav("/dashboard");
      else setSaved(true);
    } catch (e) {
      setError(e);
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className={embedded ? "" : "onboarding"}>
      {!embedded && <Brand />}
      <PageHeading
        eyebrow="YOUR PREPARATION, PERSONALIZED"
        title={embedded ? "Your profile" : "Let’s make this yours."}
        text="Tell us a little about your goals. Everything except your name is optional."
      />
      <form className="panel profile-form" onSubmit={submit}>
        <ErrorBox error={error} />
        <div className="form-grid">
          {[
            ["full_name", "Full name"],
            ["college", "College"],
            ["graduation_year", "Graduation year"],
            ["degree", "Degree"],
            ["branch", "Branch"],
          ].map(([key, label]) => (
            <label key={key}>
              {label}
              <input
                name={key}
                defaultValue={
                  key === "full_name"
                    ? user?.full_name
                    : user?.profile[key] || ""
                }
                required={key === "full_name"}
                maxLength={key === "graduation_year" ? 4 : 120}
              />
            </label>
          ))}
          <label>
            Experience level
            <select
              name="experience_level"
              defaultValue={user?.profile.experience_level || "Student"}
            >
              <option>Student</option>
              <option>Graduate</option>
              <option>Early career</option>
              <option>Experienced</option>
            </select>
          </label>
          <label>
            Target companies
            <input
              name="target_companies"
              placeholder="Google, TCS, Adobe"
              defaultValue={user?.profile.target_companies?.join(", ") || ""}
            />
            <small>Separate names with commas.</small>
          </label>
          <label>
            Target roles
            <input
              name="target_roles"
              placeholder="Software Engineer, Analyst"
              defaultValue={user?.profile.target_roles?.join(", ") || ""}
            />
          </label>
        </div>
        <div className="actions">
          <button className="btn" disabled={busy}>
            {busy
              ? "Saving…"
              : embedded
                ? "Save profile"
                : "Build my workspace"}
            <ArrowRight size={17} />
          </button>
          {!embedded && (
            <Link to="/dashboard" className="btn secondary">
              Skip for now
            </Link>
          )}
          {saved && (
            <span className="success-text" role="status">
              Profile saved.
            </span>
          )}
        </div>
      </form>
    </div>
  );
}

export function SettingsPage() {
  const { user, refresh, accept } = useAuth();
  const navigate = useNavigate();
  const [securityBusy, setSecurityBusy] = useState(false);
  const [securityError, setSecurityError] = useState<unknown>(null);
  const [theme, setTheme] = useState(
    localStorage.getItem("prepforge-theme") || "system",
  );
  const [message, setMessage] = useState(""),
    [link, setLink] = useState(""),
    [error, setError] = useState<unknown>(null);
  function change(value: string) {
    setTheme(value);
    localStorage.setItem("prepforge-theme", value);
    document.documentElement.dataset.theme =
      value === "system"
        ? matchMedia("(prefers-color-scheme: dark)").matches
          ? "dark"
          : "light"
        : value;
  }
  async function verify() {
    try {
      const d = await api("/auth/send-verification", "POST");
      setMessage(d.message);
      setLink(d.development_link || "");
      await refresh();
    } catch (e) {
      setError(e);
    }
  }
  async function secureAction(path: string, body?: unknown) {
    setSecurityBusy(true);
    setSecurityError(null);
    try {
      const result = await api(path, "POST", body);
      // Update auth and route at the same priority so the protected-route guard
      // does not replace the sign-in navigation and discard its confirmation.
      startTransition(() => {
        accept({ user: null, csrf: "" });
        navigate("/login", {
          replace: true,
          state: { securityMessage: result.message },
        });
      });
    } catch (e) {
      setSecurityError(e);
    } finally {
      setSecurityBusy(false);
    }
  }
  function updatePassword(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    if (data.get("new_password") !== data.get("confirm_password")) {
      setSecurityError(new Error("The new passwords do not match."));
      return;
    }
    void secureAction("/auth/change-password", {
      current_password: data.get("current_password"),
      new_password: data.get("new_password"),
    });
  }
  return (
    <>
      <PageHeading
        eyebrow="MAKE YOURSELF AT HOME"
        title="Settings"
        text="A workspace that feels right for you."
      />
      <div className="panel settings-panel">
        <h2>Appearance</h2>
        <p>Choose your preferred workspace theme.</p>
        <div className="segmented">
          {["light", "dark", "system"].map((t) => (
            <button
              key={t}
              className={theme === t ? "selected" : ""}
              onClick={() => change(t)}
            >
              {t}
            </button>
          ))}
        </div>
        <hr />
        <h2>Account security</h2>
        <p>
          {user?.email} ·{" "}
          {user?.email_verified ? "Email verified" : "Email not yet verified"}
        </p>
        <ErrorBox error={error} />
        <div className="actions">
          {!user?.email_verified && (
            <button className="btn secondary" onClick={() => void verify()}>
              Send verification email
            </button>
          )}
          <Link className="btn secondary" to="/forgot-password">
            Reset password
          </Link>
        </div>
        {message && (
          <p role="status">
            {message} {link && <a href={link}>Open development email</a>}
          </p>
        )}
        <hr />
        <h2>Change your password</h2>
        <p>
          Use at least 10 characters. Changing your password signs you out on
          every device and invalidates old reset links.
        </p>
        <ErrorBox error={securityError} />
        <form className="settings-security-form" onSubmit={updatePassword}>
          <label>
            Current password
            <input
              name="current_password"
              type="password"
              autoComplete="current-password"
              required
              maxLength={128}
            />
          </label>
          <label>
            New password
            <input
              name="new_password"
              type="password"
              autoComplete="new-password"
              required
              minLength={10}
              maxLength={128}
            />
          </label>
          <label>
            Confirm new password
            <input
              name="confirm_password"
              type="password"
              autoComplete="new-password"
              required
              minLength={10}
              maxLength={128}
            />
          </label>
          <button className="btn" disabled={securityBusy}>
            {securityBusy ? "Updating security…" : "Change password"}
          </button>
        </form>
        <hr />
        <h2>Signed-in devices</h2>
        <p>
          End all active sessions, including this device. You can sign in again
          with your password.
        </p>
        <button
          className="btn secondary"
          disabled={securityBusy}
          onClick={() => void secureAction("/auth/logout-all")}
        >
          Sign out everywhere
        </button>
        <hr />
        <h2>Your privacy</h2>
        <p>
          Your attempts, code, bookmarks and analytics are visible only to your
          account and authorized administrators. Leaderboards are not enabled.
        </p>
      </div>
    </>
  );
}
