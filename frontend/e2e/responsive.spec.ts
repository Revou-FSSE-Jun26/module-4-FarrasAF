import type { Locator, Page } from "@playwright/test";
import { createBoardScenario, expect, loginInBrowser, test } from "./fixtures";

const BREAKPOINT = 1024;
const COLUMN_NAMES = ["To Do", "Doing", "Done"];

interface Box {
  x: number;
  y: number;
  width: number;
  height: number;
}

async function boxOf(locator: Locator): Promise<Box> {
  const box = await locator.boundingBox();
  if (!box) throw new Error("element has no bounding box");
  return box;
}

function overlaps(a: Box, b: Box): boolean {
  const tolerance = 1; // sub-pixel rounding
  return (
    a.x < b.x + b.width - tolerance &&
    b.x < a.x + a.width - tolerance &&
    a.y < b.y + b.height - tolerance &&
    b.y < a.y + a.height - tolerance
  );
}

async function expectNoOverlap(locators: Locator[]): Promise<void> {
  const boxes = await Promise.all(locators.map(boxOf));
  for (let i = 0; i < boxes.length; i += 1) {
    for (let j = i + 1; j < boxes.length; j += 1) {
      expect(
        overlaps(boxes[i], boxes[j]),
        `elements ${i} and ${j} overlap`,
      ).toBe(false);
    }
  }
}

async function hasHorizontalPageScroll(page: Page): Promise<boolean> {
  return page.evaluate(
    () =>
      document.documentElement.scrollWidth >
      document.documentElement.clientWidth,
  );
}

test.describe("responsive layout (breakpoint 1024px)", () => {
  for (const width of [1024, 1280, 1920]) {
    test(`Board view has no horizontal page scroll at ${width}px`, async ({
      page,
      context,
      baseURL,
    }) => {
      const { admin, board } = await createBoardScenario(baseURL ?? "");
      await loginInBrowser(context, admin);
      await page.setViewportSize({ width, height: 800 });

      await page.goto(`/boards/${board.id}`);
      for (const name of COLUMN_NAMES) {
        await expect(page.getByRole("region", { name })).toBeVisible();
      }

      expect(await hasHorizontalPageScroll(page)).toBe(false);
      const viewportWidth = page.viewportSize()?.width ?? width;
      for (const name of COLUMN_NAMES) {
        const box = await boxOf(page.getByRole("region", { name }));
        expect(box.x).toBeGreaterThanOrEqual(0);
        expect(box.x + box.width).toBeLessThanOrEqual(viewportWidth);
      }
      await expect(
        page.getByRole("navigation", { name: "Primary" }),
      ).toBeVisible();
    });
  }

  for (const width of [375, 768]) {
    test(`key controls stay visible and do not overlap at ${width}px`, async ({
      page,
      context,
      baseURL,
    }) => {
      expect(width).toBeLessThan(BREAKPOINT);
      const { admin, board } = await createBoardScenario(baseURL ?? "");
      await loginInBrowser(context, admin);
      await page.setViewportSize({ width, height: 800 });

      await page.goto(`/boards/${board.id}`);
      const columns = COLUMN_NAMES.map((name) =>
        page.getByRole("region", { name }),
      );
      for (const column of columns) {
        await expect(column).toBeVisible();
      }
      const primaryNav = page.getByRole("navigation", { name: "Primary" });
      const boardNav = page.getByRole("navigation", { name: "Board" });
      const addColumn = page.getByRole("button", { name: "Add column" });
      await expect(primaryNav).toBeVisible();
      await expect(boardNav).toBeVisible();
      await expect(addColumn).toBeVisible();

      await expectNoOverlap([primaryNav, boardNav, ...columns]);

      const navLinks = await primaryNav.getByRole("link").all();
      expect(navLinks.length).toBeGreaterThan(0);
      await expectNoOverlap(navLinks);

      const boardLinks = await boardNav.getByRole("link").all();
      await expectNoOverlap(boardLinks);

      const addColumnBox = await boxOf(addColumn);
      for (const column of columns) {
        expect(overlaps(addColumnBox, await boxOf(column))).toBe(false);
      }
    });
  }
});
