import { Link, useParams } from "react-router-dom";
import { ArrowRight, CheckCircle2, Clock3, Trophy } from "lucide-react";
import {
  Badge,
  Empty,
  ErrorBox,
  Loading,
  PageHeading,
  useData,
} from "../shared";
import { Bars } from "./Workspace";
export function ResultPage() {
  const { id } = useParams();
  const { data: a, error } = useData("/attempts/" + id);
  if (error) return <ErrorBox error={error} />;
  if (!a) return <Loading />;
  if (!a.result)
    return (
      <Empty
        title="Your assessment is still active"
        action={
          <Link className="btn" to={"/attempt/" + id}>
            Resume assessment
          </Link>
        }
      />
    );
  const r = a.result;
  const strong = r.topics.filter((t: any) => t.correct / t.count >= 0.7),
    weak = r.topics.filter((t: any) => t.correct / t.count < 0.6);
  return (
    <>
      <PageHeading
        eyebrow="ANOTHER STEP FORWARD"
        title="The work is in. Here’s your progress."
        text={`${a.snapshot.company} · ${a.snapshot.track} · ${a.difficulty}`}
        action={
          <Link className="btn secondary small" to="/history">
            All attempts <ArrowRight size={16} />
          </Link>
        }
      />
      <section className="result-hero panel">
        <div
          className="score-ring"
          style={{
            background: `conic-gradient(var(--accent-dark) ${r.percentage}%, var(--border) 0)`,
          }}
        >
          <div>
            <strong>
              {r.percentage}
              <small>%</small>
            </strong>
            <span>Overall score</span>
          </div>
        </div>
        <div>
          <Badge kind="olive">
            <CheckCircle2 size={14} />
            Assessment complete
          </Badge>
          <h2>
            {r.percentage >= 80
              ? "A strong step forward."
              : r.percentage >= 50
                ? "You’re building momentum."
                : "Every attempt is a starting point."}
          </h2>
          <p>
            {r.score} of {r.maximum} marks earned. Your result is saved to your
            history.
          </p>
          <div className="result-meta">
            <span>
              <Clock3 size={17} />
              {Math.floor(r.time_used / 60)}m {r.time_used % 60}s
            </span>
            <span>
              <Trophy size={17} />
              {r.coding_score} coding marks
            </span>
          </div>
        </div>
        <div className="result-counts">
          <div>
            <strong>{r.correct}</strong>
            <span>Correct</span>
          </div>
          <div>
            <strong>{r.incorrect}</strong>
            <span>Incorrect / unevaluated</span>
          </div>
          <div>
            <strong>{r.unanswered}</strong>
            <span>Unanswered</span>
          </div>
        </div>
      </section>
      {!!r.reflections?.length && (
        <section className="panel reflection-notice">
          <h2>Your work-style reflection</h2>
          <p>
            {r.reflections.filter((x: any) => x.response !== null).length} of{" "}
            {r.reflections.length} reflection items answered. These responses
            are unscored and are not a psychological diagnosis or hiring
            recommendation.
          </p>
        </section>
      )}
      <div className="grid two">
        <section className="panel">
          <h2>Section performance</h2>
          <Bars
            items={r.sections.map((s: any) => ({
              name: s.name,
              score: (s.score / s.maximum) * 100,
            }))}
          />
        </section>
        <section className="panel">
          <h2>Topic accuracy</h2>
          <Bars
            items={r.topics.map((s: any) => ({
              name: s.name,
              score: (s.correct / s.count) * 100,
            }))}
          />
        </section>
        <section className="panel">
          <h2>Your strengths</h2>
          {strong.length ? (
            strong.map((t: any) => (
              <p className="strength" key={t.name}>
                <CheckCircle2 size={18} />
                {t.name}
              </p>
            ))
          ) : (
            <p>Keep practicing to establish your strongest topics.</p>
          )}
          <h3>Needs attention</h3>
          {weak.length ? (
            weak.map((t: any) => (
              <Link
                className="recommendation-link"
                key={t.name}
                to={"/practice?topic=" + encodeURIComponent(t.name)}
              >
                {t.name}
                <ArrowRight size={16} />
              </Link>
            ))
          ) : (
            <p>No topic is below 60% accuracy in this attempt.</p>
          )}
        </section>
        <section className="panel">
          <h2>Time distribution</h2>
          {r.sections.map((s: any) => (
            <div className="time-row" key={s.name}>
              <span>{s.name}</span>
              <strong>{Math.round(s.time_spent)}s</strong>
            </div>
          ))}
          <p className="small-text">
            Interaction time recorded while answering; excludes idle time before
            the first interaction.
          </p>
          <h3>Overall accuracy</h3>
          <p>
            {r.correct + r.incorrect
              ? Math.round((r.correct / (r.correct + r.incorrect)) * 100)
              : 0}
            % of answered questions correct · {a.difficulty} difficulty
          </p>
        </section>
      </div>
      <div className="section-title">
        <h2>Question review</h2>
        <Badge>{a.questions.length} questions</Badge>
      </div>
      {a.review_available ? (
        a.questions.map((aq: any, i: number) => {
          const q = aq.question,
            answer = aq.answer;
          return (
            <details className="panel review-question" key={aq.id}>
              <summary>
                <span>{String(i + 1).padStart(2, "0")}</span>
                <strong>{q.title}</strong>
                <Badge>
                  {q.type === "reflection"
                    ? "Unscored reflection"
                    : q.type === "coding"
                      ? answer.code_result?.status || "Not evaluated"
                      : answer.selected === null
                        ? "Unanswered"
                        : answer.selected === q.correct_answer
                          ? "Correct"
                          : "Incorrect"}
                </Badge>
              </summary>
              <div className="review-body">
                <p>{q.question}</p>
                {q.type === "reflection" ? (
                  <p>
                    Your reflection:{" "}
                    <strong>
                      {answer.selected === null
                        ? "Not answered"
                        : q.options[answer.selected]}
                    </strong>
                    . There is no correct answer; this response does not affect
                    your score.
                  </p>
                ) : q.type === "mcq" ? (
                  <>
                    <p>
                      Your answer:{" "}
                      <strong>
                        {answer.selected === null
                          ? "Not answered"
                          : q.options[answer.selected]}
                      </strong>
                    </p>
                    <p className="success-text">
                      Correct answer: {q.options[q.correct_answer]}
                    </p>
                  </>
                ) : (
                  <>
                    <pre>{answer.code || "No code submitted."}</pre>
                    <p>
                      {answer.code_result
                        ? `Passed ${answer.code_result.passed} / ${answer.code_result.total} tests`
                        : "No evaluated code submission."}
                    </p>
                  </>
                )}
                <h3>Explanation</h3>
                <p>{q.explanation}</p>
              </div>
            </details>
          );
        })
      ) : (
        <Empty
          title="Answer review isn’t available yet"
          text={
            a.snapshot.review_policy === "never"
              ? "The administrator has disabled answer review for this assessment."
              : `Review becomes available ${a.snapshot.review_delay_hours} hours after submission.`
          }
        />
      )}
    </>
  );
}
