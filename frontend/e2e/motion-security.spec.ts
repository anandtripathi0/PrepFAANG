import { test, expect } from "@playwright/test";

test("motion preferences and account security with Atlas persistence", async ({
  page,
  browser,
}) => {
  test.setTimeout(120000);
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto("/");
  await expect(
    page.getByRole("button", { name: "Pause animations", exact: true }),
  ).toBeVisible();
  await expect(page.locator("html")).toHaveAttribute("data-motion", "running");
  expect(
    await page
      .locator(".hero-orbit-one")
      .evaluate((el) => getComputedStyle(el).animationName),
  ).toBe("ambient-orbit");
  for (const width of [320, 390, 768, 1440]) {
    await page.setViewportSize({ width, height: 1000 });
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBeTruthy();
  }
  await page.screenshot({ path: "../docs/motion-landing.png", fullPage: true });
  await page
    .getByRole("button", { name: "Pause animations", exact: true })
    .click();
  await expect(page.locator("html")).toHaveAttribute("data-motion", "paused");
  expect(
    await page
      .locator(".hero-orbit-one")
      .evaluate((el) => getComputedStyle(el).animationPlayState),
  ).toBe("paused");
  await page.reload();
  await expect(
    page.getByRole("button", { name: "Enable animations", exact: true }),
  ).toBeVisible();
  await page.emulateMedia({ reducedMotion: "reduce" });
  await expect(
    page.getByRole("button", { name: "Reduced motion enabled by your device" }),
  ).toBeDisabled();
  expect(
    await page
      .locator(".hero-orbit-one")
      .evaluate((el) => getComputedStyle(el).animationName),
  ).toBe("none");
  await page.emulateMedia({ reducedMotion: "no-preference" });
  await page
    .getByRole("button", { name: "Enable animations", exact: true })
    .click();

  const email = `security-${Date.now()}@example.com`;
  const password = "Strong-passphrase-123";
  const changed = "Updated-passphrase-456";
  await page.goto("/signup");
  await page.getByLabel("Full name", { exact: true }).fill("Security Learner");
  await page.getByLabel("Email address").fill(email);
  await page.getByLabel("Password", { exact: true }).fill(password);
  await page.getByRole("button", { name: "Create account" }).click();
  await expect(page).toHaveURL(/onboarding/);
  await page.getByRole("link", { name: "Skip for now" }).click();
  await page.getByRole("link", { name: "Settings", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Change your password" }),
  ).toBeVisible();
  const second = await browser.newContext();
  expect(
    (
      await second.request.post("/api/auth/login", {
        data: { email, password },
      })
    ).status(),
  ).toBe(200);
  await page.screenshot({
    path: "../docs/security-settings.png",
    fullPage: true,
  });
  await page.getByLabel("Current password", { exact: true }).fill(password);
  await page.getByLabel("New password", { exact: true }).fill(changed);
  await page
    .getByLabel("Confirm new password", { exact: true })
    .fill("Does-not-match-123");
  await page
    .getByRole("button", { name: "Change password", exact: true })
    .click();
  await expect(page.getByRole("alert")).toContainText("do not match");
  await page.getByLabel("Confirm new password", { exact: true }).fill(changed);
  await page
    .getByRole("button", { name: "Change password", exact: true })
    .click();
  await expect(page).toHaveURL(/login/);
  await expect(page.getByRole("status")).toContainText("Password changed");
  expect((await second.request.get("/api/auth/me")).status()).toBe(401);
  await page.getByLabel("Email address").fill(email);
  await page.getByLabel("Password", { exact: true }).fill(changed);
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(page).toHaveURL(/dashboard/);
  expect(
    (
      await second.request.post("/api/auth/login", {
        data: { email, password: changed },
      })
    ).status(),
  ).toBe(200);
  await page.goto("/settings");
  await page.getByRole("button", { name: "Sign out everywhere" }).click();
  await expect(page).toHaveURL(/login/);
  expect((await second.request.get("/api/auth/me")).status()).toBe(401);
  await second.close();
  expect(errors).toEqual([]);
});
