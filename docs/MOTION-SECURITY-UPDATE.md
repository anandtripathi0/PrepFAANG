# Animation, account security and MongoDB update — 23 September 2026

## Website motion

The landing page has slowly orbiting paths and floating preparation icons. The dashboard adds subtle target motion, page entrances and card/button feedback. The loading indicator uses the PrepFaang logo. Motion is decorative and never represents fabricated activity or performance.

Pause animations using the control on the landing page or workspace header. The preference persists locally. Device reduced-motion settings take precedence, and background tabs pause decorative loops. Timed assessments have no decorative loops.

## Authentication

Settings now provides a current-password-verified password change and a Sign out everywhere action. A password change revokes every session and outstanding verification/reset token. Password resets also invalidate all previously issued links. Failed changes leave sessions intact. These actions require the session CSRF token; password changes are rate limited. Cross-site browser mutations are rejected.

The existing Argon2 password hashes, opaque HttpOnly session cookies, protected routes, ownership checks and administrator roles remain in place. Production cookies require HTTPS and are Secure. SMTP STARTTLS now validates the server certificate and hostname using the system trust store.

The Compose backend has no published port. nginx replaces client forwarding headers and the backend trusts forwarding only in this private deployment topology. If publishing the backend or using a different proxy network, replace wildcard `FORWARDED_ALLOW_IPS` with the explicit trusted proxy addresses. Docker deployment has not been exercised on this machine.

## MongoDB

Atlas remains the configured persistence layer: `prepForge`, with users in `user_details`. Configuration loads from the project's `.env` using an absolute path so importing the app from another working directory cannot silently lose its connection settings. No existing user data was replaced.

Atlas authentication and Gmail SMTP authentication succeeded, including certificate verification. No real emails were sent. Credentials remain out of source files; the configured private archive deliberately includes `.env` for the project owner's use.

## Verification

- Backend: 17 tests passed, eight Docker-only checks skipped.
- Live Atlas: three new integration cases passed using isolated temporary databases. They verify password-change session/link revocation, sign-out across devices without affecting another user, and invalidation of older reset links. Test email delivery is mocked.
- Frontend: TypeScript, ESLint and three unit tests passed.

- Production Vite build passed; the pre-existing lazy Monaco chunk-size warning remains.
- Chromium journey passed against Atlas: real signup/login, two concurrent browser sessions, password change, confirmation redirect and sign-out everywhere. No mail-sending routes were exercised.
- Animation pause persists after reload; device reduced motion disables loops. Landing overflow checks passed at 320, 390, 768 and 1440px. Landing and security Settings screenshots were inspected.
- Docker execution and actual email delivery are still unverified.
