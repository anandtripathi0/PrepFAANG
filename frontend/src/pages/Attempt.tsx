import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  Bookmark,
  Check,
  ChevronLeft,
  ChevronRight,
  Clock3,
  Flag,
  Maximize,
  ShieldCheck,
} from "lucide-react";
import { api, clock } from "../api";
import { Badge, ErrorBox, Loading } from "../shared";
import { CodeEditor, ProblemStatement } from "../components/CodeEditor";

export default function AttemptPage() {
  const { id } = useParams();
  const nav = useNavigate();
  const [attempt, setAttempt] = useState<any>(null),
    [index, setIndex] = useState(0),
    [remaining, setRemaining] = useState(0),
    [error, setError] = useState<unknown>(null),
    [saveState, setSaveState] = useState("All changes saved"),
    [confirmOpen, setConfirmOpen] = useState(false),
    [submitting, setSubmitting] = useState(false),
    [warning, setWarning] = useState("");
  const current = useRef<any>(null),
    queue = useRef(new Map<string, any>()),
    saving = useRef(false),
    anchor = useRef({ at: 0, remaining: 0 }),
    start = useRef(performance.now()),
    finished = useRef(false),
    retry = useRef<ReturnType<typeof setTimeout> | null>(null);
  const flush = useCallback(async () => {
    if (saving.current) {
      while (saving.current) await new Promise((r) => setTimeout(r, 30));
    }
    if (!queue.current.size) return;
    saving.current = true;
    setSaveState("Saving…");
    try {
      for (const [aqId, data] of queue.current) {
        await api(`/attempts/${id}/answers/${aqId}`, "PUT", data);
        if (queue.current.get(aqId) === data) queue.current.delete(aqId);
        localStorage.setItem(
          "prepforge-pending-" + id,
          JSON.stringify([...queue.current]),
        );
      }
      setSaveState(queue.current.size ? "Saving…" : "All changes saved");
    } catch (e) {
      setSaveState("Connection interrupted · retrying");
      throw e;
    } finally {
      saving.current = false;
    }
  }, [id]);
  useEffect(() => {
    let live = true;
    api("/attempts/" + id)
      .then((d) => {
        if (!live) return;
        if (d.status !== "active") {
          finished.current = true;
          nav(`/attempt/${id}/result`, { replace: true });
          return;
        }
        try {
          const pending = JSON.parse(
            localStorage.getItem("prepforge-pending-" + id) || "[]",
          );
          for (const [key, value] of pending) {
            const q = d.questions.find((q: any) => q.id === key);
            if (q) {
              q.answer = { ...q.answer, ...value };
              queue.current.set(key, value);
            }
          }
          if (queue.current.size) setSaveState("Restoring unsaved changes…");
        } catch {
          setWarning(
            "Local recovery storage is unavailable. Keep this tab open until all changes save.",
          );
        }
        current.current = d;
        setAttempt(d);
        setIndex(d.current_position);
        anchor.current = {
          at: performance.now(),
          remaining: d.expires_at - d.server_now,
        };
        setRemaining(anchor.current.remaining);
      })
      .catch(setError);
    return () => {
      live = false;
    };
  }, [id, nav]);
  useEffect(() => {
    const interval = setInterval(() => {
      if (!current.current) return;
      setRemaining(
        Math.max(
          0,
          anchor.current.remaining -
            (performance.now() - anchor.current.at) / 1000,
        ),
      );
      if (queue.current.size && !saving.current) void flush().catch(() => {});
    }, 1000);
    const sync = setInterval(() => {
      if (current.current && !finished.current)
        void api("/attempts/" + id)
          .then((d) => {
            if (d.status !== "active") {
              finished.current = true;
              nav(`/attempt/${id}/result`, { replace: true });
            } else
              anchor.current = {
                at: performance.now(),
                remaining: d.expires_at - d.server_now,
              };
          })
          .catch(() => {});
    }, 15000);
    return () => {
      clearInterval(interval);
      clearInterval(sync);
      if (retry.current) clearTimeout(retry.current);
    };
  }, [id, nav, flush]);
  useEffect(() => {
    if (!confirmOpen) return;
    function keys(e: KeyboardEvent) {
      if (e.key === "Escape" && !submitting) setConfirmOpen(false);
      if (e.key === "Tab") {
        const buttons = Array.from(
          document.querySelectorAll<HTMLButtonElement>(
            ".modal button:not(:disabled)",
          ),
        );
        if (!buttons.length) return;
        const first = buttons[0],
          last = buttons[buttons.length - 1];
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    }
    document.addEventListener("keydown", keys);
    return () => document.removeEventListener("keydown", keys);
  }, [confirmOpen, submitting]);
  useEffect(() => {
    function leave(e: BeforeUnloadEvent) {
      if (!finished.current) {
        e.preventDefault();
        e.returnValue = "";
      }
    }
    function integrity(kind: string) {
      if (!current.current || finished.current) return;
      setWarning("Leaving the assessment window may be recorded.");
      void api(`/attempts/${id}/events`, "POST", { kind }).catch(() => {});
    }
    function visibility() {
      if (document.hidden) integrity("TAB_SWITCH");
    }
    function blur() {
      integrity("WINDOW_BLUR");
    }
    function fullscreen() {
      if (!document.fullscreenElement) integrity("FULLSCREEN_EXIT");
    }
    window.addEventListener("beforeunload", leave);
    document.addEventListener("visibilitychange", visibility);
    window.addEventListener("blur", blur);
    document.addEventListener("fullscreenchange", fullscreen);
    return () => {
      window.removeEventListener("beforeunload", leave);
      document.removeEventListener("visibilitychange", visibility);
      window.removeEventListener("blur", blur);
      document.removeEventListener("fullscreenchange", fullscreen);
    };
  }, [id]);
  async function submit(expired = false) {
    if (finished.current) return;
    setSubmitting(true);
    setError(null);
    try {
      if (!expired) await flush();
      const r = await api(`/attempts/${id}/submit`, "POST");
      finished.current = true;
      localStorage.removeItem("prepforge-pending-" + id);
      if (document.fullscreenElement)
        await document.exitFullscreen().catch(() => {});
      nav(`/attempt/${r.id}/result`, { replace: true });
    } catch (e) {
      setError(e);
      setSubmitting(false);
    }
  }
  useEffect(() => {
    if (attempt && remaining <= 0 && !finished.current && !submitting)
      void submit(true);
  }, [remaining, attempt, submitting]);
  function update(patch: any) {
    const d = current.current;
    if (!d) return;
    const q = d.questions[index];
    const answer = {
      ...q.answer,
      ...patch,
      ...("code" in patch || "language" in patch ? { code_result: null } : {}),
      visited: true,
      time_spent:
        q.answer.time_spent + (performance.now() - start.current) / 1000,
    };
    start.current = performance.now();
    const next = {
      ...d,
      questions: d.questions.map((a: any, i: number) =>
        i === index ? { ...a, answer } : a,
      ),
    };
    current.current = next;
    setAttempt(next);
    const { selected, code, language, marked, visited, time_spent } = answer;
    queue.current.set(q.id, {
      selected,
      code,
      language,
      marked,
      visited,
      time_spent,
    });
    try {
      localStorage.setItem(
        "prepforge-pending-" + id,
        JSON.stringify([...queue.current]),
      );
    } catch {
      setWarning(
        "Local recovery storage is unavailable. Keep this tab open until all changes save.",
      );
    }
    setSaveState("Saving…");
    if (retry.current) clearTimeout(retry.current);
    retry.current = setTimeout(() => void flush().catch(() => {}), 400);
  }
  async function go(to: number) {
    update({});
    try {
      await flush();
      setIndex(to);
      start.current = performance.now();
      const next = current.current.questions[to];
      const answer = { ...next.answer, visited: true };
      current.current = {
        ...current.current,
        current_position: to,
        questions: current.current.questions.map((q: any, i: number) =>
          i === to ? { ...q, answer } : q,
        ),
      };
      setAttempt(current.current);
      const { selected, code, language, marked, visited, time_spent } = answer;
      queue.current.set(next.id, {
        selected,
        code,
        language,
        marked,
        visited,
        time_spent,
      });
      await flush();
    } catch (e) {
      setError(e);
    }
  }
  if (!attempt)
    return error ? (
      <div className="onboarding">
        <ErrorBox error={error} />
        <a href="/dashboard">Return to dashboard</a>
      </div>
    ) : (
      <Loading />
    );
  const aq = attempt.questions[index],
    q = aq.question,
    a = aq.answer;
  const answered = attempt.questions.filter((q: any) =>
    q.question.type !== "coding"
      ? q.answer.selected !== null
      : !!q.answer.code_result,
  ).length;
  const marked = attempt.questions.filter((q: any) => q.answer.marked).length;
  async function bookmark() {
    try {
      await api("/bookmarks/" + q.id, "PUT");
      setWarning("Question saved to your collection.");
    } catch (e) {
      setError(e);
    }
  }
  return (
    <div className="assessment-page">
      <header className="assessment-header">
        <div className="assessment-brand">
          <span className="brand assessment-logo">
            <img src="/logo.svg" className="brand-logo" alt="" />
            PrepFaang
          </span>
          <span>
            {attempt.snapshot.company}
            <small>
              {attempt.snapshot.track} · {attempt.difficulty}
            </small>
          </span>
        </div>
        <div className="actions">
          <button
            className="icon"
            title="Enter fullscreen"
            aria-label="Enter fullscreen"
            onClick={() =>
              void document.documentElement
                .requestFullscreen()
                .catch(() =>
                  setWarning("Fullscreen is not supported in this browser."),
                )
            }
          >
            <Maximize size={18} />
          </button>
          <div className={"timer " + (remaining < 60 ? "urgent" : "")}>
            <Clock3 size={18} />
            <strong>{clock(remaining)}</strong>
          </div>
          <button
            className="btn small"
            disabled={submitting}
            onClick={() => setConfirmOpen(true)}
          >
            Submit test
          </button>
        </div>
      </header>
      <div className="assessment-status">
        <span>
          <ShieldCheck size={15} />
          Focus mode · {answered}/{attempt.questions.length} answered
        </span>
        <span
          role="status"
          className={saveState.startsWith("Connection") ? "save-error" : ""}
        >
          {saveState === "All changes saved" && <Check size={14} />} {saveState}
        </span>
      </div>
      {warning && (
        <div className="integrity-warning" role="status">
          {warning}
          <button className="quiet" onClick={() => setWarning("")}>
            Dismiss
          </button>
        </div>
      )}
      <ErrorBox error={error} />
      <div className="assessment-layout">
        <aside className="section-sidebar">
          <div className="nav-label">SECTIONS</div>
          {attempt.snapshot.sections.map((s: any) => (
            <button
              key={s.name}
              className={aq.section === s.name ? "active" : ""}
              onClick={() =>
                void go(
                  attempt.questions.findIndex((q: any) => q.section === s.name),
                )
              }
            >
              <span>{s.name}</span>
              <small>
                {
                  attempt.questions.filter((q: any) => q.section === s.name)
                    .length
                }{" "}
                questions
              </small>
            </button>
          ))}
          <p className="small-text">
            Your time continues if you leave. Answers restore when you return.
          </p>
        </aside>
        <main className="question-main">
          <div className="question-top">
            <span>
              QUESTION {index + 1} OF {attempt.questions.length}
            </span>
            <div>
              <Badge>+{q.marks * q.weight} marks</Badge>
              <button
                className="icon"
                aria-label="Save question"
                onClick={() => void bookmark()}
              >
                <Bookmark size={17} />
              </button>
            </div>
          </div>
          {q.type !== "coding" ? (
            <>
              <Badge>{q.topic}</Badge>
              {q.type === "reflection" && (
                <div className="reflection-notice">
                  <p>
                    Work-style reflection · No correct answer · Not included in
                    your score.
                  </p>
                </div>
              )}
              <h1 className="question-text">{q.question}</h1>
              <div
                className="options"
                role="radiogroup"
                aria-label="Answer options"
              >
                {q.options.map((option: string, i: number) => (
                  <button
                    role="radio"
                    aria-checked={a.selected === i}
                    key={i}
                    className={"option " + (a.selected === i ? "checked" : "")}
                    onClick={() => update({ selected: i })}
                  >
                    <span>{String.fromCharCode(65 + i)}</span>
                    {option}
                    <i>{a.selected === i && <Check size={14} />}</i>
                  </button>
                ))}
              </div>
            </>
          ) : (
            <div className="assessment-coding">
              <ProblemStatement q={q} />
              <CodeEditor
                key={aq.id}
                q={q}
                code={a.code}
                language={a.language}
                onChange={(code) => update({ code })}
                onLanguage={(language) =>
                  update({
                    language,
                    code: q.coding.starter_code[language],
                    code_result: null,
                  })
                }
                beforeRun={flush}
                attemptId={id}
                attemptQuestionId={aq.id}
                onResult={(r) => {
                  const d = current.current;
                  const next = {
                    ...d,
                    questions: d.questions.map((x: any, i: number) =>
                      i === index
                        ? {
                            ...x,
                            answer: {
                              ...x.answer,
                              code:
                                x.answer.code ||
                                q.coding.starter_code[x.answer.language],
                              code_result: r,
                            },
                          }
                        : x,
                    ),
                  };
                  current.current = next;
                  setAttempt(next);
                }}
              />
            </div>
          )}
          <div className="question-actions">
            <div className="actions">
              <button
                className="btn secondary small"
                onClick={() => update({ selected: null })}
                disabled={q.type === "coding"}
              >
                Clear response
              </button>
              <button
                className={
                  "btn secondary small " + (a.marked ? "marked-btn" : "")
                }
                onClick={() => update({ marked: !a.marked })}
              >
                <Flag size={15} />
                {a.marked ? "Unmark" : "Mark for review"}
              </button>
            </div>
            <div className="actions">
              <button
                className="icon"
                aria-label="Previous question"
                disabled={index === 0}
                onClick={() => void go(index - 1)}
              >
                <ChevronLeft />
              </button>
              <button
                className="btn small"
                onClick={() =>
                  index < attempt.questions.length - 1
                    ? void go(index + 1)
                    : setConfirmOpen(true)
                }
              >
                {index < attempt.questions.length - 1
                  ? "Save & next"
                  : "Review & submit"}
                <ChevronRight size={16} />
              </button>
            </div>
          </div>
        </main>
        <aside className="navigator">
          <h3>Question navigator</h3>
          <div className="question-numbers">
            {attempt.questions.map((x: any, i: number) => {
              const yes =
                x.question.type !== "coding"
                  ? x.answer.selected !== null
                  : !!x.answer.code_result;
              return (
                <button
                  key={x.id}
                  aria-label={`Question ${i + 1}${yes ? ", answered" : ""}${x.answer.marked ? ", marked for review" : ""}`}
                  aria-current={index === i ? "step" : undefined}
                  className={
                    (yes ? "answered " : x.answer.visited ? "visited " : "") +
                    (x.answer.marked ? "marked " : "") +
                    (index === i ? "current" : "")
                  }
                  onClick={() => void go(i)}
                >
                  {i + 1}
                </button>
              );
            })}
          </div>
          <div className="navigator-key">
            <span>
              <i className="answered" />
              Answered
            </span>
            <span>
              <i className="visited" />
              Visited
            </span>
            <span>
              <i />
              Unvisited
            </span>
            <span>
              <i className="marked" />
              Marked for review
            </span>
            <span>
              <i className="answered marked" />
              Answered + marked
            </span>
          </div>
          <div className="test-note">
            <Clock3 size={17} />
            <p>
              Steady progress beats rushing.
              <br />
              You can revisit any question.
            </p>
          </div>
        </aside>
      </div>
      {confirmOpen && (
        <div className="modal-backdrop">
          <div
            className="modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="submit-title"
          >
            <h2 id="submit-title">Ready to submit?</h2>
            <p>Your answers will be locked and your result saved.</p>
            <div className="submit-counts">
              <span>
                <strong>{answered}</strong>Answered
              </span>
              <span>
                <strong>{attempt.questions.length - answered}</strong>Unanswered
              </span>
              <span>
                <strong>{marked}</strong>For review
              </span>
            </div>
            <p className="small-text">
              Coding receives marks only for the latest submitted code.
              Unsubmitted edits receive no coding marks.
            </p>
            <ErrorBox error={error} />
            <div className="actions">
              <button
                autoFocus
                className="btn secondary"
                disabled={submitting}
                onClick={() => setConfirmOpen(false)}
              >
                Keep working
              </button>
              <button
                className="btn"
                disabled={submitting}
                onClick={() => void submit()}
              >
                {submitting ? "Submitting…" : "Confirm submission"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
