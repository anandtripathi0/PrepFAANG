import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import {
  Link,
  Navigate,
  NavLink,
  Outlet,
  useLocation,
  useNavigate,
} from "react-router-dom";
import {
  ArrowUpRight,
  BarChart3,
  BookOpen,
  Bookmark,
  Building2,
  Code2,
  LayoutDashboard,
  GraduationCap,
  LogOut,
  Settings,
  Shield,
  Sparkles,
  History,
  ChevronRight,
  Menu,
  X,
} from "lucide-react";
import { api, setCsrf } from "./api";
import { MotionToggle } from "./components/Motion";

export type User = {
  id: string;
  full_name: string;
  email: string;
  role: string;
  email_verified: boolean;
  profile: Record<string, any>;
};
type AuthState = {
  user: User | null;
  loading: boolean;
  refresh: () => Promise<void>;
  accept: (data: any) => void;
  logout: () => Promise<void>;
};
const Auth = createContext<AuthState>(null!);
export const useAuth = () => useContext(Auth);
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null),
    [loading, setLoading] = useState(true);
  function accept(data: any) {
    setUser(data.user);
    setCsrf(data.csrf);
  }
  async function refresh() {
    try {
      accept(await api("/auth/me"));
    } catch {
      setUser(null);
    } finally {
      setLoading(false);
    }
  }
  useEffect(() => {
    void refresh();
  }, []);
  async function logout() {
    await api("/auth/logout", "POST");
    setUser(null);
    setCsrf("");
  }
  return (
    <Auth.Provider value={{ user, loading, refresh, accept, logout }}>
      {children}
    </Auth.Provider>
  );
}
export function Protected({ admin = false }: { admin?: boolean }) {
  const { user, loading } = useAuth();
  const location = useLocation();
  if (loading) return <Loading />;
  if (!user)
    return <Navigate to="/login" state={{ from: location.pathname }} replace />;
  if (admin && user.role !== "admin")
    return (
      <Empty
        title="Administrator access required"
        text="Your account does not have access to this page."
      />
    );
  return <Outlet />;
}
export function Brand() {
  return (
    <Link to="/" className="brand">
      <img src="/logo.svg" className="brand-logo" alt="" />
      PrepFaang
    </Link>
  );
}
const navigation = [
  ["/learn", "Learning library", GraduationCap],
  ["/dashboard", "Overview", LayoutDashboard],
  ["/companies", "Company explorer", Building2],
  ["/practice", "Topic practice", BookOpen],
  ["/coding", "Coding challenges", Code2],
  ["/analytics", "Analytics", BarChart3],
  ["/history", "Test history", History],
  ["/bookmarks", "Saved questions", Bookmark],
] as const;
export function Shell() {
  const { user, logout } = useAuth();
  const nav = useNavigate();
  const [open, setOpen] = useState(false);
  const location = useLocation();
  useEffect(() => setOpen(false), [location.pathname]);
  return (
    <div className="app-shell">
      <aside className={"sidebar " + (open ? "is-open" : "")}>
        <Brand />
        <div className="nav-label">YOUR WORKSPACE</div>
        <nav>
          {navigation.map(([href, label, Icon]) => (
            <NavLink key={href} to={href}>
              <Icon size={19} />
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="practice-note">
            <Sparkles size={18} />
            <strong>
              A little practice.
              <br />A lot of possibility.
            </strong>
            <p>Make your next opportunity count.</p>
            <Link to="/practice">
              Find your focus <ArrowUpRight size={16} />
            </Link>
          </div>
          {user?.role === "admin" && (
            <NavLink to="/admin">
              <Shield size={18} />
              Administration
            </NavLink>
          )}
          <NavLink to="/settings">
            <Settings size={18} />
            Settings
          </NavLink>
          <button
            className="quiet"
            onClick={() => void logout().then(() => nav("/login"))}
          >
            <LogOut size={18} />
            Sign out
          </button>
        </div>
      </aside>
      <div className="main-shell">
        <header className="topbar">
          <button
            className="icon mobile-menu"
            aria-label="Toggle navigation"
            onClick={() => setOpen(!open)}
          >
            {open ? <X /> : <Menu />}
          </button>
          <span className="breadcrumb">
            Workspace <ChevronRight size={14} />{" "}
            {navigation.find(([p]) => location.pathname.startsWith(p))?.[1] ||
              "Preparation"}
          </span>
          <div className="topbar-right">
            <MotionToggle />
            <span className="independent">
              Independent practice. Real progress.
            </span>
            <Link to="/profile" className="avatar" aria-label="Your profile">
              {user?.full_name
                .split(" ")
                .map((s) => s[0])
                .slice(0, 2)
                .join("")}
            </Link>
          </div>
        </header>
        <main className="workspace">
          <Outlet />
        </main>
        <footer>
          Made for your next chapter.{" "}
          <span>
            Practice assessments are independently created for preparation and
            are not official tests of the respective companies.
          </span>
        </footer>
      </div>
    </div>
  );
}
export function PageHeading({
  eyebrow,
  title,
  text,
  action,
}: {
  eyebrow?: string;
  title: string;
  text?: string;
  action?: ReactNode;
}) {
  return (
    <div className="page-heading">
      <div>
        {eyebrow && <div className="eyebrow">{eyebrow}</div>}
        <h1>{title}</h1>
        {text && <p>{text}</p>}
      </div>
      {action}
    </div>
  );
}
export function Loading() {
  return (
    <div className="empty" role="status">
      <span className="loading-brand" aria-hidden="true">
        <span className="spinner" />
        <img src="/logo.svg" alt="" />
      </span>
      Loading your workspace…
    </div>
  );
}
export function ErrorBox({ error }: { error: unknown }) {
  return error ? (
    <div className="error" role="alert">
      {error instanceof Error ? error.message : String(error)}
    </div>
  ) : null;
}
export function Empty({
  title,
  text,
  action,
}: {
  title: string;
  text?: string;
  action?: ReactNode;
}) {
  return (
    <div className="empty">
      <div className="empty-icon">
        <Sparkles size={25} />
      </div>
      <h2>{title}</h2>
      {text && <p>{text}</p>}
      {action}
    </div>
  );
}
export function useData<T = any>(path: string) {
  const [data, setData] = useState<T | null>(null),
    [error, setError] = useState<unknown>(null);
  const [tick, setTick] = useState(0);
  useEffect(() => {
    let alive = true;
    setData(null);
    setError(null);
    api<T>(path)
      .then((d) => {
        if (alive) setData(d);
      })
      .catch((e) => {
        if (alive) setError(e);
      });
    return () => {
      alive = false;
    };
  }, [path, tick]);
  return { data, error, reload: () => setTick((t) => t + 1) };
}
export function Badge({
  children,
  kind = "",
}: {
  children: ReactNode;
  kind?: string;
}) {
  return <span className={"badge " + kind}>{children}</span>;
}
export function CompanyMark({ name, logo }: { name: string; logo?: string }) {
  return (
    <span className={"company-mark mark-" + name.toLowerCase()}>
      {logo && /^https?:\/\//.test(logo) ? (
        <img
          className="company-logo"
          src={logo}
          alt={name}
          referrerPolicy="no-referrer"
        />
      ) : name === "Microsoft" ? (
        <span className="ms-grid">
          <i />
          <i />
          <i />
          <i />
        </span>
      ) : name === "Amazon" ? (
        "a"
      ) : name === "Google" ? (
        "G"
      ) : name === "Meta" ? (
        "∞"
      ) : name === "Apple" ? (
        "A"
      ) : name === "TCS" ? (
        "tcs"
      ) : (
        name.slice(0, 2)
      )}
    </span>
  );
}
