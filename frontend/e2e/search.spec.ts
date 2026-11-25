import {
  createBoardScenario,
  createCard,
  expect,
  loginInBrowser,
  test,
  uniqueId,
} from "./fixtures";

test.describe("card search", () => {
  test("finds Cards by case-insensitive title and shows Board and Column", async ({
    page,
    context,
    baseURL,
  }) => {
    const scenario = await createBoardScenario(baseURL ?? "");
    const doing = scenario.board.columns.find((c) => c.name === "Doing");
    const todo = scenario.board.columns.find((c) => c.name === "To Do");
    if (!doing || !todo) throw new Error("default columns missing");

    const token = `zq${uniqueId()}`;
    const firstTitle = `Alpha ${token} task`;
    const secondTitle = `Beta ${token.toUpperCase()} work`;
    const otherTitle = `Unrelated ${uniqueId()}`;
    await createCard(scenario.admin, todo.id, firstTitle);
    await createCard(scenario.admin, doing.id, secondTitle);
    await createCard(scenario.admin, todo.id, otherTitle);

    await loginInBrowser(context, scenario.admin);
    await page.goto("/search");
    await page.getByLabel("Card title keyword").fill(token.toUpperCase());
    await page.getByRole("button", { name: "Search", exact: true }).click();

    const results = page.getByRole("listitem");
    await expect(results).toHaveCount(2);
    const first = results.filter({ hasText: firstTitle });
    const second = results.filter({ hasText: secondTitle });
    await expect(first).toContainText(scenario.board.name);
    await expect(first).toContainText("To Do");
    await expect(second).toContainText(scenario.board.name);
    await expect(second).toContainText("Doing");
    await expect(page.getByText(otherTitle)).toHaveCount(0);
  });

  test("shows an empty state when no Card matches", async ({
    page,
    context,
    baseURL,
  }) => {
    const scenario = await createBoardScenario(baseURL ?? "");
    await loginInBrowser(context, scenario.admin);
    const keyword = `nomatch${uniqueId()}`;

    await page.goto("/search");
    await page.getByLabel("Card title keyword").fill(keyword);
    await page.getByRole("button", { name: "Search", exact: true }).click();

    await expect(page.getByText(`No Cards match "${keyword}".`)).toBeVisible();
    await expect(page.getByRole("listitem")).toHaveCount(0);
  });

  test("rejects a blank keyword", async ({ page, context, baseURL }) => {
    const scenario = await createBoardScenario(baseURL ?? "");
    await loginInBrowser(context, scenario.admin);

    await page.goto("/search");
    await page.getByLabel("Card title keyword").fill("   ");
    await page.getByRole("button", { name: "Search", exact: true }).click();

    await expect(page.getByText("Enter a keyword to search.")).toBeVisible();
    await expect(page.getByText(/No Cards match/)).toHaveCount(0);
    await expect(page.getByRole("listitem")).toHaveCount(0);
  });
});
