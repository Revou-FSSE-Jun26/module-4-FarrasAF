import {
  DEFAULT_PASSWORD,
  expect,
  loginThroughUi,
  test,
  uniqueId,
} from "./fixtures";

const GENERIC_LOGIN_ERROR = "Invalid email or password.";

test.describe("authentication", () => {
  test("registers a new user and lands on the app", async ({ page }) => {
    const email = `e2e-${uniqueId()}@example.com`;

    await page.goto("/register");
    await page.getByLabel("Display name").fill("New Person");
    await page.getByLabel("Email").fill(email);
    await page.getByLabel("Password").fill(DEFAULT_PASSWORD);
    await page.getByRole("button", { name: "Register" }).click();

    await expect(page).toHaveURL(/\/boards/);
    await expect(page.getByText("New Person")).toBeVisible();
  });

  test("logs in with valid credentials", async ({ page, makeUser }) => {
    const user = await makeUser("Login User");

    await loginThroughUi(page, user.email, user.password);

    await expect(page).toHaveURL(/\/boards/);
    await expect(page.getByText("Login User")).toBeVisible();
  });

  test("shows the same generic error for wrong password and unknown email", async ({
    page,
    makeUser,
  }) => {
    const user = await makeUser();

    await page.goto("/login");
    await page.getByLabel("Email").fill(user.email);
    await page.getByLabel("Password").fill("Wrong-Password-999!");
    await page.getByRole("button", { name: "Log in" }).click();
    await expect(page.getByText(GENERIC_LOGIN_ERROR)).toBeVisible();
    await expect(page).toHaveURL(/\/login/);

    await page.getByLabel("Email").fill(`nobody-${uniqueId()}@example.com`);
    await page.getByLabel("Password").fill(DEFAULT_PASSWORD);
    await page.getByRole("button", { name: "Log in" }).click();
    await expect(page.getByText(GENERIC_LOGIN_ERROR)).toBeVisible();
    await expect(page).toHaveURL(/\/login/);
  });

  test("logs out and returns to the login page", async ({ page, makeUser }) => {
    const user = await makeUser();
    await loginThroughUi(page, user.email, user.password);

    await page.getByRole("button", { name: "Log out" }).click();

    await expect(page).toHaveURL(/\/login/);
    await page.goto("/boards");
    await expect(page).toHaveURL(/\/login/);
  });

  test("redirects an unauthenticated visitor from a protected route to /login", async ({
    page,
  }) => {
    await page.goto("/boards");

    await expect(page).toHaveURL(/\/login/);
    await expect(page.getByRole("heading", { name: "Enter your workspace" })).toBeVisible();
  });
});
