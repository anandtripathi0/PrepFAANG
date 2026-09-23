import { test, expect } from "@playwright/test";

test("registration, onboarding, assessment, autosave, recovery, results, isolation and responsive layout", async ({
  page,
  browser,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  const email = `journey-${Date.now()}@example.com`;
  await page.goto("/signup");
  await page.getByLabel("Full name", { exact: true }).fill("Alex Morgan");
  await page.getByLabel("Email address").fill(email);
  await page
    .getByLabel("Password", { exact: true })
    .fill("Strong-passphrase-123");
  await page.getByRole("button", { name: "Create account" }).click();
  await expect(page).toHaveURL(/onboarding/);
  await page.getByLabel("College", { exact: true }).fill("Example Institute");
  await page.getByLabel("Target companies").fill("Google, TCS");
  await page.getByRole("button", { name: "Build my workspace" }).click();
  await expect(
    page.getByRole("heading", { name: "Welcome back, Alex." }),
  ).toBeVisible();
  await expect(page.getByText("No tests attempted yet.")).toBeVisible();
  for (const width of [320, 360, 375, 390, 414, 768, 1024, 1280, 1440, 1920]) {
    await page.setViewportSize({ width, height: 1000 });
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= window.innerWidth,
      ),
    ).toBeTruthy();
  }
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.screenshot({ path: "../docs/dashboard.png", fullPage: true });
  await page
    .getByRole("link", { name: "Company explorer", exact: true })
    .click();
  await page.getByLabel("Search companies").fill("Google");
  await page
    .getByRole("link")
    .filter({ has: page.getByRole("heading", { name: "Google", exact: true }) })
    .click();
  await page
    .getByRole("link")
    .filter({
      has: page.getByRole("heading", {
        name: "Software Engineer",
        exact: true,
      }),
    })
    .click();
  await page.getByLabel("Assessment question count").selectOption("0");
  await page.getByRole("button", { name: /moderate Find your rhythm/ }).click();
  await page
    .getByRole("button", { name: "Start assessment", exact: true })
    .click();
  await expect(page).toHaveURL(/\/attempt\/[a-f0-9-]+$/);
  const attemptUrl = page.url();
  const aid = attemptUrl.split("/").pop()!;
  const before = await (await page.request.get("/api/attempts/" + aid)).json();
  await page.getByRole("radio").first().click();
  await expect(page.getByText("All changes saved")).toBeVisible();
  await page
    .getByRole("button", { name: "Mark for review", exact: true })
    .click();
  await expect(page.getByText("All changes saved")).toBeVisible();
  await page.getByRole("button", { name: "Save & next" }).click();
  await page.reload();
  await expect(page.getByText("QUESTION 2 OF 8")).toBeVisible();
  const after = await (await page.request.get("/api/attempts/" + aid)).json();
  expect(after.expires_at).toBe(before.expires_at);
  expect(after.questions[0].answer.selected).toBe(0);
  expect(after.questions[0].answer.marked).toBe(true);
  await page
    .getByRole("button", { name: "Coding 1 questions", exact: true })
    .click();
  await expect(page.locator(".monaco-editor").first()).toBeVisible();
  await page.getByRole("button", { name: "Run examples" }).click();
  await expect(page.locator(".error[role=alert]")).toContainText(
    "isolated code runner is unavailable",
  );
  // This machine has no Docker. Verify an honest execution error, never a fabricated pass.
  await page.getByRole("button", { name: "Submit code", exact: true }).click();
  await expect(page.locator(".error[role=alert]")).toContainText(
    "isolated code runner is unavailable",
  );
  await page.getByRole("button", { name: "Submit test", exact: true }).click();
  await page.getByRole("button", { name: "Confirm submission" }).click();
  await expect(page).toHaveURL(/\/result$/);
  await expect(
    page.getByText("Assessment complete", { exact: true }),
  ).toBeVisible();
  await page.screenshot({ path: "../docs/result.png", fullPage: true });
  await page.getByRole("link", { name: "Test history", exact: true }).click();
  await expect(page.getByRole("link", { name: "View result" })).toHaveCount(1);
  await page.getByRole("link", { name: "Analytics", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Score over time" }),
  ).toBeVisible();
  const second = await browser.newContext();
  const secondPage = await second.newPage();
  await secondPage.goto("/signup");
  await secondPage
    .getByLabel("Full name", { exact: true })
    .fill("Second Learner");
  await secondPage
    .getByLabel("Email address")
    .fill(`second-${Date.now()}@example.com`);
  await secondPage
    .getByLabel("Password", { exact: true })
    .fill("Strong-passphrase-123");
  await secondPage.getByRole("button", { name: "Create account" }).click();
  await expect(secondPage).toHaveURL(/onboarding/);
  expect((await secondPage.request.get("/api/attempts/" + aid)).status()).toBe(
    404,
  );
  expect(
    (await (await secondPage.request.get("/api/history")).json()).total,
  ).toBe(0);
  expect(
    (await (await secondPage.request.get("/api/analytics")).json()).attempts,
  ).toBe(0);
  await second.close();
  await page.getByRole("button", { name: "Sign out", exact: true }).click();
  await page.goto(attemptUrl);
  await expect(page).toHaveURL(/login/);
  await page.getByLabel("Email address").fill(email);
  await page
    .getByLabel("Password", { exact: true })
    .fill("Strong-passphrase-123");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(page).toHaveURL(/\/result$/);
  expect(errors).toEqual([]);
});
