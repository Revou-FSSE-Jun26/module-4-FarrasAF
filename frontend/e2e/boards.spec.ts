import {
  addTeamMemberToBoard,
  createBoardScenario,
  createCard,
  createTeam,
  expect,
  loginInBrowser,
  test,
  uniqueId,
} from "./fixtures";

const DEFAULT_COLUMNS = ["To Do", "Doing", "Done"];

test.describe("board, column, and card CRUD", () => {
  test("creates a Board with the default Columns", async ({
    page,
    context,
    makeUser,
  }) => {
    const owner = await makeUser("Board Creator");
    await createTeam(owner);
    await loginInBrowser(context, owner);
    const boardName = `Board ${uniqueId()}`;

    await page.goto("/boards");
    // The Team list loads asynchronously; wait until the select has an option.
    await expect(page.getByLabel("Team").getByRole("option")).toHaveCount(1);
    await page.getByLabel("Board name").fill(boardName);
    await page.getByRole("button", { name: "Create Board" }).click();
    await page.getByRole("link", { name: boardName }).click();

    await expect(page.getByRole("heading", { name: boardName })).toBeVisible();
    for (const name of DEFAULT_COLUMNS) {
      await expect(page.getByRole("region", { name })).toBeVisible();
    }
    await expect(page.getByRole("button", { name: "Add column" })).toBeVisible();
  });

  test("Admin adds, renames, and deletes an empty Column", async ({
    page,
    context,
    baseURL,
  }) => {
    const { admin, board } = await createBoardScenario(baseURL ?? "");
    await loginInBrowser(context, admin);
    const added = `Review ${uniqueId()}`;
    const renamed = `QA ${uniqueId()}`;

    await page.goto(`/boards/${board.id}`);
    await page.getByLabel("Column name").fill(added);
    await page.getByRole("button", { name: "Add column" }).click();
    await expect(page.getByRole("region", { name: added })).toBeVisible();

    await page.getByRole("button", { name: `Rename ${added}` }).click();
    await page.getByLabel("Column name").first().fill(renamed);
    await page.getByRole("button", { name: "Save" }).click();
    await expect(page.getByRole("region", { name: renamed })).toBeVisible();
    await expect(page.getByRole("region", { name: added })).toHaveCount(0);

    await page.getByRole("button", { name: `Delete ${renamed}` }).click();
    await page
      .getByRole("dialog")
      .getByRole("button", { name: "Delete", exact: true })
      .click();
    await expect(page.getByRole("region", { name: renamed })).toHaveCount(0);
  });

  test("rejects deleting a Column that still has Cards", async ({
    page,
    context,
    baseURL,
  }) => {
    const { admin, board } = await createBoardScenario(baseURL ?? "");
    const todo = board.columns.find((c) => c.name === "To Do");
    if (!todo) throw new Error("default To Do column missing");
    await createCard(admin, todo.id, "Keep me");
    await loginInBrowser(context, admin);

    await page.goto(`/boards/${board.id}`);
    await page.getByRole("button", { name: "Delete To Do" }).click();
    await page
      .getByRole("dialog")
      .getByRole("button", { name: "Delete", exact: true })
      .click();

    await expect(page.getByRole("alert")).toBeVisible();
    const column = page.getByRole("region", { name: "To Do" });
    await expect(column).toBeVisible();
    await expect(column.getByText("Keep me")).toBeVisible();
  });

  test("creates, edits, assigns, and deletes a Card", async ({
    page,
    context,
    baseURL,
  }) => {
    const scenario = await createBoardScenario(baseURL ?? "");
    const member = await addTeamMemberToBoard(
      scenario,
      baseURL ?? "",
      "Assignee Person",
    );
    await loginInBrowser(context, scenario.admin);
    const title = `Task ${uniqueId()}`;
    const edited = `${title} edited`;
    const todo = page.getByRole("region", { name: "To Do" });

    await page.goto(`/boards/${scenario.board.id}`);
    await todo.getByRole("button", { name: "Add card to To Do" }).click();
    await todo.getByLabel("Card title").fill(title);
    await todo.getByRole("button", { name: "Add", exact: true }).click();
    await expect(todo.getByText(title, { exact: true })).toBeVisible();

    await todo.getByText(title, { exact: true }).click();
    const dialog = page.getByRole("dialog", { name: "Card details" });
    await dialog.getByLabel("Title").fill(edited);
    await dialog.getByLabel("Description").fill("Details here");
    await dialog.getByLabel("Assignee").selectOption({ label: member.displayName });
    await dialog.getByLabel("Due date").fill("2030-01-15");
    await dialog.getByRole("button", { name: "Save", exact: true }).click();

    await expect(dialog).toHaveCount(0);
    const card = todo.getByTestId("card-item").filter({ hasText: edited });
    await expect(card).toBeVisible();
    await expect(card).toContainText("Due 2030-01-15");

    await card.click();
    const reopened = page.getByRole("dialog", { name: "Card details" });
    await expect(reopened.getByLabel("Description")).toHaveValue("Details here");
    await expect(reopened.getByLabel("Assignee")).toHaveValue(member.user.id);
    await reopened.getByRole("button", { name: "Delete card" }).click();
    await reopened.getByRole("button", { name: "Confirm delete" }).click();

    await expect(todo.getByText(edited)).toHaveCount(0);
    await expect(todo.getByText("No cards yet")).toBeVisible();
  });

  test("Admin archives a Board and restores it", async ({
    page,
    context,
    baseURL,
  }) => {
    const { admin, board } = await createBoardScenario(baseURL ?? "");
    await loginInBrowser(context, admin);

    await page.goto(`/boards/${board.id}/settings`);
    await page.getByRole("button", { name: "Archive Board" }).click();
    await expect(
      page.getByRole("button", { name: "Restore Board" }),
    ).toBeVisible();

    await page.goto("/boards");
    await expect(page.getByRole("link", { name: board.name })).toHaveCount(0);
    await page.getByRole("button", { name: "Show archived Boards" }).click();
    await expect(page.getByRole("link", { name: board.name })).toBeVisible();

    await page.goto(`/boards/${board.id}/settings`);
    await page.getByRole("button", { name: "Restore Board" }).click();
    await expect(
      page.getByRole("button", { name: "Archive Board" }),
    ).toBeVisible();

    await page.goto("/boards");
    await expect(page.getByRole("link", { name: board.name })).toBeVisible();
  });

  test("Member sees Card controls but no Column or lifecycle controls", async ({
    page,
    context,
    baseURL,
  }) => {
    const scenario = await createBoardScenario(baseURL ?? "");
    const member = await addTeamMemberToBoard(scenario, baseURL ?? "");
    await loginInBrowser(context, member);

    await page.goto(`/boards/${scenario.board.id}`);
    const todo = page.getByRole("region", { name: "To Do" });
    await expect(todo).toBeVisible();
    await expect(
      todo.getByRole("button", { name: "Add card to To Do" }),
    ).toBeVisible();
    await expect(page.getByRole("button", { name: "Add column" })).toHaveCount(
      0,
    );
    await expect(page.getByRole("button", { name: "Rename To Do" })).toHaveCount(
      0,
    );
    await expect(page.getByRole("button", { name: "Delete To Do" })).toHaveCount(
      0,
    );

    await page.goto(`/boards/${scenario.board.id}/settings`);
    await expect(
      page.getByText("Only Board admins can change these settings."),
    ).toBeVisible();
    await expect(
      page.getByRole("button", { name: "Archive Board" }),
    ).toHaveCount(0);
    await expect(
      page.getByRole("button", { name: "Delete Board" }),
    ).toHaveCount(0);
  });
});
