import { test, expect } from "@playwright/test";
test("bookmarks, focused practice, themes, verification and mobile assessment", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/signup");
  await page.getByLabel("Full name", { exact: true }).fill("Feature Learner");
  await page
    .getByLabel("Email address")
    .fill(`features-${Date.now()}@example.com`);
  await page
    .getByLabel("Password", { exact: true })
    .fill("Strong-passphrase-123");
  await page.getByRole("button", { name: "Create account" }).click();
  await expect(page).toHaveURL(/onboarding/);
  await page.getByRole("link", { name: "Skip for now" }).click();
  await page.getByRole("link", { name: "Settings", exact: true }).click();
  await page.getByRole("button", { name: "dark", exact: true }).click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await page.reload();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await page.screenshot({ path: "../docs/dark-settings.png", fullPage: true });
  // Only exercise development email links against a backend with SMTP disabled.
  if (process.env.TEST_DEV_MAIL_ONLY === "1") {
    await page.getByRole("button", { name: "Send verification email" }).click();
    await page
      .getByRole("link", { name: "Open development email", exact: true })
      .click();
    await page
      .getByRole("button", { name: "Verify email", exact: true })
      .click();
    await expect(page.getByText("Your email is verified.")).toBeVisible();
  }
  await page.goto("/coding/array-total");
  await page.getByRole("button", { name: "Save problem", exact: true }).click();
  await expect(
    page.getByRole("button", { name: "Saved", exact: true }),
  ).toBeVisible();
  await page
    .getByRole("link", { name: "Saved questions", exact: true })
    .click();
  await expect(page).toHaveURL(/bookmarks/);
  await expect(
    page.getByRole("heading", { name: "Array total", exact: true, level: 3 }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Remove", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Your collection is waiting" }),
  ).toBeVisible();
  await page.goto("/practice");
  await page.getByLabel("Topic", { exact: true }).selectOption("SQL");
  await page.getByLabel("Difficulty", { exact: true }).selectOption("beginner");
  await page
    .getByRole("button", { name: "Start practice", exact: true })
    .click();
  await expect(page).toHaveURL(/\/attempt\/[a-f0-9-]+$/);
  await page.getByRole("radio").nth(2).click();
  await expect(page.getByText("All changes saved")).toBeVisible();
  for (const width of [320, 360, 375, 390, 414, 768, 1024, 1280, 1440, 1920]) {
    await page.setViewportSize({ width, height: 1000 });
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= window.innerWidth,
      ),
    ).toBeTruthy();
  }
  await page.setViewportSize({ width: 390, height: 844 });
  await page.screenshot({
    path: "../docs/mobile-assessment.png",
    fullPage: true,
  });
  await page.getByRole("button", { name: "Submit test", exact: true }).click();
  await page.getByRole("button", { name: "Confirm submission" }).click();
  await expect(page.getByText("100%").first()).toBeVisible();
  expect(errors).toEqual([]);
});
