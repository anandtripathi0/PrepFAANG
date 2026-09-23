import { useState } from "react";
import { Plus, Save, Upload } from "lucide-react";
import { api } from "../api";
import { Badge, ErrorBox, Loading, PageHeading, useData } from "../shared";
const templates: Record<string, any> = {
  companies: {
    slug: "new-company",
    name: "New company",
    category: "Product Companies",
    description: "Independent practice configuration",
    logo: "",
    active: true,
  },
  tracks: {
    company_id: "",
    name: "Software Engineer",
    description: "Independent practice configuration",
    active: true,
  },
  patterns: {
    track_id: "",
    duration_minutes: 30,
    difficulty_rules: { beginner: 1.3, moderate: 1, pro: 0.8 },
    review_policy: "immediate",
    review_delay_hours: 24,
    active: true,
  },
  sections: {
    pattern_id: "",
    name: "Aptitude",
    position: 0,
    topics: ["Quantitative Aptitude"],
    question_count: 2,
    marks: 2,
    negative_marks: 0,
    weight: 1,
    partial_coding: true,
  },
  questions: {
    slug: "new-question",
    type: "mcq",
    title: "Question title",
    question: "Write an original question.",
    options: ["Option A", "Option B"],
    correct_answer: 0,
    explanation: "Explain why the answer is correct.",
    difficulty: "beginner",
    topic: "Quantitative Aptitude",
    status: "active",
  },
  announcements: {
    title: "Announcement",
    body: "Message for learners.",
    active: true,
  },
};
export function AdminPage() {
  const [entity, setEntity] = useState("companies"),
    [page, setPage] = useState(1),
    [editId, setEditId] = useState<string | null>(null),
    [editor, setEditor] = useState<string | null>(null),
    [error, setError] = useState<unknown>(null),
    [message, setMessage] = useState(""),
    [busy, setBusy] = useState(false),
    [importText, setImportText] = useState(""),
    [format, setFormat] = useState("json");
  const {
    data,
    error: loadError,
    reload,
  } = useData<any[]>(`/admin/${entity}?page=${page}`);
  function edit(row: any) {
    setEditId(row.id);
    const copy = { ...row };
    for (const k of ["id", "created_at", "updated_at"]) delete copy[k];
    if (entity === "users") {
      setEditor(
        JSON.stringify({ role: row.role, active: row.active }, null, 2),
      );
    } else setEditor(JSON.stringify(copy, null, 2));
    setError(null);
  }
  async function save() {
    setBusy(true);
    setError(null);
    try {
      await api(
        "/admin/" + entity + (editId ? "/" + editId : ""),
        editId ? "PUT" : "POST",
        JSON.parse(editor || "{}"),
      );
      setEditor(null);
      setMessage("Changes saved. Existing attempt snapshots are preserved.");
      reload();
    } catch (e) {
      setError(e);
    } finally {
      setBusy(false);
    }
  }
  async function importQuestions() {
    setBusy(true);
    setError(null);
    try {
      const r = await api("/admin/questions/import", "POST", {
        format,
        content: importText,
      });
      setMessage(`${r.imported} questions imported.`);
      setImportText("");
      reload();
    } catch (e) {
      setError(e);
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <PageHeading
        eyebrow="PREPFORGE CONTROL ROOM"
        title="Administration"
        text="Manage the catalog, assessment patterns and original question bank."
      />
      <div className="admin-tabs">
        {[
          "companies",
          "tracks",
          "patterns",
          "sections",
          "questions",
          "users",
          "attempts",
          "announcements",
        ].map((e) => (
          <button
            key={e}
            className={entity === e ? "active" : ""}
            onClick={() => {
              setEntity(e);
              setPage(1);
              setEditor(null);
              setMessage("");
            }}
          >
            {e}
          </button>
        ))}
      </div>
      <ErrorBox error={error || loadError} />
      {message && (
        <div className="success" role="status">
          {message}
        </div>
      )}
      <div className="section-title">
        <h2>{entity[0].toUpperCase() + entity.slice(1)}</h2>
        {templates[entity] && (
          <button
            className="btn small"
            onClick={() => {
              setEditId(null);
              setEditor(JSON.stringify(templates[entity], null, 2));
            }}
          >
            <Plus size={16} />
            Add {entity.replace(/ies$/, "y").replace(/s$/, "")}
          </button>
        )}
      </div>
      {editor !== null && (
        <section className="panel admin-editor">
          <h2>{editId ? "Edit" : "Create"} record</h2>
          <p>
            Use the validated configuration below. IDs are available in the
            corresponding resource list. Invalid imports and configurations are
            rejected by the API.
          </p>
          <label>
            Configuration JSON
            <textarea
              spellCheck={false}
              rows={18}
              value={editor}
              onChange={(e) => setEditor(e.target.value)}
            />
          </label>
          <div className="actions">
            <button className="btn" disabled={busy} onClick={() => void save()}>
              <Save size={16} />
              {busy ? "Saving…" : "Save record"}
            </button>
            <button className="btn secondary" onClick={() => setEditor(null)}>
              Cancel
            </button>
          </div>
        </section>
      )}
      {!data && !loadError ? (
        <Loading />
      ) : (
        <div className="panel table-wrap">
          <table>
            <thead>
              <tr>
                <th>Record</th>
                <th>ID</th>
                <th>Status</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {data?.map((row) => (
                <tr key={row.id}>
                  <td>
                    <strong>
                      {row.name ||
                        row.title ||
                        row.email ||
                        row.snapshot?.company ||
                        "Assessment pattern"}
                    </strong>
                    <small>
                      {row.category ||
                        row.topic ||
                        row.track_id ||
                        row.pattern_id ||
                        row.company_id ||
                        row.role ||
                        row.snapshot?.track}
                    </small>
                  </td>
                  <td>
                    <code className="record-id">{row.id}</code>
                  </td>
                  <td>
                    <Badge>
                      {row.status ||
                        (row.active === false ? "inactive" : "active")}
                    </Badge>
                  </td>
                  <td>
                    {entity !== "attempts" && (
                      <button
                        className="btn secondary small"
                        onClick={() => edit(row)}
                      >
                        Edit
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="actions">
            <button
              className="btn secondary small"
              disabled={page === 1}
              onClick={() => setPage((p) => p - 1)}
            >
              Previous
            </button>
            <span>Page {page}</span>
            <button
              className="btn secondary small"
              disabled={!data || data.length < 50}
              onClick={() => setPage((p) => p + 1)}
            >
              Next
            </button>
          </div>
        </div>
      )}
      {entity === "questions" && (
        <section className="panel admin-import">
          <h2>Import original questions</h2>
          <p>
            JSON accepts an array of question objects. CSV uses the same field
            names, with JSON arrays in options and tag columns. The import
            validates every row before saving.
          </p>
          <label>
            Format
            <select value={format} onChange={(e) => setFormat(e.target.value)}>
              <option value="json">JSON</option>
              <option value="csv">CSV</option>
            </select>
          </label>
          <label>
            Question data
            <textarea
              rows={8}
              value={importText}
              onChange={(e) => setImportText(e.target.value)}
              placeholder="Paste your original question bank here"
            />
          </label>
          <button
            className="btn"
            disabled={busy || !importText.trim()}
            onClick={() => void importQuestions()}
          >
            <Upload size={16} />
            Validate & import
          </button>
        </section>
      )}
    </>
  );
}
