import Editor, { loader } from "@monaco-editor/react";
import * as monaco from "monaco-editor/esm/vs/editor/editor.api";
import "monaco-editor/esm/vs/basic-languages/python/python.contribution";
import "monaco-editor/esm/vs/basic-languages/cpp/cpp.contribution";
import "monaco-editor/esm/vs/basic-languages/java/java.contribution";
import "monaco-editor/esm/vs/basic-languages/javascript/javascript.contribution";
import EditorWorker from "monaco-editor/esm/vs/editor/editor.worker?worker";
import { useState } from "react";
import { Play, RotateCcw, Send } from "lucide-react";
import { api } from "../api";
import { Badge, ErrorBox } from "../shared";
(self as any).MonacoEnvironment = { getWorker: () => new EditorWorker() };
loader.config({ monaco });
const names: Record<string, string> = {
  python: "Python",
  c: "C",
  cpp: "C++",
  java: "Java",
  javascript: "JavaScript",
};
export function ProblemStatement({ q }: { q: any }) {
  return (
    <div className="problem-statement">
      <Badge kind={q.difficulty}>{q.difficulty}</Badge>
      <h2>{q.title}</h2>
      <p className="pre-wrap">{q.question}</p>
      {q.coding && (
        <>
          <h3>Input format</h3>
          <p>{q.coding.input_format}</p>
          <h3>Output format</h3>
          <p>{q.coding.output_format}</p>
          <h3>Constraints</h3>
          <p>{q.coding.constraints}</p>
          {q.coding.tests.map((t: any, i: number) => (
            <div className="example" key={i}>
              <h3>Example {i + 1}</h3>
              <div className="grid two">
                <div>
                  <small>INPUT</small>
                  <pre>{t.input}</pre>
                </div>
                <div>
                  <small>OUTPUT</small>
                  <pre>{t.output}</pre>
                </div>
              </div>
            </div>
          ))}
          <p className="small-text">
            Time limit {q.coding.time_limit}s · Memory limit{" "}
            {q.coding.memory_limit} MB
          </p>
        </>
      )}
    </div>
  );
}
export function CodeEditor({
  q,
  code,
  language,
  onChange,
  onLanguage,
  attemptId,
  attemptQuestionId,
  onResult,
  beforeRun,
}: {
  q: any;
  code: string;
  language: string;
  onChange: (v: string) => void;
  onLanguage: (v: string) => void;
  attemptId?: string;
  attemptQuestionId?: string;
  onResult?: (r: any) => void;
  beforeRun?: () => Promise<void>;
}) {
  const [busy, setBusy] = useState(""),
    [result, setResult] = useState<any>(null),
    [error, setError] = useState<unknown>(null);
  async function run(mode: string) {
    setBusy(mode);
    setError(null);
    try {
      if (beforeRun) await beforeRun();
      const r = await api("/code/evaluate", "POST", {
        question_id: q.id,
        attempt_id: attemptId,
        attempt_question_id: attemptQuestionId,
        language,
        code,
        mode,
      });
      setResult(r);
      if (mode === "submit") onResult?.(r);
    } catch (e) {
      setError(e);
    } finally {
      setBusy("");
    }
  }
  return (
    <div className="code-workspace">
      <div className="editor-toolbar">
        <label className="sr-only" htmlFor="language">
          Language
        </label>
        <select
          id="language"
          value={language}
          onChange={(e) => onLanguage(e.target.value)}
          disabled={!!busy}
        >
          {q.coding.allowed_languages.map((l: string) => (
            <option key={l} value={l}>
              {names[l]}
            </option>
          ))}
        </select>
        <button
          className="quiet"
          disabled={!!busy}
          onClick={() => {
            if (confirm("Replace your current code with starter code?"))
              onChange(q.coding.starter_code[language]);
          }}
        >
          <RotateCcw size={15} />
          Reset
        </button>
      </div>
      <Editor
        height="380px"
        language={language === "c" ? "cpp" : language}
        value={code}
        theme={
          document.documentElement.dataset.theme === "dark" ? "vs-dark" : "vs"
        }
        onChange={(v) => onChange(v || "")}
        options={{
          minimap: { enabled: false },
          fontSize: 14,
          scrollBeyondLastLine: false,
          wordWrap: "on",
          automaticLayout: true,
          tabSize: 4,
          readOnly: !!busy,
        }}
        onMount={(editor) => {
          editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter, () =>
            document.getElementById("run-code")?.click(),
          );
        }}
      />
      <div className="editor-actions">
        <span>Ctrl / ⌘ + Enter to run</span>
        <button
          id="run-code"
          className="btn secondary small"
          disabled={!!busy || !code.trim()}
          onClick={() => void run("run")}
        >
          <Play size={15} />
          {busy === "run" ? "Running…" : "Run examples"}
        </button>
        <button
          className="btn small"
          disabled={!!busy || !code.trim()}
          onClick={() => void run("submit")}
        >
          <Send size={15} />
          {busy === "submit" ? "Evaluating…" : "Submit code"}
        </button>
      </div>
      <ErrorBox error={error} />
      {result ? (
        <div
          className={
            "code-result " + (result.status === "Accepted" ? "accepted" : "")
          }
          role="status"
        >
          <strong>{result.status}</strong>
          <span>
            Passed {result.passed} / {result.total} ·{" "}
            {Math.round(result.runtime_ms)} ms
          </span>
          <div className="test-chips">
            {result.tests.map((t: any) => (
              <Badge
                kind={t.status === "Accepted" ? "olive" : ""}
                key={t.index}
              >
                Case {t.index}: {t.status}
              </Badge>
            ))}
          </div>
        </div>
      ) : (
        <div className="console-empty">
          Run your code to check the visible examples. Submit to evaluate all
          cases.
        </div>
      )}
    </div>
  );
}
