import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { Code2, Pause, Play, Target, TrendingUp } from "lucide-react";

const preferenceKey = "prepfaang-motion";
const reducedMotionQuery = "(prefers-reduced-motion: reduce)";
const Motion = createContext({
  enabled: true,
  reducedMotion: false,
  setEnabled: (_enabled: boolean) => {},
});

function readPreference() {
  try {
    return localStorage.getItem(preferenceKey) !== "paused";
  } catch {
    return true;
  }
}

export function MotionProvider({ children }: { children: ReactNode }) {
  const [preference, setPreference] = useState(readPreference);
  const [reducedMotion, setReducedMotion] = useState(
    () => matchMedia(reducedMotionQuery).matches,
  );
  const [visible, setVisible] = useState(() => !document.hidden);
  const enabled = preference && !reducedMotion;

  useEffect(() => {
    const query = matchMedia(reducedMotionQuery);
    const onPreference = () => setReducedMotion(query.matches);
    const onVisibility = () => setVisible(!document.hidden);
    query.addEventListener("change", onPreference);
    document.addEventListener("visibilitychange", onVisibility);
    return () => {
      query.removeEventListener("change", onPreference);
      document.removeEventListener("visibilitychange", onVisibility);
    };
  }, []);

  useEffect(() => {
    document.documentElement.dataset.motion =
      enabled && visible ? "running" : "paused";
  }, [enabled, visible]);

  function setEnabled(value: boolean) {
    setPreference(value);
    try {
      localStorage.setItem(preferenceKey, value ? "enabled" : "paused");
    } catch {
      // The control still works when browser storage is unavailable.
    }
  }

  return (
    <Motion.Provider value={{ enabled, reducedMotion, setEnabled }}>
      {children}
    </Motion.Provider>
  );
}

export const useMotion = () => useContext(Motion);

export function MotionToggle() {
  const { enabled, reducedMotion, setEnabled } = useMotion();
  const label = reducedMotion
    ? "Reduced motion enabled by your device"
    : enabled
      ? "Pause animations"
      : "Enable animations";
  return (
    <button
      type="button"
      className="quiet motion-control"
      onClick={() => setEnabled(!enabled)}
      disabled={reducedMotion}
      aria-label={label}
      title={label}
    >
      {enabled ? (
        <Pause size={14} aria-hidden />
      ) : (
        <Play size={14} aria-hidden />
      )}
      <span>{reducedMotion ? "Reduced motion" : label}</span>
    </button>
  );
}

export function HeroAtmosphere() {
  return (
    <div className="hero-atmosphere" aria-hidden="true">
      <span className="hero-glow hero-glow-one" />
      <span className="hero-glow hero-glow-two" />
      <span className="hero-orbit hero-orbit-one" />
      <span className="hero-orbit hero-orbit-two" />
      <span className="hero-tile hero-tile-code">
        <Code2 strokeWidth={1.25} />
      </span>
      <span className="hero-tile hero-tile-target">
        <Target strokeWidth={1.25} />
      </span>
      <span className="hero-tile hero-tile-progress">
        <TrendingUp strokeWidth={1.25} />
      </span>
    </div>
  );
}
