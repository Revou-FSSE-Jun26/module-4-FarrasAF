import {
  createTeam,
  expect,
  loginInBrowser,
  loginThroughUi,
  test,
  uniqueId,
} from "./fixtures";

const GENERIC_LOGIN_ERROR = "Invalid email or password.";
const NEW_PASSWORD = "New-E2e-Password-456!";

test.describe("profile", () => {
  test("changes the display name and shows it in the app shell and on the Team members page", async ({
    page,
    context,
    makeUser,
  }) => {
    const user = await makeUser("Before Name");
    const team = await createTeam(user);
    await loginInBrowser(context, user);
    const newName = `After ${uniqueId()}`;

    await page.goto("/profile");
    await page.getByLabel("Display name").fill(newName);
    await page.getByRole("button", { name: "Save display name" }).click();

    await expect(page.getByText("Display name updated.")).toBeVisible();
    await expect(
      page.getByRole("banner").getByText(newName, { exact: true }),
    ).toBeVisible();

    await page.goto(`/teams/${team.id}`);
    await expect(
      page.getByRole("list").getByText(newName, { exact: true }),
    ).toBeVisible();
  });

  test("shows an inline error for a blank display name", async ({
    page,
    context,
    makeUser,
  }) => {
    const user = await makeUser("Keep Name");
    await loginInBrowser(context, user);

    await page.goto("/profile");
    await page.getByLabel("Display name").fill("   ");
    await page.getByRole("button", { name: "Save display name" }).click();

    await expect(
      page.getByText("Display name must be 1 to 50 characters."),
    ).toBeVisible();
    await expect(
      page.getByRole("banner").getByText("Keep Name", { exact: true }),
    ).toBeVisible();
  });

  test("changes the password and stays logged in", async ({
    page,
    context,
    makeUser,
  }) => {
    const user = await makeUser("Stay Logged");
    await loginInBrowser(context, user);

    await page.goto("/profile");
    await page.getByLabel("Current password").fill(user.password);
    await page.getByLabel("New password", { exact: true }).fill(NEW_PASSWORD);
    await page.getByLabel("Confirm new password").fill(NEW_PASSWORD);
    await page.getByRole("button", { name: "Change password" }).click();

    await expect(page.getByText("Password changed.")).toBeVisible();
    await page.goto("/boards");
    await expect(page).toHaveURL(/\/boards/);
    await expect(
      page.getByRole("banner").getByText("Stay Logged"),
    ).toBeVisible();
  });

  test("logs in with the new password after logout and rejects the old one", async ({
    page,
    context,
    makeUser,
  }) => {
    const user = await makeUser("Relogin User");
    await loginInBrowser(context, user);

    await page.goto("/profile");
    await page.getByLabel("Current password").fill(user.password);
    await page.getByLabel("New password", { exact: true }).fill(NEW_PASSWORD);
    await page.getByLabel("Confirm new password").fill(NEW_PASSWORD);
    await page.getByRole("button", { name: "Change password" }).click();
    await expect(page.getByText("Password changed.")).toBeVisible();

    await page.getByRole("button", { name: "Log out" }).click();
    await expect(page).toHaveURL(/\/login/);

    await page.getByLabel("Email").fill(user.email);
    await page.getByLabel("Password").fill(user.password);
    await page.getByRole("button", { name: "Log in" }).click();
    await expect(page.getByText(GENERIC_LOGIN_ERROR)).toBeVisible();
    await expect(page).toHaveURL(/\/login/);

    await loginThroughUi(page, user.email, NEW_PASSWORD);
    await expect(page).toHaveURL(/\/boards/);
    await expect(
      page.getByRole("banner").getByText("Relogin User"),
    ).toBeVisible();
  });

  test("shows an inline error for a wrong current password", async ({
    page,
    context,
    makeUser,
  }) => {
    const user = await makeUser("Wrong Current");
    await loginInBrowser(context, user);

    await page.goto("/profile");
    await page.getByLabel("Current password").fill("Not-The-Password-1!");
    await page.getByLabel("New password", { exact: true }).fill(NEW_PASSWORD);
    await page.getByLabel("Confirm new password").fill(NEW_PASSWORD);
    await page.getByRole("button", { name: "Change password" }).click();

    await expect(page.getByLabel("Current password")).toHaveAttribute(
      "aria-invalid",
      "true",
    );
    await expect(page.getByText("Password changed.")).toHaveCount(0);
  });

  test("redirects /profile to /login when logged out", async ({ page }) => {
    await page.goto("/profile");

    await expect(page).toHaveURL(/\/login/);
    await expect(page.getByRole("heading", { name: "Log in" })).toBeVisible();
  });
});
