import {
  createBoardScenario,
  createCard,
  createInvitationLink,
  expect,
  revokeInvitationLink,
  test,
  uniqueId,
} from "./fixtures";

const UNAVAILABLE_MESSAGE = "This link is not available.";

test.describe("Guest access via Invitation Link", () => {
  test("anonymous visit shows the Board read-only with no write controls", async ({
    page,
    baseURL,
  }) => {
    const { admin, board } = await createBoardScenario(baseURL ?? "");
    const todo = board.columns.find((c) => c.name === "To Do");
    if (!todo) throw new Error("default To Do column missing");
    const title = `Guest card ${uniqueId()}`;
    await createCard(admin, todo.id, title);
    const link = await createInvitationLink(admin, board.id);

    // Fresh browser context: no cookies, so the visitor is anonymous.
    await page.goto(`/invite/${link.token}`);

    await expect(page.getByRole("heading", { name: board.name })).toBeVisible();
    await expect(page.getByText("Read-only guest view")).toBeVisible();
    for (const name of ["To Do", "Doing", "Done"]) {
      await expect(page.getByRole("region", { name })).toBeVisible();
    }
    await expect(
      page.getByRole("region", { name: "To Do" }).getByText(title),
    ).toBeVisible();

    await expect(page).not.toHaveURL(/\/login/);
    await expect(page.getByRole("button", { name: /add/i })).toHaveCount(0);
    await expect(page.getByRole("button", { name: /rename/i })).toHaveCount(0);
    await expect(page.getByRole("button", { name: /delete/i })).toHaveCount(0);
    await expect(page.getByTestId("card-item")).toHaveCount(0);
    await expect(page.getByRole("textbox")).toHaveCount(0);

    // Opening a Card shows details and comments, still without write controls.
    await page.getByRole("button", { name: title }).click();
    const dialog = page.getByRole("dialog");
    await expect(dialog.getByRole("heading", { name: "Comments" })).toBeVisible();
    await expect(dialog.getByText("No comments yet")).toBeVisible();
    await expect(dialog.getByRole("textbox")).toHaveCount(0);
    await expect(dialog.getByRole("button", { name: /save|delete|reply/i })).toHaveCount(0);
  });

  test("a revoked token shows the generic unavailable message", async ({
    page,
    baseURL,
  }) => {
    const { admin, board } = await createBoardScenario(baseURL ?? "");
    const link = await createInvitationLink(admin, board.id);
    await revokeInvitationLink(admin, link.token);

    await page.goto(`/invite/${link.token}`);

    await expect(page.getByText(UNAVAILABLE_MESSAGE)).toBeVisible();
    await expect(page.getByRole("heading", { name: board.name })).toHaveCount(0);
    await expect(page).not.toHaveURL(/\/login/);
  });

  test("an unknown token shows the same generic unavailable message", async ({
    page,
  }) => {
    await page.goto(`/invite/unknown-${uniqueId()}-token`);

    await expect(page.getByText(UNAVAILABLE_MESSAGE)).toBeVisible();
    await expect(page).not.toHaveURL(/\/login/);
  });
});
