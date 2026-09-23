# PrepFaang

A working company-focused placement preparation application: register, personalize your profile, choose a company and role, take a server-timed mock, review the result, and use stored performance to decide what to practice next.

**Practice assessments are independently created for preparation and are not official tests of the respective companies.** All seeded questions are original. The company patterns are illustrative admin-configured practice patterns, not verified current recruitment specifications.

## Latest update

Live decorative animations include a persistent pause control and device reduced-motion support. Settings now supports current-password-verified password changes and signing out on every device. Successful password changes/resets invalidate all existing reset links; SMTP verifies server certificates. MongoDB remains connected to `prepForge` / `user_details`. See `docs/MOTION-SECURITY-UPDATE.md` for implementation and test details, and `START-HERE.md` for setup.

## Stack and architecture

- Python 3.12+, FastAPI, Pydantic, SQLAlchemy 2, Alembic, Argon2.
- React 19, TypeScript, Vite, React Router, Lucide, Recharts, locally bundled Monaco editor.
- MongoDB Atlas via PyMongo transactions; SQLite for offline development and PostgreSQL remain supported.
- Opaque, revocable database sessions in HttpOnly cookies, CSRF tokens, explicit roles and ownership checks.
- Independent Python runner service orchestrating disposable Docker containers. The web backend never executes submitted source code.

The React SPA is intentional: the application’s authenticated assessment flows do not require Next.js server rendering. FastAPI owns authentication, validation, business logic and persistence. Vite/nginx proxies `/api` to the backend under the same origin.

```text
frontend/src/
  pages/             Accounts, workspace, assessment, coding, result, admin
  components/        Monaco editor and problem renderer
  shared.tsx         Session context, protected layouts, shared UI
backend/app/
  auth.py            Sessions, CSRF, account tokens, SMTP, rate limiting
  models.py          SQLAlchemy entities and indexes
  assessment.py      Generation, snapshots, autosave, expiry, scoring
  questions.py       Question snapshots and safe public serialization
  catalog.py         Companies, profile, history, analytics, bookmarks
  admin.py           Validated CRUD and atomic question import
  code_runner.py     Authenticated HTTP runner adapter
  seed.py            Original practice content, idempotent seed
backend/migrations/  Alembic schema history
runner/              Separate orchestration service and sandbox image
```

## Run locally

From the `prepforge` directory, using Python 3.12+ and Node 22.12+:

```powershell
if (!(Test-Path .env)) { Copy-Item .env.example .env }
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
cd backend
..\.venv\Scripts\python.exe -m app.bootstrap
..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

In a second terminal:

```powershell
cd frontend
npm ci
npm run dev -- --port 5173
```

Open **http://localhost:5173**. The current workspace also works at **http://127.0.0.1:5173** when `FRONTEND_ORIGIN` is set to that exact origin. Do not mix the two origins within a session. Register your own account; there is no default password or hardcoded logged-in user. API documentation is at http://localhost:8000/docs.

On macOS/Linux, use `.venv/bin/python` and normal `cp` equivalents. Run backend commands from `backend/` so the environment file and SQLite path resolve consistently.

## Database configuration

Put your final connection string in **`prepforge/.env`**:

```dotenv
DATABASE_URL=mongodb+srv://USERNAME:PASSWORD@CLUSTER/?retryWrites=true&w=majority
DATABASE_NAME=prepForge
USER_COLLECTION=user_details
```

The template **`.env.example` deliberately contains `DATABASE_URL=` with no credentials**. A blank value uses `backend/prepforge.db` only in development. Environment variables override `.env`. URL-encode special characters in credentials. Switching the URL does not copy your existing SQLite data.

Run `python -m app.bootstrap` before starting the API: MongoDB gets collections/indexes and SQL databases get Alembic migrations; both receive the original content seed. MongoDB requires transaction support (Atlas or a replica set). Users are stored in `user_details` within `prepForge`; other entities use separate collections. Mongo persistence implements the application’s supported query operations and transactions; it is not a general SQL-to-Mongo engine. Application logic enforces relationships; MongoDB does not enforce SQL foreign keys.

For SQL databases only, use `python -m alembic upgrade head`. The checked-in initial migration contains explicit table/index operations. Generate future migrations using `alembic revision --autogenerate -m descriptive_name`, inspect them, then apply them. Back up production data before migrations.

### Models

Normalized entities include User, UserProfile, Session, AuthToken, RateBucket, Company, Track, Pattern, Section, Question, QuestionOption, CodingProblem, CodingTestCase, Attempt, AttemptQuestion, Answer, CodeSubmission, IntegrityEvent, Bookmark and Announcement. UUID primary keys, unique constraints, foreign keys and common query indexes are included. Flexible profile fields and immutable attempt snapshots use JSON columns. Topic aggregates are computed from stored results rather than duplicated in an eventually consistent statistics table.

### Development seed

`python -m app.seed` is idempotent. It creates:

- Google, Amazon, Microsoft, Meta, Apple, TCS, Infosys, Wipro, Accenture, Cognizant, Capgemini, Deloitte, IBM, Oracle and Adobe.
- Two tracks per company: Software Engineer plus Graduate Engineer for IT services, or Internship for other categories.
- 30 patterns, each with aptitude, reasoning, verbal, technical and coding sections.
- 231 original scored MCQs, 15 unscored work-style reflection items, and six original coding challenges (252 total).
- A learning library of 23 original short lessons across Quants, Logical, Verbal, Data Interpretation, and Psychometric Reflection.
- Mixed assessments with 25, 50, or 75 questions, equally divided across five areas. This gives 20/40/60 scored questions and 5/10/15 unscored reflections, worth 40/80/120 marks.
- Eight-question mocks worth 20 marks. Base duration 30 minutes; beginner 39 minutes, moderate 30, pro 24.

The mixed builder has enough original questions for every supported size and difficulty without repeating a question within an attempt. Numbered variants share underlying concepts. Company instructions default to 25 mixed questions; select Original company practice pattern to retain its coding section. Reflections have no correct answer, do not affect marks or accuracy, and are not a validated psychological test.

The linked PrepInsta public category pages informed the broad category structure only. This project does not reproduce their proprietary question bank or claim feature/content parity with their app. All included lessons and questions are independently authored.

The local credentials are stored only in ignored `.env`, excluded from source archives. Existing SQLite records were copied into Atlas without overwriting remote records; the SQLite file remains intact. The folder name and legacy cookie/storage identifiers remain `prepforge` to preserve existing sessions and local recovery data; the visible product is PrepFaang.

## Accounts and email

Sign up, sign in, remembered sessions, logout, onboarding, profile changes, verification and password reset are connected to the API. Password changes revoke existing sessions. Verification/reset tokens are single-use, hashed at rest, and expire in one hour. Passwords use Argon2.

Configure `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USER`, `EMAIL_PASSWORD` and `EMAIL_FROM` for SMTP with STARTTLS. In development without SMTP, verification/reset responses expose a labeled local development link. Production never does this. Verification is available in Settings; verified email is not currently mandatory to start practice.

Promote an existing account from the backend directory:

```powershell
..\.venv\Scripts\python.exe -m app.manage make-admin your-email@example.com
```

Admin access is enforced by the API. No registration input can grant an admin role.

## Assessment behavior

Patterns and section rules come from the database. Generation uses difficulty, topic distribution, company/track relevance and randomized selection; it rejects undersupplied configurations rather than silently changing difficulty. Starting an attempt persists question content, answer key, coding tests, rules, company/track labels and expiry. Editing a question or pattern never changes an existing attempt.

The server owns `started_at` and `expires_at`. The UI derives display time from a server response plus monotonic `performance.now()` and resynchronizes every 15 seconds. API requests enforce expiry; a 15-second background sweep finalizes abandoned expired attempts. Refresh, browser clock edits or local storage edits cannot extend an attempt.

MCQs save after selection; code changes debounce into the same API. A local queue retains unsaved edits for recovery and retries every second. Recovery never overrides server expiry. Save failures remain visible. Section and question navigation restore from the server. Only one active assessment is allowed per user.

**Run examples** evaluates visible cases. **Submit code** evaluates all cases and saves coding marks. Changing the code/language invalidates the prior result. **Submit test** uses the last evaluated version matching the saved buffer; unsubmitted code receives zero marks, which the confirmation explains. Hidden inputs, outputs and reference solutions are never returned to the browser. Coding is scored by fraction of passed cases or all-or-nothing per section configuration.

Scoring supports marks, negative marking, section weights and partial coding credit. Submission is idempotent. A negative raw score is retained; displayed percentage is floored at zero. Review policy can be immediate, delayed, or never.

Fullscreen is optional. Visibility changes, window blur and fullscreen exit are recorded as advisory integrity events. This is not secure proctoring and does not prevent OS shortcuts or other devices.

## Isolated code execution

**Docker is required for real code execution.** If no worker is available, the UI reports a 503 execution error; the app does not fake test results. Python, C, C++, Java and JavaScript are supported by the worker image.

For a local worker on a dedicated development host:

```powershell
docker build -t prepforge-sandbox:local -f runner/Dockerfile.sandbox .
# Set the same randomly generated CODE_RUNNER_TOKEN in .env and this terminal.
$env:CODE_RUNNER_TOKEN = 'YOUR_RANDOM_TOKEN'
.\.venv\Scripts\python.exe -m uvicorn runner.service:app --host 127.0.0.1 --port 8090
```

Each test launches an unprivileged disposable container with no network, read-only root, temporary filesystem, dropped capabilities, no-new-privileges, one CPU, cgroup memory/swap and process limits, bounded runtime, file size and output. Compilation has a 15-second budget. Cleanup runs even after timeout. Expected outputs remain in the external worker, not inside the code container. Only sanitized verdicts and timings reach the API/browser.

### Docker Compose

Set `DATABASE_URL`, a strong `CODE_RUNNER_TOKEN`, and `FRONTEND_ORIGIN=http://localhost:5173` in `.env` first. Compose uses the DATABASE_URL from .env without overriding it.

```sh
docker compose up -d sandbox-daemon
# Wait for the daemon to become ready before building its sandbox image.
docker compose --profile runner-setup run --rm sandbox-build
docker compose up --build -d
```

The worker talks over TLS to a **separate Docker-in-Docker daemon**, not the host Docker socket. Only the trusted source-build helper mounts the runner source; submitted code containers mount no host paths. The development daemon is privileged; never place this topology on a sensitive shared host. Production execution should use a dedicated sandbox VM/host, a bounded job queue and stronger isolation such as gVisor or microVMs, with patching, monitoring and abuse controls. Docker alone is not a guarantee against kernel exploits.

## Add a new company without code changes

1. Sign in as an admin and open Administration.
2. Companies → Add company → set name, slug, category and description.
3. Tracks → Add track → use the company’s ID and role name.
4. Patterns → Add pattern → use the track ID; set duration, difficulty multipliers and review policy.
5. Sections → add ordered sections using the pattern ID, topic list, count and scoring rules.
6. Questions → create original MCQs or coding problems and assign difficulty/topics and optional company/track tags.
7. Activate the company, track and pattern. Run a test at each difficulty to confirm sufficient coverage.

The admin editor uses validated JSON configurations, with resource IDs shown in the lists. Users can be activated/deactivated or promoted; questions archived; announcements created. Attempts are inspectable but not editable. Coding test cases are edited as part of their question. CSV/JSON import validates all rows before committing. `docs/question-import.json` is a sample. The admin panel is functional but uses a technical configuration editor rather than a polished nontechnical form builder.

## Environment variables

| Variable | Purpose |
|---|---|
| `APP_ENV` | `development` or `production` |
| `DATABASE_URL` | Blank for local SQLite; MongoDB Atlas or PostgreSQL otherwise |
| `DATABASE_NAME` | MongoDB database, default prepForge |
| `USER_COLLECTION` | MongoDB user collection, default user_details |
| `SECRET_KEY` | Required 32+ character production deployment secret; sessions themselves use random opaque tokens |
| `FRONTEND_ORIGIN` | Exact allowed browser origin, HTTPS in production |
| `EMAIL_*` | SMTP settings described above |
| `CODE_RUNNER_URL` | Private worker endpoint, default localhost:8090 |
| `CODE_RUNNER_TOKEN` | Shared worker authentication secret, 32+ characters in production |
| `REDIS_URL` | Reserved optional integration; core currently uses database-backed rate limiting |

Production configuration fails early if a MongoDB/PostgreSQL URL, HTTPS origin, required secret, mail host or runner secret is absent. No credentials are committed.

## Security and deployment

Use HTTPS and same-origin `/api` proxying. Production cookies are Secure, HttpOnly and SameSite=Lax. Mutations require a session CSRF token, and cross-origin writes are rejected. SQL is ORM parameterized; React escapes text; arbitrary HTML/Markdown is never rendered. Security headers are set in the API/nginx. Admin checks and attempt/submission/bookmark ownership are backend-enforced. Authentication and execution rate limits persist in the database. Deploy behind a reverse proxy that additionally enforces request-size, IP and connection limits. Do not expose FastAPI or the runner directly to the internet.

Before public deployment: configure SMTP and the selected database, run real sandbox integration tests, verify PostgreSQL concurrency, replace the development sandbox deployment with hardened workers, establish backups and observability, and load-test assessment submission. The worker currently has bounded concurrent evaluation but no durable job queue. The API evaluates code synchronously. Atlas persistence and SMTP authentication were verified. Actual email delivery, PostgreSQL concurrency and Docker execution have not been verified.

## Tests and build

```powershell
cd backend
..\.venv\Scripts\python.exe -m pytest -q
..\.venv\Scripts\python.exe -m ruff check app tests
cd ../frontend
npm test
npm run typecheck
npm run lint
npm run build
npx playwright install chromium
# Start both local servers before this command:
npm run test:e2e
```

The backend tests cover auth, hashing, CSRF, roles, snapshots, difficulty, insufficient inventory, recovery, expiry, scoring, ownership, idempotency, imports, rate limits and hidden-output sanitization. A test double verifies coding score integration; **this is not a real execution test**. Eight separate Docker integration cases test accepted/wrong/compile/runtime/timeout/network/output/resource behavior and skip explicitly if the sandbox image is unavailable.

The browser test checks the complete MCQ journey, real API persistence, coding-editor availability and honest worker-unavailable errors, second-user isolation, logout/login and dashboard overflow at 320, 360, 375, 390, 414, 768, 1024, 1280, 1440 and 1920px. On a runner-enabled deployment, update the coding assertions to accepted solutions and execute the full coding path. See `docs/VALIDATION.md` for the actual results of this build.

## Remaining scope

- Real Docker execution, PostgreSQL concurrency and SMTP delivery require infrastructure verification; no production-readiness claim is made.
- Optional leaderboards are not implemented; no private profiles are exposed publicly.
- Admin editing is schema-validated JSON, not a drag-and-drop pattern builder. No audit log UI or bulk user actions yet.
- Seed track patterns are intentionally illustrative and share a baseline. Add verified public pattern metadata and more original content before marketing company-specific realism.
- No durable distributed execution queue, remote proctoring, or per-section hard time limits. The assessment uses one server-authoritative total timer.
- Code practice outside an assessment is kept in the editor until submitted; assessment code has durable autosave/recovery.

These are explicit limitations, not placeholder buttons or fabricated functionality.

