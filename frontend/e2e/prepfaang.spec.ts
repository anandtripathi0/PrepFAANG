import { test, expect } from "@playwright/test";

test("PrepFaang mixed learning, 75 questions, autosave and reflection results", async ({
  page,
}) => {
  test.setTimeout(120000);
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/signup");
  await page.getByLabel("Full name", { exact: true }).fill("Mixed Learner");
  await page
    .getByLabel("Email address")
    .fill(`mixed-${Date.now()}@example.com`);
  await page
    .getByLabel("Password", { exact: true })
    .fill("Strong-passphrase-123");
  await page.getByRole("button", { name: "Create account" }).click();
  await expect(page).toHaveURL(/onboarding/);
  await page.getByRole("link", { name: "Skip for now" }).click();
  await page
    .getByRole("link", { name: "Learning library", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Your preparation library" }),
  ).toBeVisible();
  await expect(page.locator(".brand")).toContainText("PrepFaang");
  for (const count of [25, 50, 75]) {
    await page
      .getByRole("button", { name: `${count} questions`, exact: true })
      .click();
    await expect(
      page.getByText(`${count / 5} questions per area`, { exact: false }),
    ).toBeVisible();
  }
  for (const width of [320, 390, 768, 1440]) {
    await page.setViewportSize({ width, height: 1000 });
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBeTruthy();
  }
  await page.screenshot({
    path: "../docs/prepfaang-learning.png",
    fullPage: true,
  });
  await page
    .getByRole("tab", { name: "Data interpretation", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Tables and totals" }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Start 75-question assessment" })
    .click();
  await expect(page).toHaveURL(/\/attempt\/[a-f0-9-]+$/);
  const id = page.url().split("/").pop();
  const before = await (await page.request.get("/api/attempts/" + id)).json();
  expect(before.questions).toHaveLength(75);
  await page.getByRole("radio").first().click();
  await expect(page.getByText("All changes saved")).toBeVisible();
  await page.reload();
  const after = await (await page.request.get("/api/attempts/" + id)).json();
  expect(after.expires_at).toBe(before.expires_at);
  expect(after.questions[0].answer.selected).toBe(0);
  await page
    .getByRole("button", {
      name: "Psychometric Reflection 15 questions",
      exact: true,
    })
    .click();
  await page.getByRole("radio").first().click();
  await expect(page.getByText("All changes saved")).toBeVisible();
  await page.getByRole("button", { name: "Submit test", exact: true }).click();
  await page.getByRole("button", { name: "Confirm submission" }).click();
  await expect(page).toHaveURL(/\/result$/);
  await expect(
    page.getByText("Assessment complete", { exact: true }),
  ).toBeVisible();
  await page.screenshot({
    path: "../docs/prepfaang-result.png",
    fullPage: true,
  });
  expect(errors).toEqual([]);
});
