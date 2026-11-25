import type { Locator, Page } from "@playwright/test";
import {
  createBoardScenario,
  createCard,
  expect,
  loginInBrowser,
  test,
} from "./fixtures";

/** Drags with real pointer events in small steps so dnd-kit's PointerSensor activates. */
async function dragTo(
  page: Page,
  source: Locator,
  target: Locator,
  position: "top" | "center" = "center",
): Promise<void> {
  const from = await source.boundingBox();
  const to = await target.boundingBox();
  if (!from || !to) throw new Error("drag source or target is not visible");
  const toY = position === "top" ? to.y + 2 : to.y + to.height / 2;
  await page.mouse.move(from.x + from.width / 2, from.y + from.height / 2);
  await page.mouse.down();
  await page.mouse.move(from.x + from.width / 2 + 10, from.y + 10, {
    steps: 5,
  });
  await page.mouse.move(to.x + to.width / 2, toY, { steps: 20 });
  await page.mouse.up();
}

async function cardTitles(column: Locator): Promise<string[]> {
  return column
    .getByTestId("card-item")
    .locator("p.font-medium")
    .allTextContents();
}

test.describe("drag and drop", () => {
  test("moves a Card to another Column and the order persists after reload", async ({
    page,
    context,
    baseURL,
  }) => {
    const { admin, board } = await createBoardScenario(baseURL ?? "");
    const todoCol = board.columns.find((c) => c.name === "To Do");
    if (!todoCol) throw new Error("default To Do column missing");
    await createCard(admin, todoCol.id, "Alpha");
    await createCard(admin, todoCol.id, "Beta");
    await loginInBrowser(context, admin);

    await page.goto(`/boards/${board.id}`);
    const todo = page.getByRole("region", { name: "To Do" });
    const doing = page.getByRole("region", { name: "Doing" });
    await expect(todo.getByText("Beta", { exact: true })).toBeVisible();

    const moved = page.waitForResponse(
      (r) => r.url().includes("/move") && r.request().method() !== "GET",
    );
    await dragTo(
      page,
      todo.getByTestId("card-item").filter({ hasText: "Alpha" }),
      doing.getByText("No cards yet"),
    );
    expect((await moved).ok()).toBe(true);

    await expect(doing.getByText("Alpha", { exact: true })).toBeVisible();
    await expect(todo.getByText("Alpha", { exact: true })).toHaveCount(0);

    await page.reload();
    const todoAfter = page.getByRole("region", { name: "To Do" });
    const doingAfter = page.getByRole("region", { name: "Doing" });
    await expect(doingAfter.getByText("Alpha", { exact: true })).toBeVisible();
    expect(await cardTitles(doingAfter)).toEqual(["Alpha"]);
    expect(await cardTitles(todoAfter)).toEqual(["Beta"]);
  });

  test("reorders Cards within a Column and the order persists after reload", async ({
    page,
    context,
    baseURL,
  }) => {
    const { admin, board } = await createBoardScenario(baseURL ?? "");
    const todoCol = board.columns.find((c) => c.name === "To Do");
    if (!todoCol) throw new Error("default To Do column missing");
    for (const title of ["First", "Second", "Third"]) {
      await createCard(admin, todoCol.id, title);
    }
    await loginInBrowser(context, admin);

    await page.goto(`/boards/${board.id}`);
    const todo = page.getByRole("region", { name: "To Do" });
    await expect(todo.getByTestId("card-item")).toHaveCount(3);
    expect(await cardTitles(todo)).toEqual(["First", "Second", "Third"]);

    const moved = page.waitForResponse(
      (r) => r.url().includes("/move") && r.request().method() !== "GET",
    );
    await dragTo(
      page,
      todo.getByTestId("card-item").filter({ hasText: "Third" }),
      todo.getByTestId("card-item").filter({ hasText: "First" }),
      "top",
    );
    expect((await moved).ok()).toBe(true);
    await expect
      .poll(() => cardTitles(todo))
      .toEqual(["Third", "First", "Second"]);

    await page.reload();
    const todoAfter = page.getByRole("region", { name: "To Do" });
    await expect(todoAfter.getByTestId("card-item")).toHaveCount(3);
    expect(await cardTitles(todoAfter)).toEqual(["Third", "First", "Second"]);
  });
});
