import React, { Suspense, lazy } from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { AuthProvider, Empty, Loading, Protected, Shell } from "./shared";
import { AuthPage, Onboarding, SettingsPage } from "./pages/Account";
import {
  Landing,
  Dashboard,
  Companies,
  CompanyPage,
  Instructions,
  Practice,
  CodingList,
  Bookmarks,
  HistoryPage,
  AnalyticsPage,
} from "./pages/Workspace";
import { ResultPage } from "./pages/Result";
import { AdminPage } from "./pages/Admin";
import "./styles.css";
import Learning from "./pages/Learning";
import { MotionProvider } from "./components/Motion";
const AttemptPage = lazy(() => import("./pages/Attempt"));
const CodingPage = lazy(() => import("./pages/Coding"));
const saved = localStorage.getItem("prepforge-theme") || "system";
document.documentElement.dataset.theme =
  saved === "system"
    ? matchMedia("(prefers-color-scheme: dark)").matches
      ? "dark"
      : "light"
    : saved;
matchMedia("(prefers-color-scheme: dark)").addEventListener("change", (e) => {
  if ((localStorage.getItem("prepforge-theme") || "system") === "system")
    document.documentElement.dataset.theme = e.matches ? "dark" : "light";
});
ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <MotionProvider>
        <AuthProvider>
          <Suspense fallback={<Loading />}>
            <Routes>
              <Route path="/" element={<Landing />} />
              {[
                "login",
                "signup",
                "forgot-password",
                "reset-password",
                "verify-email",
              ].map((p) => (
                <Route key={p} path={"/" + p} element={<AuthPage mode={p} />} />
              ))}
              <Route element={<Protected />}>
                <Route path="/onboarding" element={<Onboarding />} />
                <Route path="/attempt/:id" element={<AttemptPage />} />
                <Route element={<Shell />}>
                  <Route path="/dashboard" element={<Dashboard />} />
                  <Route path="/learn" element={<Learning />} />
                  <Route path="/companies" element={<Companies />} />
                  <Route path="/companies/:slug" element={<CompanyPage />} />
                  <Route path="/tracks/:id" element={<Instructions />} />
                  <Route
                    path="/assessment/:id/instructions"
                    element={<Instructions />}
                  />
                  <Route path="/attempt/:id/result" element={<ResultPage />} />
                  <Route path="/history" element={<HistoryPage />} />
                  <Route path="/analytics" element={<AnalyticsPage />} />
                  <Route path="/practice" element={<Practice />} />
                  <Route path="/coding" element={<CodingList />} />
                  <Route path="/coding/:slug" element={<CodingPage />} />
                  <Route path="/bookmarks" element={<Bookmarks />} />
                  <Route path="/profile" element={<Onboarding embedded />} />
                  <Route path="/settings" element={<SettingsPage />} />
                  <Route element={<Protected admin />}>
                    <Route path="/admin" element={<AdminPage />} />
                  </Route>
                </Route>
              </Route>
              <Route
                path="*"
                element={
                  <Empty
                    title="Page not found"
                    text="This page may have moved. Return to your dashboard."
                    action={
                      <a className="btn" href="/dashboard">
                        Go to dashboard
                      </a>
                    }
                  />
                }
              />
            </Routes>
          </Suspense>
        </AuthProvider>
      </MotionProvider>
    </BrowserRouter>
  </React.StrictMode>,
);
