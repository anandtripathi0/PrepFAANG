import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { Bookmark } from "lucide-react";
import { api } from "../api";
import { ErrorBox, Loading, PageHeading, useData } from "../shared";
import { CodeEditor, ProblemStatement } from "../components/CodeEditor";
export default function CodingPage() {
  const { slug } = useParams();
  const { data: q, error } = useData("/questions/" + slug);
  const [code, setCode] = useState(""),
    [language, setLanguage] = useState("python"),
    [saved, setSaved] = useState(false),
    [failure, setFailure] = useState<unknown>(null);
  useEffect(() => {
    if (q) {
      setCode(q.coding.starter_code.python);
      setLanguage("python");
    }
  }, [q]);
  async function bookmark() {
    try {
      await api("/bookmarks/" + q.id, "PUT");
      setSaved(true);
    } catch (e) {
      setFailure(e);
    }
  }
  if (error) return <ErrorBox error={error} />;
  if (!q) return <Loading />;
  return (
    <>
      <Link className="back-link" to="/coding">
        ← Coding challenges
      </Link>
      <PageHeading
        eyebrow="MAKE THE LOGIC YOURS"
        title={q.title}
        action={
          <button
            className="btn secondary small"
            onClick={() => void bookmark()}
          >
            <Bookmark size={16} />
            {saved ? "Saved" : "Save problem"}
          </button>
        }
      />
      <ErrorBox error={failure} />
      <div className="coding-layout">
        <section className="panel">
          <ProblemStatement q={q} />
        </section>
        <section className="panel editor-panel">
          <CodeEditor
            q={q}
            code={code}
            language={language}
            onChange={setCode}
            onLanguage={(l) => {
              setLanguage(l);
              setCode(q.coding.starter_code[l]);
            }}
          />
        </section>
      </div>
    </>
  );
}
