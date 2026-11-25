import { randomUUID } from "node:crypto";
import {
  expect,
  request as playwrightRequest,
  test as base,
} from "@playwright/test";
import type { APIRequestContext, BrowserContext, Page } from "@playwright/test";
import type {
  Board,
  BoardDetail,
  Card,
  Column,
  CreateBoardRequest,
  CreateCardRequest,
  CreateColumnRequest,
  InvitationLink,
  RegisterRequest,
  Team,
  TeamJoinLink,
  User,
} from "@/types/api";

// Baseline data created by `python -m scripts.seed` (backend/scripts/seed.py).
export const SEED = {
  password: "Password123!",
  adminEmail: "admin@example.com",
  memberEmail: "member@example.com",
  outsiderEmail: "outsider@example.com",
  teamName: "Demo Team",
  boardName: "Demo Board",
  invitationToken: "demo-invitation-token-for-e2e-0000000000000001",
} as const;

export const DEFAULT_PASSWORD = "E2e-Password-123!";

/** A registered user with a logged-in API session (HttpOnly cookies kept in `api`). */
export interface TestUser {
  user: User;
  email: string;
  password: string;
  displayName: string;
  api: APIRequestContext;
}

interface Fixtures {
  makeUser: (displayName?: string) => Promise<TestUser>;
}

/** Unique, collision-free suffix so parallel tests never share data. */
export function uniqueId(): string {
  return randomUUID().replace(/-/g, "").slice(0, 12);
}

async function parseJson<T>(
  response: Awaited<ReturnType<APIRequestContext["get"]>>,
  context: string,
): Promise<T> {
  if (!response.ok()) {
    throw new Error(
      `${context} failed with status ${response.status()}: ${await response.text()}`,
    );
  }
  const body: unknown = await response.json();
  return body as T;
}

async function expectNoContent(
  response: Awaited<ReturnType<APIRequestContext["get"]>>,
  context: string,
): Promise<void> {
  if (!response.ok()) {
    throw new Error(
      `${context} failed with status ${response.status()}: ${await response.text()}`,
    );
  }
}

/** Registers a fresh user and logs in; the returned context carries the auth cookies. */
export async function createUser(
  baseURL: string,
  displayName = "E2E User",
): Promise<TestUser> {
  const email = `e2e-${uniqueId()}@example.com`;
  const api = await playwrightRequest.newContext({ baseURL });
  const registerBody: RegisterRequest = {
    email,
    password: DEFAULT_PASSWORD,
    displayName,
  };
  await parseJson<User>(
    await api.post("/api/auth/register", { data: registerBody }),
    "register",
  );
  const user = await parseJson<User>(
    await api.post("/api/auth/login", {
      data: { email, password: DEFAULT_PASSWORD },
    }),
    "login",
  );
  return { user, email, password: DEFAULT_PASSWORD, displayName, api };
}

/** Copies the API session cookies into a browser context so pages start logged in. */
export async function loginInBrowser(
  context: BrowserContext,
  testUser: TestUser,
): Promise<void> {
  const state = await testUser.api.storageState();
  await context.addCookies(state.cookies);
}

/** Logs in through the UI with accessible locators. */
export async function loginThroughUi(
  page: Page,
  email: string,
  password: string,
): Promise<void> {
  await page.goto("/login");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password").fill(password);
  await page.getByRole("button", { name: /log in|sign in/i }).click();
  await expect(page).not.toHaveURL(/\/login/);
}

export async function createTeam(
  owner: TestUser,
  name = `Team ${uniqueId()}`,
): Promise<Team> {
  return parseJson<Team>(
    await owner.api.post("/api/teams", { data: { name } }),
    "create team",
  );
}

export async function createTeamJoinLink(
  owner: TestUser,
  teamId: string,
): Promise<TeamJoinLink> {
  return parseJson<TeamJoinLink>(
    await owner.api.post(`/api/teams/${teamId}/join-links`),
    "create team join link",
  );
}

export async function joinTeam(
  joiner: TestUser,
  token: string,
): Promise<{ teamId: string }> {
  return parseJson<{ teamId: string }>(
    await joiner.api.post(`/api/team-join-links/${token}/accept`),
    "accept team join link",
  );
}

/** Creates a Board (the creator becomes its Admin). Returns the full Board with default Columns. */
export async function createBoard(
  owner: TestUser,
  teamId: string,
  name = `Board ${uniqueId()}`,
): Promise<BoardDetail> {
  const data: CreateBoardRequest = { teamId, name };
  const created = await parseJson<Board>(
    await owner.api.post("/api/boards", { data }),
    "create board",
  );
  return getBoard(owner, created.id);
}

export async function getBoard(
  user: TestUser,
  boardId: string,
): Promise<BoardDetail> {
  return parseJson<BoardDetail>(
    await user.api.get(`/api/boards/${boardId}`),
    "get board",
  );
}

export async function createColumn(
  admin: TestUser,
  boardId: string,
  name: string,
): Promise<Column> {
  const data: CreateColumnRequest = { name };
  return parseJson<Column>(
    await admin.api.post(`/api/boards/${boardId}/columns`, { data }),
    "create column",
  );
}

export async function createCard(
  user: TestUser,
  columnId: string,
  title = `Card ${uniqueId()}`,
  extra: Omit<CreateCardRequest, "title"> = {},
): Promise<Card> {
  const data: CreateCardRequest = { title, ...extra };
  return parseJson<Card>(
    await user.api.post(`/api/columns/${columnId}/cards`, { data }),
    "create card",
  );
}

export async function addBoardMember(
  admin: TestUser,
  boardId: string,
  userId: string,
  role: "admin" | "member" = "member",
): Promise<void> {
  await expectNoContent(
    await admin.api.post(`/api/boards/${boardId}/members`, {
      data: { userId, role },
    }),
    "add board member",
  );
}

export async function createInvitationLink(
  admin: TestUser,
  boardId: string,
): Promise<InvitationLink> {
  return parseJson<InvitationLink>(
    await admin.api.post(`/api/boards/${boardId}/invitations`),
    "create invitation link",
  );
}

export async function revokeInvitationLink(
  admin: TestUser,
  token: string,
): Promise<void> {
  await expectNoContent(
    await admin.api.post(`/api/invitations/${token}/revoke`),
    "revoke invitation link",
  );
}

export interface BoardScenario {
  admin: TestUser;
  team: Team;
  board: BoardDetail;
}

/** Admin user + Team + Board (default columns). The common starting point for most flows. */
export async function createBoardScenario(
  baseURL: string,
): Promise<BoardScenario> {
  const admin = await createUser(baseURL, "Board Admin");
  const team = await createTeam(admin);
  const board = await createBoard(admin, team.id);
  return { admin, team, board };
}

/** Adds a second user to the Team and the Board as a Member. */
export async function addTeamMemberToBoard(
  scenario: BoardScenario,
  baseURL: string,
  displayName = "Board Member",
): Promise<TestUser> {
  const member = await createUser(baseURL, displayName);
  const link = await createTeamJoinLink(scenario.admin, scenario.team.id);
  await joinTeam(member, link.token);
  await addBoardMember(scenario.admin, scenario.board.id, member.user.id);
  return member;
}

/**
 * `makeUser` registers users that are disposed automatically after each test.
 * Every test creates its own data; nothing is shared between tests.
 */
export const test = base.extend<Fixtures>({
  makeUser: async ({ baseURL }, provide) => {
    if (!baseURL) {
      throw new Error("baseURL must be set in playwright.config.ts");
    }
    const created: TestUser[] = [];
    await provide(async (displayName?: string) => {
      const testUser = await createUser(baseURL, displayName);
      created.push(testUser);
      return testUser;
    });
    await Promise.all(created.map((u) => u.api.dispose()));
  },
});

export { expect };
