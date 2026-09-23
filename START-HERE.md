# Run PrepFaang

If this is the configured private package, `.env` already contains your Atlas and Gmail settings. Keep that file and archive private. The public source package has only `.env.example`; copy it to `.env` and fill in your own credentials before running.

From the extracted `prepfaang` folder, open PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
cd backend
..\.venv\Scripts\python.exe -m app.bootstrap
..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

In another terminal, from the `prepfaang` folder:

```powershell
cd frontend
npm ci
npm run dev -- --port 5173
```

Open http://127.0.0.1:5173. Sign up or sign in with your existing account. Use **Settings** to change your password, sign out on every device, or send a verification email. Use **Forgot password** on the sign-in page to request a reset email.

Use the **Pause animations** control to disable decorative motion. Your device's reduced-motion setting is also respected.

The database is `prepForge`; users are in `user_details`. SMTP uses Gmail STARTTLS. Database connectivity and SMTP authentication were checked; actual email delivery is untested. Docker is required for executing submitted code; see README.md for that setup.
