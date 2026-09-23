# Validation report

Validated locally on Windows using Python 3.12, Node 25 and Chromium.

| Check | Result |
|---|---|
| Alembic initial migration | Applied successfully to SQLite |
| Alembic schema drift check | No new upgrade operations detected |
| Seed execution and repeat execution | Passed; no duplicate seed records |
| Backend pytest | 9 passed, 8 explicitly skipped |
| Backend Ruff | Passed |
| Frontend unit tests | 3 passed |
| TypeScript | Passed |
| ESLint | Passed |
| Production Vite build | Passed; lazy Monaco chunk size warning only |
| npm dependency audit | 0 known vulnerabilities at installation time |
| Main Playwright journey | Passed |
| Additional feature Playwright journey | Passed |
| Browser JavaScript exceptions | None in the passing journeys |
| Backend logs | No unexpected 500 responses in passing journeys |
| Responsive checks | Dashboard and MCQ assessment passed all ten requested widths |

## Browser coverage

The main journey exercised real HTTP requests and database persistence: signup, onboarding, fresh dashboard, company search, Google → Software Engineer → Moderate, assessment creation, MCQ autosave, review flag, next question, refresh, restoration of the same question IDs/answer/expiry, Monaco editor, unavailable-runner error for Run and Submit Code, final test submission, result, history, analytics, second-account isolation, logout, protected-route redirection and login recovery.

The additional journey exercised persistent dark mode, development email verification, coding bookmarks and removal, SQL topic practice, answer autosave, assessment submission and a 100% result. Screenshot files show the actual rendered dashboard, result, dark settings and mobile assessment.

Overflow assertions passed at 320, 360, 375, 390, 414, 768, 1024, 1280, 1440 and 1920 pixels. Screenshots were also inspected visually. This is not a full WCAG certification or an exhaustive audit of every route at every width.

## Backend coverage

Tests verify Argon2 hashing, sign-in/out, profile saving, CSRF/origin checks, role enforcement, account disable/demotion protection, password reset and session invalidation, rate limits, no fake empty analytics, pattern lookup, three difficulties, inventory shortage, duplicate-active-attempt rejection, snapshots, answer save/recovery, expiry, weighted negative marking, repeat submission, saved history and derived analytics, private attempts/results/code submissions/bookmarks, review restrictions, invalid imports and hidden-output filtering.

Coding score integration uses an explicitly identified **test double** for the runner. This proves the API-to-scoring contract, not execution isolation.

## Not verified here

Docker is not installed on the authoring machine. Eight real Docker integration cases were skipped: accepted, wrong answer, runtime failure, compilation failure, timeout, disabled network, resource limit and output limit. The browser verified truthful runner-unavailable behavior, not successful code execution.

No PostgreSQL service, SMTP credentials or deployed sandbox workers were supplied. PostgreSQL concurrency, real mail delivery, the Compose topology and adversarial sandbox behavior still require infrastructure testing. The application is a working development implementation, not an audited production deployment.

Optional leaderboards, a durable distributed runner queue, per-section hard timers and a visual admin pattern builder are not implemented. Administration uses validated JSON editing. Seed patterns are illustrative rather than verified current company hiring specifications.
