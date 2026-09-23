import { useState } from "react";
import {
  Link,
  useNavigate,
  useParams,
  useSearchParams,
} from "react-router-dom";
import {
  ArrowRight,
  ArrowUpRight,
  BookOpen,
  Check,
  ChevronRight,
  Clock3,
  Code2,
  Flame,
  Search,
  Target,
  Trophy,
  TrendingUp,
} from "lucide-react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api, date } from "../api";
import { HeroAtmosphere, MotionToggle, useMotion } from "../components/Motion";
import {
  Badge,
  Brand,
  CompanyMark,
  Empty,
  ErrorBox,
  Loading,
  PageHeading,
  useAuth,
  useData,
} from "../shared";

export function Landing() {
  const { user } = useAuth();
  return (
    <div className="landing">
      <header>
        <Brand />
        <nav>
          <Link to="/companies">Explore companies</Link>
          <Link to={user ? "/dashboard" : "/login"}>Sign in</Link>
          <Link className="btn small" to={user ? "/dashboard" : "/signup"}>
            Start preparing <ArrowUpRight size={16} />
          </Link>
        </nav>
      </header>
      <main>
        <section className="landing-hero">
          <HeroAtmosphere />
          <div className="eyebrow">
            <span className="tiny-line" /> PREPARATION WITH A PURPOSE
          </div>
          <h1>
            Prepare for the company.
            <br />
            Practice the pattern.
            <br />
            <span>Own your next chapter.</span>
          </h1>
          <p>
            Company-focused mock assessments, aptitude practice
            <br className="desktop" /> and coding challenges. One thoughtfully
            connected workspace.
          </p>
          <div className="actions">
            <Link className="btn" to={user ? "/dashboard" : "/signup"}>
              Start preparing <ArrowRight size={18} />
            </Link>
            <Link className="btn secondary" to="/companies">
              Explore companies
            </Link>
          </div>
          <div className="hero-details">
            <span>
              <Check size={15} />
              Original practice questions
            </span>
            <span>
              <Check size={15} />
              Progress that stays with you
            </span>
          </div>
          <div className="landing-motion">
            <MotionToggle />
          </div>
        </section>
        <section className="landing-preview panel">
          <div className="preview-title">
            <span className="eyebrow">YOUR NEXT OPPORTUNITY</span>
            <span>Explore. Practice. Improve.</span>
          </div>
          <div className="grid three">
            {[
              ["Google", "Software Engineer"],
              ["TCS", "Graduate Engineer"],
              ["Adobe", "Software Engineer"],
            ].map(([c, t]) => (
              <Link
                to={"/companies/" + c.toLowerCase()}
                className="preview-company"
                key={c}
              >
                <CompanyMark name={c} />
                <h3>{c}</h3>
                <p>{t}</p>
                <span>
                  Explore practice tracks <ArrowUpRight size={16} />
                </span>
              </Link>
            ))}
          </div>
          <p className="disclaimer">
            Practice assessments are independently created for preparation and
            are not official tests of the respective companies.
          </p>
        </section>
        <section className="landing-steps">
          <PageHeading
            eyebrow="A CLEARER WAY FORWARD"
            title="Less searching. More preparing."
          />
          <div className="grid three">
            {[
              [
                "01",
                "Find your direction",
                "Choose a company and role, then select the challenge that fits your level.",
              ],
              [
                "02",
                "Get into your flow",
                "Practice in a focused assessment with a real timer, saved answers and coding challenges.",
              ],
              [
                "03",
                "Know your next step",
                "Review every attempt and turn your strengths and gaps into a preparation plan.",
              ],
            ].map(([n, t, d]) => (
              <div key={n}>
                <span className="step-number">{n}</span>
                <h2>{t}</h2>
                <p>{d}</p>
              </div>
            ))}
          </div>
        </section>
      </main>
      <footer>
        <Brand />
        <span>Built for the work before the opportunity.</span>
      </footer>
    </div>
  );
}

function Stat({
  label,
  value,
  caption,
  icon: Icon,
}: {
  label: string;
  value: string | number;
  caption: string;
  icon: typeof Target;
}) {
  return (
    <div className="stat panel">
      <div className="stat-top">
        {label}
        <Icon size={18} />
      </div>
      <strong>{value}</strong>
      <small>{caption}</small>
    </div>
  );
}
export function Trend({ data }: { data: any[] }) {
  const { enabled } = useMotion();
  return (
    <div className="chart" aria-label="Score over time">
      {data.length ? (
        <ResponsiveContainer width="100%" height={220}>
          <AreaChart data={data.map((d, i) => ({ ...d, label: `${i + 1}` }))}>
            <defs>
              <linearGradient id="scoreFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#87a866" stopOpacity={0.25} />
                <stop offset="100%" stopColor="#87a866" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid
              strokeDasharray="3 6"
              vertical={false}
              stroke="var(--border)"
            />
            <XAxis
              dataKey="label"
              tickLine={false}
              axisLine={false}
              fontSize={12}
            />
            <YAxis
              domain={[0, 100]}
              tickLine={false}
              axisLine={false}
              fontSize={12}
              width={30}
            />
            <Tooltip
              contentStyle={{
                background: "var(--surface)",
                border: "1px solid var(--border)",
                borderRadius: 12,
              }}
              labelFormatter={(l) => `Attempt ${l}`}
            />
            <Area
              isAnimationActive={enabled}
              animationDuration={450}
              name="Score %"
              type="monotone"
              dataKey="score"
              stroke="#6c8c4d"
              strokeWidth={3}
              fill="url(#scoreFill)"
            />
          </AreaChart>
        </ResponsiveContainer>
      ) : (
        <Empty
          title="Your progress starts here"
          text="Complete your first mock to see your performance take shape."
        />
      )}
    </div>
  );
}
export function Dashboard() {
  const { user } = useAuth();
  const { data: d, error } = useData("/analytics");
  const { data: companies } = useData<any[]>("/companies");
  const { data: announcements } = useData<any[]>("/announcements");
  if (error) return <ErrorBox error={error} />;
  if (!d) return <Loading />;
  const recommended = (companies || [])
    .slice()
    .sort(
      (a, b) =>
        Number(d.target_companies.includes(b.name)) -
        Number(d.target_companies.includes(a.name)),
    )
    .slice(0, 3);
  return (
    <>
      <PageHeading
        eyebrow="A LITTLE BETTER, EVERY DAY"
        title={`Welcome back, ${user?.full_name.split(" ")[0]}.`}
        text="Your next opportunity starts with what you do today."
        action={
          <Link className="btn secondary small" to="/history">
            <Clock3 size={16} />
            View history
          </Link>
        }
      />
      {announcements?.map((note) => (
        <div className="panel announcement" key={note.id}>
          <strong>{note.title}</strong>
          <p>{note.body}</p>
        </div>
      ))}
      <section className="focus-banner">
        <div>
          <Badge kind="olive">YOUR NEXT MOVE</Badge>
          <h2>
            {d.active
              ? "Pick up where you left off."
              : "Big goals. Small, focused steps."}
          </h2>
          <p>
            {d.active
              ? `${d.active.company} · ${d.active.track} · ${d.active.difficulty}`
              : "Choose a company. Practice its configured pattern. Build your confidence."}
          </p>
          <Link
            className="btn"
            to={d.active ? "/attempt/" + d.active.id : "/companies"}
          >
            {d.active ? "Resume assessment" : "Find your next mock"}
            <ArrowRight size={18} />
          </Link>
        </div>
        <div className="focus-art" aria-hidden="true">
          <div className="orbit orbit-one" />
          <div className="orbit orbit-two" />
          <div className="focus-symbol">
            <Target strokeWidth={1.1} />
          </div>
          <span className="art-label">ONE STEP CLOSER</span>
        </div>
      </section>
      <div className="grid four stats">
        <Stat
          label="Tests attempted"
          value={d.attempts}
          caption="Every attempt is a step forward"
          icon={BookOpen}
        />
        <Stat
          label="Average score"
          value={d.average === null ? "—" : `${d.average}%`}
          caption={
            d.best === null
              ? "Your first score awaits"
              : `Personal best: ${d.best}%`
          }
          icon={TrendingUp}
        />
        <Stat
          label="Coding solved"
          value={d.solved}
          caption="Unique challenges accepted"
          icon={Code2}
        />
        <Stat
          label="Practice streak"
          value={`${d.streak} days`}
          caption={`${Math.round(d.practice_seconds / 60)} minutes invested`}
          icon={Flame}
        />
      </div>
      <div className="section-title">
        <h2>Find your next company</h2>
        <Link to="/companies">
          Explore all companies <ArrowUpRight size={16} />
        </Link>
      </div>
      <div className="grid three">
        {recommended.map((c) => (
          <CompanyCard key={c.id} c={c} />
        ))}
      </div>
      <div className="grid dashboard-bottom">
        <section className="panel">
          <div className="section-title">
            <div>
              <h2>Your performance</h2>
              <p>A little perspective on your progress.</p>
            </div>
            <Badge>Last {d.trend.length} attempts</Badge>
          </div>
          <Trend data={d.trend} />
        </section>
        <section className="panel">
          <div className="section-title">
            <h2>Your focus areas</h2>
            <Target size={18} />
          </div>
          {d.topics.length ? (
            <div className="topic-list">
              {d.topics.slice(0, 4).map((t: any) => (
                <Link
                  key={t.name}
                  to={"/practice?topic=" + encodeURIComponent(t.name)}
                >
                  <span>
                    {t.name}
                    <small>
                      {t.accuracy < 60 ? "Room to grow" : "Keep the momentum"}
                    </small>
                  </span>
                  <strong>{t.accuracy}%</strong>
                  <ChevronRight size={15} />
                </Link>
              ))}
            </div>
          ) : (
            <Empty
              title="Let’s find your strengths"
              text="Your first assessment will help us recommend what to practice next."
              action={
                <Link to="/practice">
                  Try topic practice <ArrowRight size={15} />
                </Link>
              }
            />
          )}
        </section>
      </div>
      <section className="panel">
        <div className="section-title">
          <h2>Recent attempts</h2>
          <Link to="/history">
            View all <ArrowUpRight size={16} />
          </Link>
        </div>
        {d.recent.length ? (
          <AttemptTable items={d.recent} />
        ) : (
          <Empty
            title="No tests attempted yet."
            text="Take your first mock and start building your story."
            action={
              <Link className="btn secondary" to="/companies">
                Take your first mock
              </Link>
            }
          />
        )}
      </section>
    </>
  );
}
export function CompanyCard({ c }: { c: any }) {
  return (
    <Link to={"/companies/" + c.slug} className="company-card panel">
      <div className="company-card-top">
        <CompanyMark name={c.name} logo={c.logo} />
        <ArrowUpRight size={19} />
      </div>
      <h3>{c.name}</h3>
      <p>{c.category}</p>
      <div className="company-card-bottom">
        <span>{c.tracks.length} preparation tracks</span>
        <span>
          <Code2 size={14} />
          Coding
        </span>
      </div>
    </Link>
  );
}
export function Companies() {
  const [search, setSearch] = useState(""),
    [category, setCategory] = useState(""),
    [role, setRole] = useState("");
  const { data, error } = useData<any[]>("/companies");
  if (error) return <ErrorBox error={error} />;
  if (!data) return <Loading />;
  const filtered = data.filter(
    (c) =>
      c.name.toLowerCase().includes(search.toLowerCase()) &&
      (!category || c.category === category) &&
      (!role || c.tracks.some((t: any) => t.name === role)),
  );
  return (
    <>
      <PageHeading
        eyebrow="PICK A DIRECTION"
        title="Company explorer"
        text="The company you’re aiming for. The practice that gets you closer."
      />
      <div className="filter-bar">
        <label className="search-field">
          <Search size={18} />
          <input
            aria-label="Search companies"
            placeholder="Search Google, TCS, Amazon…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </label>
        <select
          aria-label="Company category"
          value={category}
          onChange={(e) => setCategory(e.target.value)}
        >
          <option value="">All categories</option>
          {[...new Set(data.map((c) => c.category))].map((c) => (
            <option key={c}>{c}</option>
          ))}
        </select>
        <select
          aria-label="Hiring role"
          value={role}
          onChange={(e) => setRole(e.target.value)}
        >
          <option value="">All roles</option>
          {[
            ...new Set<string>(
              data.flatMap((c) => c.tracks.map((t: any) => t.name)),
            ),
          ].map((t) => (
            <option key={t}>{t}</option>
          ))}
        </select>
      </div>
      <div className="section-title">
        <p>{filtered.length} companies to explore</p>
        <Badge>Independent practice configurations</Badge>
      </div>
      <div className="grid three">
        {filtered.map((c) => (
          <CompanyCard c={c} key={c.id} />
        ))}
      </div>
      {!filtered.length && (
        <Empty
          title="No matching companies"
          text="Try another company name or clear your filters."
        />
      )}
    </>
  );
}
export function CompanyPage() {
  const { slug } = useParams();
  const { data: c, error } = useData("/companies/" + slug);
  if (error) return <ErrorBox error={error} />;
  if (!c) return <Loading />;
  return (
    <>
      <Link className="back-link" to="/companies">
        ← Company explorer
      </Link>
      <div className="company-heading">
        <CompanyMark name={c.name} logo={c.logo} />
        <PageHeading
          eyebrow={c.category}
          title={`Your path to ${c.name}`}
          text={c.description}
        />
      </div>
      <div className="section-title">
        <h2>Choose your preparation track</h2>
        <Badge>{c.tracks.length} tracks</Badge>
      </div>
      <div className="grid two">
        {c.tracks.map((t: any) => (
          <Link key={t.id} className="panel track-card" to={"/tracks/" + t.id}>
            <div className="track-icon">
              <Code2 />
            </div>
            <Badge>Practice configuration</Badge>
            <h2>{t.name}</h2>
            <p>{t.description}</p>
            <div className="track-details">
              <span>
                <BookOpen size={16} />
                Aptitude + technical + coding
              </span>
              <span>
                <Target size={16} />3 difficulty levels
              </span>
            </div>
            <div className="track-cta">
              Choose difficulty <ArrowRight size={18} />
            </div>
          </Link>
        ))}
      </div>
    </>
  );
}
export function Instructions() {
  const { id } = useParams();
  const [questionCount, setQuestionCount] = useState(25);
  const { data: mixedPattern, error: mixedError } = useData(
    `/assessments/mixed-pattern?count=${questionCount || 25}`,
  );
  const [params] = useSearchParams();
  const [difficulty, setDifficulty] = useState(
      params.get("difficulty") || "moderate",
    ),
    [error, setError] = useState<unknown>(null),
    [busy, setBusy] = useState(false);
  const { data: basePattern, error: loadError } = useData("/tracks/" + id);
  const p =
    questionCount && basePattern && mixedPattern
      ? {
          ...basePattern,
          ...mixedPattern,
          company: basePattern.company,
          company_slug: basePattern.company_slug,
          track: basePattern.track,
        }
      : basePattern;
  const nav = useNavigate();
  if (loadError) return <ErrorBox error={loadError} />;
  if (mixedError) return <ErrorBox error={mixedError} />;
  if (!p || (questionCount && !mixedPattern)) return <Loading />;
  async function start() {
    setBusy(true);
    setError(null);
    try {
      const d = await api("/assessments/start", "POST", {
        track_id: id,
        question_count: questionCount || null,
        difficulty,
      });
      nav("/attempt/" + d.id);
    } catch (e) {
      setError(e);
    } finally {
      setBusy(false);
    }
  }
  const count = p.sections.reduce(
    (s: number, a: any) => s + a.question_count,
    0,
  );
  return (
    <>
      <Link className="back-link" to={"/companies/" + p.company_slug}>
        ← {p.company}
      </Link>
      <PageHeading
        eyebrow="SET YOUR CHALLENGE"
        title={p.track}
        text={`${p.company} · Independently created practice configuration`}
      />
      <section className="panel mixed-pattern-control">
        <label>
          Assessment question count
          <select
            aria-label="Assessment question count"
            value={questionCount}
            onChange={(e) => setQuestionCount(Number(e.target.value))}
          >
            <option value={25}>25 questions · 5 per area</option>
            <option value={50}>50 questions · 10 per area</option>
            <option value={75}>75 questions · 15 per area</option>
            <option value={0}>Original company practice pattern</option>
          </select>
        </label>
        <p>
          {questionCount
            ? "Mixed preparation: Quants, Logical, Verbal, Data Interpretation, and unscored Psychometric Reflection. This replaces the original section mix for this attempt."
            : "Use the administrator-configured company pattern, including its coding section."}
        </p>
      </section>
      <div className="difficulty-grid">
        {[
          [
            "beginner",
            "Build the foundation",
            "A little more time. Solid fundamentals.",
          ],
          [
            "moderate",
            "Find your rhythm",
            "Applied concepts. Placement-level practice.",
          ],
          ["pro", "Raise the bar", "Deeper problems. A tighter time budget."],
        ].map(([d, t, s]) => (
          <button
            key={d}
            className={"panel difficulty " + (difficulty === d ? "chosen" : "")}
            onClick={() => setDifficulty(d)}
          >
            <div>
              <Badge>{d}</Badge>
              <span className="radio-dot" />
            </div>
            <h3>{t}</h3>
            <p>{s}</p>
          </button>
        ))}
      </div>
      <div className="grid instructions-grid">
        <section className="panel">
          <h2>Your assessment at a glance</h2>
          <div className="assessment-facts">
            <span>
              <Clock3 />{" "}
              <strong>
                {Math.round(
                  p.duration_minutes * p.difficulty_rules[difficulty],
                )}{" "}
                min
              </strong>
              Total time
            </span>
            <span>
              <BookOpen />
              <strong>{count} questions</strong>Original practice
            </span>
            <span>
              <Trophy />
              <strong>
                {p.sections.reduce(
                  (s: number, a: any) =>
                    s + a.question_count * a.marks * a.weight,
                  0,
                )}{" "}
                marks
              </strong>
              Maximum score
            </span>
          </div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Section</th>
                  <th>Questions</th>
                  <th>Marks each</th>
                  <th>Penalty</th>
                </tr>
              </thead>
              <tbody>
                {p.sections.map((s: any) => (
                  <tr key={s.name}>
                    <td>{s.name}</td>
                    <td>{s.question_count}</td>
                    <td>{s.marks * s.weight}</td>
                    <td>{s.negative_marks * s.weight}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
        <section className="panel">
          <h2>A moment before you begin</h2>
          <ul className="rules">
            <li>
              Your server-timed assessment continues if you refresh or close the
              browser.
            </li>
            <li>
              Answers save automatically. Check the save indicator before moving
              on.
            </li>
            <li>
              Run checks examples. Submit code evaluates hidden cases and saves
              a coding score. Edited code must be submitted again.
            </li>
            <li>
              Fullscreen is optional. Leaving the assessment window may be
              recorded.
            </li>
            <li>
              Review policy: {p.review_policy}
              {p.review_policy === "delayed"
                ? ` (${p.review_delay_hours} hours)`
                : ""}
              .
            </li>
          </ul>
          <ErrorBox error={error} />
          <button
            className="btn full"
            onClick={() => void start()}
            disabled={busy}
          >
            {busy ? "Preparing your assessment…" : "Start assessment"}
            <ArrowRight size={18} />
          </button>
          <p className="small-text">
            You may have one active assessment at a time.
          </p>
        </section>
      </div>
    </>
  );
}

export function Practice() {
  const [params] = useSearchParams();
  const [topic, setTopic] = useState(
      params.get("topic") || "Quantitative Aptitude",
    ),
    [difficulty, setDifficulty] = useState("moderate"),
    [count, setCount] = useState(1),
    [error, setError] = useState<unknown>(null),
    [busy, setBusy] = useState(false);
  const { data: topics } = useData<string[]>("/topics");
  const nav = useNavigate();
  async function start() {
    setBusy(true);
    try {
      const d = await api("/assessments/practice", "POST", {
        topic,
        difficulty,
        count,
      });
      nav("/attempt/" + d.id);
    } catch (e) {
      setError(e);
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <PageHeading
        eyebrow="SMALL SESSIONS. LASTING PROGRESS."
        title="Practice with intention"
        text="Pick one topic. Give it your full attention."
      />
      <Link className="panel learning-promo" to="/learn">
        <strong>Try a balanced 25, 50 or 75-question set</strong>
        <p>
          All five preparation areas, plus original learning guides. Open
          learning library →
        </p>
      </Link>
      <div className="panel practice-config">
        <div className="empty-icon">
          <Target />
        </div>
        <h2>What will you work on today?</h2>
        <p>Short, focused sessions with saved results and explanations.</p>
        <div className="form-grid">
          <label>
            Topic
            <select
              aria-label="Topic"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
            >
              {topics?.map((t) => (
                <option key={t}>{t}</option>
              ))}
            </select>
          </label>
          <label>
            Difficulty
            <select
              aria-label="Difficulty"
              value={difficulty}
              onChange={(e) => setDifficulty(e.target.value)}
            >
              {["beginner", "moderate", "pro"].map((t) => (
                <option key={t}>{t}</option>
              ))}
            </select>
          </label>
          <label>
            Question count
            <input
              type="number"
              min={1}
              max={20}
              value={count}
              onChange={(e) => setCount(Number(e.target.value))}
            />
          </label>
        </div>
        <p className="small-text">
          Five minutes per question. The starter bank has 1–2 questions per
          topic and difficulty; larger sessions become available as admins add
          questions.
        </p>
        <ErrorBox error={error} />
        <button className="btn" disabled={busy} onClick={() => void start()}>
          {busy ? "Preparing…" : "Start practice"}
          <ArrowRight size={18} />
        </button>
      </div>
    </>
  );
}
export function CodingList() {
  const [difficulty, setDifficulty] = useState(""),
    [search, setSearch] = useState(""),
    [topic, setTopic] = useState("");
  const { data, error } = useData<any[]>("/questions?type=coding");
  if (error) return <ErrorBox error={error} />;
  if (!data) return <Loading />;
  const items = data.filter(
    (q) =>
      (!difficulty || q.difficulty === difficulty) &&
      q.title.toLowerCase().includes(search.toLowerCase()) &&
      (!topic || q.tags.includes(topic)),
  );
  return (
    <>
      <PageHeading
        eyebrow="THINK IT THROUGH. CODE IT OUT."
        title="Coding challenges"
        text="Original problems. Visible examples. Hidden cases that test the details."
      />
      <div className="filter-bar">
        <label className="search-field">
          <Search size={18} />
          <input
            aria-label="Search coding challenges"
            placeholder="Find a challenge…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </label>
        <select
          aria-label="Coding difficulty"
          value={difficulty}
          onChange={(e) => setDifficulty(e.target.value)}
        >
          <option value="">All levels</option>
          <option value="beginner">Easy</option>
          <option value="moderate">Medium</option>
          <option value="pro">Hard</option>
        </select>
        <select
          aria-label="Coding topic"
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
        >
          <option value="">All topics</option>
          {[...new Set<string>(data.flatMap((q) => q.tags))].map((t) => (
            <option key={t}>{t}</option>
          ))}
        </select>
      </div>
      <div className="panel problem-list">
        {items.map((q, i) => (
          <Link key={q.id} to={"/coding/" + q.slug}>
            <span className="problem-number">
              {String(i + 1).padStart(2, "0")}
            </span>
            <div>
              <h3>{q.title}</h3>
              <p>{q.tags.join(" · ")}</p>
            </div>
            <Badge kind={q.difficulty}>
              {q.difficulty === "beginner"
                ? "Easy"
                : q.difficulty === "pro"
                  ? "Hard"
                  : "Medium"}
            </Badge>
            <ArrowUpRight size={19} />
          </Link>
        ))}
      </div>
      {!items.length && (
        <Empty title="No matching challenges" text="Try a different filter." />
      )}
    </>
  );
}
export function Bookmarks() {
  const { data, error, reload } = useData<any[]>("/bookmarks");
  const [failure, setFailure] = useState<unknown>(null);
  async function remove(id: string) {
    try {
      await api("/bookmarks/" + id, "DELETE");
      reload();
    } catch (e) {
      setFailure(e);
    }
  }
  return (
    <>
      <PageHeading
        eyebrow="KEEP THE GOOD QUESTIONS CLOSE"
        title="Saved questions"
        text="A personal collection for the things you want to revisit."
      />
      <ErrorBox error={error || failure} />
      {!data && !error ? (
        <Loading />
      ) : data?.length ? (
        <div className="grid two">
          {data.map((q) => (
            <div className="panel saved-card" key={q.id}>
              <Badge>{q.difficulty}</Badge>
              <h3>{q.title}</h3>
              <p>{q.topic}</p>
              <div className="actions">
                <Link
                  className="btn secondary small"
                  to={
                    q.type === "coding"
                      ? "/coding/" + q.slug
                      : "/practice?topic=" + encodeURIComponent(q.topic)
                  }
                >
                  Practice topic
                </Link>
                <button className="quiet" onClick={() => void remove(q.id)}>
                  Remove
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <Empty
          title="Your collection is waiting"
          text="Save a question during an assessment or while exploring a coding challenge."
          action={
            <Link className="btn secondary" to="/coding">
              Explore coding challenges
            </Link>
          }
        />
      )}
    </>
  );
}
export function AttemptTable({ items }: { items: any[] }) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Assessment</th>
            <th>Difficulty</th>
            <th>Score</th>
            <th>Date</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {items.map((a) => (
            <tr key={a.id}>
              <td>
                <strong>{a.company}</strong>
                <small>{a.track}</small>
              </td>
              <td>
                <Badge>{a.difficulty}</Badge>
              </td>
              <td>
                <strong>{a.result.percentage}%</strong>
                <small>
                  {a.result.score} / {a.result.maximum}
                </small>
              </td>
              <td>
                {date(a.started_at)}
                <small>
                  {Math.round(a.result.time_used / 60)} min · completed
                </small>
              </td>
              <td>
                <Link
                  className="table-link"
                  to={"/attempt/" + a.id + "/result"}
                >
                  View result <ArrowUpRight size={15} />
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
export function HistoryPage() {
  const [difficulty, setDifficulty] = useState(""),
    [company, setCompany] = useState(""),
    [after, setAfter] = useState(""),
    [score, setScore] = useState(0),
    [page, setPage] = useState(1);
  const { data: companies } = useData<any[]>("/companies");
  const { data, error } = useData(
    `/history?difficulty=${difficulty}&company=${encodeURIComponent(company)}&after=${after ? new Date(after).getTime() / 1000 : 0}&min_score=${score}&page=${page}`,
  );
  return (
    <>
      <PageHeading
        eyebrow="EVERY ATTEMPT COUNTS"
        title="Your preparation history"
        text="The work you’ve put in, all in one place."
      />
      <div className="filter-bar">
        <select
          aria-label="History company"
          value={company}
          onChange={(e) => {
            setCompany(e.target.value);
            setPage(1);
          }}
        >
          <option value="">All companies</option>
          {companies?.map((c) => (
            <option key={c.id}>{c.name}</option>
          ))}
          <option>Topic practice</option>
        </select>
        <select
          aria-label="History difficulty"
          value={difficulty}
          onChange={(e) => {
            setDifficulty(e.target.value);
            setPage(1);
          }}
        >
          <option value="">All difficulties</option>
          {["beginner", "moderate", "pro"].map((d) => (
            <option key={d}>{d}</option>
          ))}
        </select>
        <label>
          Since
          <input
            aria-label="History since date"
            type="date"
            value={after}
            onChange={(e) => {
              setAfter(e.target.value);
              setPage(1);
            }}
          />
        </label>
        <label>
          Minimum %
          <input
            aria-label="Minimum score"
            type="number"
            min={0}
            max={100}
            value={score}
            onChange={(e) => {
              setScore(Number(e.target.value));
              setPage(1);
            }}
          />
        </label>
      </div>
      <ErrorBox error={error} />
      {!data && !error ? (
        <Loading />
      ) : data?.items.length ? (
        <section className="panel">
          <AttemptTable items={data.items} />
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
              disabled={page * 20 >= data.total}
              onClick={() => setPage((p) => p + 1)}
            >
              Next
            </button>
          </div>
        </section>
      ) : (
        <Empty
          title="No completed assessments yet."
          text="Your completed mocks and practice sessions will appear here."
          action={
            <Link className="btn" to="/companies">
              Take a mock
            </Link>
          }
        />
      )}
    </>
  );
}
export function AnalyticsPage() {
  const { data: d, error } = useData("/analytics");
  if (error) return <ErrorBox error={error} />;
  if (!d) return <Loading />;
  return (
    <>
      <PageHeading
        eyebrow="UNDERSTAND YOUR MOMENTUM"
        title="Progress, in perspective"
        text="A clear picture of what’s working and where to go next."
      />
      {!d.attempts ? (
        <Empty
          title="Your progress deserves a closer look"
          text="Complete a mock test to unlock your performance analytics."
          action={
            <Link className="btn" to="/companies">
              Take your first mock
            </Link>
          }
        />
      ) : (
        <>
          <div className="grid four stats">
            <Stat
              label="Average score"
              value={`${d.average}%`}
              caption={`${d.attempts} completed attempts`}
              icon={TrendingUp}
            />
            <Stat
              label="Personal best"
              value={`${d.best}%`}
              caption="Your highest assessment score"
              icon={Trophy}
            />
            <Stat
              label="Coding acceptance"
              value={
                d.coding_acceptance === null ? "—" : `${d.coding_acceptance}%`
              }
              caption="Across code submissions"
              icon={Code2}
            />
            <Stat
              label="Practice time"
              value={`${Math.round(d.practice_seconds / 60)} min`}
              caption="Time in completed assessments"
              icon={Clock3}
            />
          </div>
          <div className="grid two">
            <section className="panel">
              <h2>Score over time</h2>
              <Trend data={d.trend} />
            </section>
            <section className="panel">
              <h2>Topic accuracy</h2>
              <Bars
                items={d.topics.map((t: any) => ({
                  name: t.name,
                  score: t.accuracy,
                }))}
              />
            </section>
            <section className="panel">
              <h2>Company performance</h2>
              <Bars items={d.companies} />
            </section>
            <section className="panel">
              <h2>By difficulty</h2>
              <Bars items={d.difficulties} />
            </section>
          </div>
          <section className="panel recommendations">
            <h2>Your next steps</h2>
            {d.recommendations.length ? (
              d.recommendations.map((r: string) => (
                <p key={r}>
                  <Target size={18} />
                  {r}
                </p>
              ))
            ) : (
              <p>
                Your topic accuracy is at least 60% throughout. Try a higher
                difficulty to extend your preparation.
              </p>
            )}
            <Link className="btn secondary" to="/practice">
              Work on a topic <ArrowRight size={16} />
            </Link>
          </section>
        </>
      )}
    </>
  );
}
export function Bars({ items }: { items: { name: string; score: number }[] }) {
  return (
    <div className="bars">
      {items.map((t) => (
        <div key={t.name}>
          <div>
            <span>{t.name}</span>
            <strong>{Math.round(t.score)}%</strong>
          </div>
          <progress
            max={100}
            value={Math.max(0, t.score)}
            aria-label={t.name}
          />
        </div>
      ))}
    </div>
  );
}
