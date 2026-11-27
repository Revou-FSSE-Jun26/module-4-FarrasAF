import type { Page } from "@playwright/test";
import {
  addTeamMemberToBoard,
  createBoardScenario,
  createCard,
  expect,
  loginInBrowser,
  test,
  uniqueId,
} from "./fixtures";
import type { BoardScenario } from "./fixtures";

// Notifications are polled every 30 s (useNotifications), so allow one full cycle.
const POLL_TIMEOUT_MS = 45_000;

interface OpenedCard {
  scenario: BoardScenario;
  title: string;
}

async function createScenarioWithCard(baseURL: string): Promise<OpenedCard> {
  const scenario = await createBoardScenario(baseURL);
  const todo = scenario.board.columns.find((c) => c.name === "To Do");
  if (!todo) throw new Error("default To Do column missing");
  const title = `Card ${uniqueId()}`;
  await createCard(scenario.admin, todo.id, title);
  return { scenario, title };
}

async function openCard(page: Page, boardId: string, title: string) {
  await page.goto(`/boards/${boardId}`);
  await page
    .getByRole("region", { name: "To Do" })
    .getByText(title, { exact: true })
    .click();
  const dialog = page.getByRole("dialog", { name: "Card details" });
  await expect(dialog).toBeVisible();
  return dialog;
}

test.describe("comments, mentions, and notifications", () => {
  test("creates, replies to, edits, and deletes a Comment", async ({
    page,
    context,
    baseURL,
  }) => {
    const { scenario, title } = await createScenarioWithCard(baseURL ?? "");
    await loginInBrowser(context, scenario.admin);
    const id = uniqueId();
    const rootBody = `Root comment ${id}`;
    const replyBody = `Reply comment ${id}`;
    const editedBody = `Edited comment ${id}`;

    const dialog = await openCard(page, scenario.board.id, title);
    await expect(dialog.getByText("No comments yet.")).toBeVisible();

    await dialog.getByLabel("Add a comment").fill(rootBody);
    await dialog.getByRole("button", { name: "Comment", exact: true }).click();
    const comments = dialog.getByRole("region", { name: "Comments" });
    await expect(comments.getByText(rootBody)).toBeVisible();

    // Reply (threaded)
    const rootItem = comments
      .getByRole("listitem")
      .filter({ hasText: rootBody })
      .first();
    await rootItem.getByRole("button", { name: "Reply", exact: true }).click();
    await dialog.getByLabel("Reply", { exact: true }).fill(replyBody);
    await dialog.getByRole("button", { name: "Post reply" }).click();
    await expect(comments.getByText(replyBody)).toBeVisible();

    // Edit the root comment
    // The root item also contains the nested reply, so take its own button (first in DOM).
    await rootItem
      .getByRole("button", { name: "Edit", exact: true })
      .first()
      .click();
    await dialog.getByLabel("Edit comment").fill(editedBody);
    await comments.getByRole("button", { name: "Save", exact: true }).click();
    await expect(comments.getByText(editedBody)).toBeVisible();
    await expect(comments.getByText(rootBody)).toHaveCount(0);
    await expect(comments.getByText("(edited)")).toBeVisible();

    // Delete the reply (the nested list item is last in DOM order)
    const replyItem = comments
      .getByRole("listitem")
      .filter({ hasText: replyBody })
      .last();
    await replyItem.getByRole("button", { name: "Delete", exact: true }).click();
    await replyItem.getByRole("button", { name: "Confirm delete" }).click();
    await expect(comments.getByText(replyBody)).toHaveCount(0);
    await expect(comments.getByText(editedBody)).toBeVisible();
  });

  test("a mentioned Member sees the Notification via polling and marks it read", async ({
    page,
    context,
    browser,
    baseURL,
  }) => {
    // One full 30 s polling cycle plus setup exceeds the default 30 s test timeout.
    test.setTimeout(90_000);
    const { scenario, title } = await createScenarioWithCard(baseURL ?? "");
    const member = await addTeamMemberToBoard(
      scenario,
      baseURL ?? "",
      `Mentioned ${uniqueId()}`,
    );

    // The mentioned Member is already on the app, with no Notifications yet.
    const memberContext = await browser.newContext();
    try {
      await loginInBrowser(memberContext, member);
      const memberPage = await memberContext.newPage();
      await memberPage.goto("/boards");
      const bell = memberPage.getByRole("button", { name: /^Notifications,/ });
      await expect(bell).toHaveAccessibleName("Notifications, 0 unread");

      // The author mentions the Member in a Comment.
      await loginInBrowser(context, scenario.admin);
      const body = `Please look ${uniqueId()}`;
      const dialog = await openCard(page, scenario.board.id, title);
      await dialog
        .getByLabel("Mention a member")
        .selectOption({ label: member.displayName });
      await dialog.getByLabel("Add a comment").focus();
      const composer = dialog.getByLabel("Add a comment");
      await composer.fill(`${await composer.inputValue()}${body}`);
      await dialog
        .getByRole("button", { name: "Comment", exact: true })
        .click();
      await expect(
        dialog.getByText(`@${member.displayName} ${body}`),
      ).toBeVisible();

      // The Notification appears for the Member through polling.
      await expect(bell).toHaveAccessibleName("Notifications, 1 unread", {
        timeout: POLL_TIMEOUT_MS,
      });
      await bell.click();
      await expect(
        memberPage.getByText(/You were mentioned in a comment on the card/),
      ).toBeVisible();

      await memberPage.getByRole("button", { name: "Mark as read" }).click();
      await expect(bell).toHaveAccessibleName("Notifications, 0 unread");
      await expect(
        memberPage.getByRole("button", { name: "Mark as read" }),
      ).toHaveCount(0);
    } finally {
      await memberContext.close();
    }
  });
});
