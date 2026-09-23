import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ArrowRight, BookOpen, Layers, Sparkles } from "lucide-react";
import { api } from "../api";
import { Badge, ErrorBox, Loading, PageHeading, useData } from "../shared";

export default function Learning() {
  const { data, error } = useData("/learning");
  const [count, setCount] = useState(25);
  const [difficulty, setDifficulty] = useState("moderate");
  const [selected, setSelected] = useState(0);
  const [failure, setFailure] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);
  const navigate = useNavigate();
  async function start() {
    setBusy(true);
    setFailure(null);
    try {
      const result = await api("/assessments/mixed", "POST", {
        count,
        difficulty,
      });
      navigate("/attempt/" + result.id);
    } catch (e) {
      setFailure(e);
    } finally {
      setBusy(false);
    }
  }
  if (error) return <ErrorBox error={error} />;
  if (!data) return <Loading />;
  const guide = data.guides[selected];
  const duration = Math.round(
    count * 2 * ({ beginner: 1.2, moderate: 1, pro: 0.8 }[difficulty] || 1),
  );
  return (
    <>
      <PageHeading
        eyebrow="LEARN THE IDEA. PRACTICE THE SKILL."
        title="Your preparation library"
        text="Five foundations, one connected preparation plan. Original lessons and practice, built for PrepFaang."
      />
      <section className="panel mixed-builder">
        <div>
          <Badge kind="olive">
            <Layers size={14} />
            Mixed assessment
          </Badge>
          <h2>Choose your pace. Cover every area.</h2>
          <p>
            Quants, logical reasoning, verbal ability, data interpretation, and
            unscored work-style reflection.
          </p>
        </div>
        <div
          className="mixed-counts"
          role="group"
          aria-label="Mixed question count"
        >
          {[25, 50, 75].map((n) => (
            <button
              key={n}
              aria-pressed={count === n}
              className={count === n ? "chosen" : ""}
              onClick={() => setCount(n)}
            >
              <strong>{n}</strong>
              <span>questions</span>
            </button>
          ))}
        </div>
        <div className="form-grid">
          <label>
            Difficulty
            <select
              aria-label="Mixed difficulty"
              value={difficulty}
              onChange={(e) => setDifficulty(e.target.value)}
            >
              <option value="beginner">Beginner</option>
              <option value="moderate">Moderate</option>
              <option value="pro">Pro</option>
            </select>
          </label>
          <div className="mixed-summary">
            <strong>
              {count / 5} questions per area · {duration} minutes
            </strong>
            <span>
              {(count * 4) / 5} scored questions + {count / 5} reflection items
            </span>
            <span>2 marks per scored question · no negative marking</span>
          </div>
        </div>
        <p className="small-text">
          The timer begins when you start. Answers autosave and the test resumes
          after refresh. Reflection has no right answer and does not affect your
          score. This is not a validated psychological assessment.
        </p>
        <ErrorBox error={failure} />
        <button className="btn" disabled={busy} onClick={() => void start()}>
          {busy ? "Preparing your set…" : `Start ${count}-question assessment`}
          <ArrowRight size={17} />
        </button>
      </section>
      <div className="section-title">
        <h2>Learn, then put it into practice</h2>
        <Badge>
          <Sparkles size={13} />
          Original content
        </Badge>
      </div>
      <div
        className="learning-tabs"
        role="tablist"
        aria-label="Preparation areas"
      >
        {data.guides.map((g: any, i: number) => (
          <button
            key={g.topic}
            role="tab"
            aria-selected={selected === i}
            aria-controls="learning-panel"
            id={`learning-tab-${i}`}
            className={selected === i ? "active" : ""}
            onClick={() => setSelected(i)}
            onKeyDown={(e) => {
              if (e.key === "ArrowRight" || e.key === "ArrowLeft") {
                e.preventDefault();
                const next =
                  (i + (e.key === "ArrowRight" ? 1 : -1) + data.guides.length) %
                  data.guides.length;
                setSelected(next);
                document.getElementById(`learning-tab-${next}`)?.focus();
              }
            }}
          >
            <BookOpen size={16} />
            {g.name}
          </button>
        ))}
      </div>
      <section
        id="learning-panel"
        role="tabpanel"
        aria-labelledby={`learning-tab-${selected}`}
      >
        <PageHeading title={guide.name} text={guide.description} />
        <div className="grid two">
          {guide.lessons.map((lesson: any) => (
            <article className="panel lesson-card" key={lesson.title}>
              <h3>{lesson.title}</h3>
              <p>{lesson.rule}</p>
              <div className="lesson-example">
                <span>WORKED EXAMPLE</span>
                <p>{lesson.example}</p>
              </div>
            </article>
          ))}
        </div>
        <div className="actions learning-action">
          <Link
            className="btn secondary"
            to={"/practice?topic=" + encodeURIComponent(guide.topic)}
          >
            Practice this topic <ArrowRight size={16} />
          </Link>
        </div>
      </section>
      <p className="small-text">{data.notice}</p>
    </>
  );
}
