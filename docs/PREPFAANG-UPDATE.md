# PrepFaang update

The visible product name, header logo and favicon now use PrepFaang. Existing cookie, recovery-storage and local database identifiers are retained for compatibility.

The local ignored `.env` is configured for the supplied Atlas connection, database `prepForge`, users collection `user_details`, and Gmail STARTTLS SMTP. Credentials are excluded from the source archive. Atlas authentication and SMTP authentication succeeded; no email was sent during connection checks. Existing SQLite records were imported using insert-only upserts; existing remote records and the SQLite source were retained.

## Learning and assessments

- Choose 25, 50 or 75 questions from the Learning library or company instructions.
- Each set divides equally among Quants, Logical Reasoning, Verbal Ability, Data Interpretation and Psychometric Reflection.
- Reflection questions are unscored, have no correct answer and are excluded from score, accuracy and weak-topic metrics. They are not a validated psychological assessment.
- 195 original items were added: 180 scored MCQs and 15 reflection prompts. Combined bank: 252 items, including six coding challenges.
- 23 original short lessons include rules and worked examples. Questions vary by difficulty and are selected without replacement within each attempt.
- Choose the original company pattern to retain its technical/coding section mix.
- Public PrepInsta category pages informed category organization only. The proprietary app and full question corpus have not been copied or reproduced.

## Verification

- Backend: 12 tests passed; eight Docker-dependent cases skipped because the sandbox is unavailable.
- Atlas: six integration cases passed in isolated temporary databases, covering accounts, ownership, expiry, recovery, all mixed sizes, reflection scoring, CSRF/roles/reset tokens, atomic imports, negative marking and rate limiting. Tests mock mail delivery and remove only their own temporary databases.
- Frontend: three unit tests, ESLint, TypeScript and production build passed. Monaco retains a bundle-size warning.
- The new learning page passed overflow checks at 320, 390, 768 and 1440 pixels; its screenshot was visually inspected.
- Real Docker execution and actual SMTP message delivery remain unverified. SMTP authentication alone does not establish deliverability.

`VALIDATION.md` records the earlier base-build checks; this file records the current MongoDB/PrepFaang update.

## Setup

Keep the configured local `.env`. For a fresh checkout, copy `.env.example` and supply your own credentials. Run `python -m app.bootstrap` from `backend/` to initialize the selected database and seed original content. MongoDB uses transactions and requires Atlas or a replica set; SQL uses Alembic. Compose now respects `.env` rather than overriding the connection with PostgreSQL.

Use `python -m app.check_connections` for credential-safe connection checks. For isolated Atlas integration tests set `TEST_MONGO=1` before pytest; the account must be able to create and drop temporary test databases. Browser email verification is opt-in with `TEST_DEV_MAIL_ONLY=1` and must use a backend with SMTP disabled.

The final Chromium mixed-assessment journey passed in 23.6 seconds against Atlas: signup, learning tabs, 25/50/75 previews, responsive checks, 75-question creation, autosave, reload with preserved expiry, reflection response and final result. Batch option/snapshot and answer loading removed per-question network round trips. The combined legacy browser suite was blocked by automatic approval review due to its email-verification path; only the mail-free mixed journey was rerun for this update.
