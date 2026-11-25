import type {
  AcceptJoinLinkResponse,
  ActivityPage,
  AddBoardMemberRequest,
  Analytics,
  ApiErrorBody,
  Board,
  BoardDetail,
  BoardMember,
  Card,
  ChangeBoardMemberRoleRequest,
  ChangePasswordRequest,
  Column,
  Comment,
  CreateBoardRequest,
  CreateCardRequest,
  CreateColumnRequest,
  CreateCommentRequest,
  CreateTeamRequest,
  GuestBoard,
  GuestComment,
  InvitationLink,
  ItemsResponse,
  ListBoardsParams,
  ListNotificationsParams,
  LoginRequest,
  MoveCardRequest,
  Notification,
  NotificationPage,
  RegisterRequest,
  RenameColumnRequest,
  ReorderColumnRequest,
  SearchResult,
  Team,
  TeamJoinLink,
  TeamJoinLinkPreview,
  TeamMember,
  UpdateBoardRequest,
  UpdateCardRequest,
  UpdateCommentRequest,
  UpdateProfileRequest,
  User,
} from "@/types/api";

type HttpMethod = "GET" | "POST" | "PATCH" | "DELETE";
type QueryValue = string | number | boolean | undefined;

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly field?: string;

  constructor(status: number, body: ApiErrorBody) {
    super(body.message);
    this.name = "ApiError";
    this.status = status;
    this.code = body.code;
    this.field = body.field;
  }

  get isConflict(): boolean {
    return this.status === 409;
  }
}

// Auth endpoints never trigger refresh-and-retry: a 401 there is the answer.
const NO_REFRESH_PATHS: readonly string[] = [
  "/api/auth/login",
  "/api/auth/register",
  "/api/auth/refresh",
  "/api/auth/logout",
];

// Pages that show the 401 error instead of redirecting to /login.
const PUBLIC_PAGE_PATTERN = /^\/(login|register|invite\/[^/]+)\/?$/;
const JOIN_PAGE_PATTERN = /^\/join\/[^/]+\/?$/;

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function toErrorBody(data: unknown, status: number): ApiErrorBody {
  if (isRecord(data) && isRecord(data.error)) {
    const { code, message, field } = data.error;
    if (typeof code === "string" && typeof message === "string") {
      return { code, message, ...(typeof field === "string" ? { field } : {}) };
    }
  }
  return { code: "unknown_error", message: `Request failed (${status})` };
}

function buildQuery(params: Record<string, QueryValue>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined) {
      search.set(key, String(value));
    }
  }
  const text = search.toString();
  return text ? `?${text}` : "";
}

function redirectToLoginIfNeeded(): void {
  if (typeof window === "undefined") return;
  const { pathname } = window.location;
  if (PUBLIC_PAGE_PATTERN.test(pathname)) return;
  if (JOIN_PAGE_PATTERN.test(pathname)) {
    // Return to the same join link after a successful login.
    // eslint-disable-next-line @next/next/no-location-assign-relative-destination -- full reload outside React
    window.location.href = `/login?next=${encodeURIComponent(pathname)}`;
    return;
  }
  // eslint-disable-next-line @next/next/no-location-assign-relative-destination -- full reload outside React
  window.location.href = "/login";
}

let refreshInFlight: Promise<boolean> | null = null;

function refreshSession(): Promise<boolean> {
  if (!refreshInFlight) {
    refreshInFlight = fetch("/api/auth/refresh", {
      method: "POST",
      credentials: "same-origin",
    })
      .then((res) => res.ok)
      .catch(() => false)
      .finally(() => {
        refreshInFlight = null;
      });
  }
  return refreshInFlight;
}

async function send(
  method: HttpMethod,
  path: string,
  body?: unknown,
): Promise<Response> {
  const init: RequestInit = { method, credentials: "same-origin" };
  if (body !== undefined) {
    init.headers = { "Content-Type": "application/json" };
    init.body = JSON.stringify(body);
  }
  return fetch(path, init);
}

async function request<T>(
  method: HttpMethod,
  path: string,
  body?: unknown,
): Promise<T> {
  let res = await send(method, path, body);

  const basePath = path.split("?")[0];
  const isNoRefresh =
    NO_REFRESH_PATHS.includes(basePath) || basePath.startsWith("/api/guest/");
  if (res.status === 401 && !isNoRefresh) {
    if (await refreshSession()) {
      res = await send(method, path, body);
    }
    if (res.status === 401) {
      redirectToLoginIfNeeded();
    }
  }

  if (res.status === 204) {
    return undefined as T;
  }

  let data: unknown = null;
  try {
    data = await res.json();
  } catch {
    data = null;
  }

  if (!res.ok) {
    throw new ApiError(res.status, toErrorBody(data, res.status));
  }
  return data as T;
}

const enc = encodeURIComponent;

export const apiClient = {
  // ----- Auth -----
  register: (body: RegisterRequest) =>
    request<User>("POST", "/api/auth/register", body),
  login: (body: LoginRequest) => request<User>("POST", "/api/auth/login", body),
  logout: () => request<void>("POST", "/api/auth/logout"),
  refresh: () => request<User>("POST", "/api/auth/refresh"),
  getMe: () => request<User>("GET", "/api/auth/me"),
  updateProfile: (body: UpdateProfileRequest) =>
    request<User>("PATCH", "/api/auth/me", body),
  changePassword: (body: ChangePasswordRequest) =>
    request<User>("POST", "/api/auth/me/password", body),

  // ----- Teams -----
  createTeam: (body: CreateTeamRequest) =>
    request<Team>("POST", "/api/teams", body),
  listTeams: () => request<ItemsResponse<Team>>("GET", "/api/teams"),
  listTeamMembers: (teamId: string) =>
    request<ItemsResponse<TeamMember>>(
      "GET",
      `/api/teams/${enc(teamId)}/members`,
    ),
  createTeamJoinLink: (teamId: string) =>
    request<TeamJoinLink>("POST", `/api/teams/${enc(teamId)}/join-links`),
  listTeamJoinLinks: (teamId: string) =>
    request<ItemsResponse<TeamJoinLink>>(
      "GET",
      `/api/teams/${enc(teamId)}/join-links`,
    ),
  revokeTeamJoinLink: (token: string) =>
    request<TeamJoinLink>("POST", `/api/team-join-links/${enc(token)}/revoke`),
  previewTeamJoinLink: (token: string) =>
    request<TeamJoinLinkPreview>("GET", `/api/team-join-links/${enc(token)}`),
  acceptTeamJoinLink: (token: string) =>
    request<AcceptJoinLinkResponse>(
      "POST",
      `/api/team-join-links/${enc(token)}/accept`,
    ),

  // ----- Boards -----
  createBoard: (body: CreateBoardRequest) =>
    request<Board>("POST", "/api/boards", body),
  listBoards: (params: ListBoardsParams = {}) =>
    request<ItemsResponse<Board>>(
      "GET",
      `/api/boards${params.archived ? "?archived=true" : ""}`,
    ),
  getBoard: (boardId: string) =>
    request<BoardDetail>("GET", `/api/boards/${enc(boardId)}`),
  updateBoard: (boardId: string, body: UpdateBoardRequest) =>
    request<Board>("PATCH", `/api/boards/${enc(boardId)}`, body),
  archiveBoard: (boardId: string) =>
    request<Board>("POST", `/api/boards/${enc(boardId)}/archive`),
  restoreBoard: (boardId: string) =>
    request<Board>("POST", `/api/boards/${enc(boardId)}/restore`),
  deleteBoard: (boardId: string) =>
    request<void>("DELETE", `/api/boards/${enc(boardId)}`),

  // ----- Columns -----
  createColumn: (boardId: string, body: CreateColumnRequest) =>
    request<Column>("POST", `/api/boards/${enc(boardId)}/columns`, body),
  renameColumn: (columnId: string, body: RenameColumnRequest) =>
    request<Column>("PATCH", `/api/columns/${enc(columnId)}`, body),
  reorderColumn: (columnId: string, body: ReorderColumnRequest) =>
    request<Column>("POST", `/api/columns/${enc(columnId)}/reorder`, body),
  deleteColumn: (columnId: string) =>
    request<void>("DELETE", `/api/columns/${enc(columnId)}`),

  // ----- Cards -----
  createCard: (columnId: string, body: CreateCardRequest) =>
    request<Card>("POST", `/api/columns/${enc(columnId)}/cards`, body),
  getCard: (cardId: string) =>
    request<Card>("GET", `/api/cards/${enc(cardId)}`),
  updateCard: (cardId: string, body: UpdateCardRequest) =>
    request<Card>("PATCH", `/api/cards/${enc(cardId)}`, body),
  moveCard: (cardId: string, body: MoveCardRequest) =>
    request<Card>("POST", `/api/cards/${enc(cardId)}/move`, body),
  deleteCard: (cardId: string) =>
    request<void>("DELETE", `/api/cards/${enc(cardId)}`),

  // ----- Comments -----
  listComments: (cardId: string) =>
    request<ItemsResponse<Comment>>(
      "GET",
      `/api/cards/${enc(cardId)}/comments`,
    ),
  createComment: (cardId: string, body: CreateCommentRequest) =>
    request<Comment>("POST", `/api/cards/${enc(cardId)}/comments`, body),
  updateComment: (commentId: string, body: UpdateCommentRequest) =>
    request<Comment>("PATCH", `/api/comments/${enc(commentId)}`, body),
  deleteComment: (commentId: string) =>
    request<void>("DELETE", `/api/comments/${enc(commentId)}`),

  // ----- Notifications -----
  listNotifications: (params: ListNotificationsParams = {}) =>
    request<NotificationPage>(
      "GET",
      `/api/notifications${buildQuery({ cursor: params.cursor, unreadOnly: params.unreadOnly })}`,
    ),
  markNotificationRead: (notificationId: string) =>
    request<Notification>(
      "POST",
      `/api/notifications/${enc(notificationId)}/read`,
    ),

  // ----- Search -----
  searchCards: (q: string) =>
    request<ItemsResponse<SearchResult>>(
      "GET",
      `/api/search/cards${buildQuery({ q })}`,
    ),

  // ----- Activity and analytics -----
  listActivity: (boardId: string, page?: number) =>
    request<ActivityPage>(
      "GET",
      `/api/boards/${enc(boardId)}/activity${buildQuery({ page })}`,
    ),
  getAnalytics: (boardId: string) =>
    request<Analytics>("GET", `/api/boards/${enc(boardId)}/analytics`),

  // ----- Board members and invitations -----
  listBoardMembers: (boardId: string) =>
    request<ItemsResponse<BoardMember>>(
      "GET",
      `/api/boards/${enc(boardId)}/members`,
    ),
  addBoardMember: (boardId: string, body: AddBoardMemberRequest) =>
    request<BoardMember>("POST", `/api/boards/${enc(boardId)}/members`, body),
  changeBoardMemberRole: (
    boardId: string,
    userId: string,
    body: ChangeBoardMemberRoleRequest,
  ) =>
    request<BoardMember>(
      "PATCH",
      `/api/boards/${enc(boardId)}/members/${enc(userId)}`,
      body,
    ),
  removeBoardMember: (boardId: string, userId: string) =>
    request<void>(
      "DELETE",
      `/api/boards/${enc(boardId)}/members/${enc(userId)}`,
    ),
  listInvitations: (boardId: string) =>
    request<ItemsResponse<InvitationLink>>(
      "GET",
      `/api/boards/${enc(boardId)}/invitations`,
    ),
  createInvitation: (boardId: string) =>
    request<InvitationLink>("POST", `/api/boards/${enc(boardId)}/invitations`),
  revokeInvitation: (token: string) =>
    request<InvitationLink>("POST", `/api/invitations/${enc(token)}/revoke`),

  // ----- Guest (anonymous, read-only) -----
  getGuestBoard: (token: string) =>
    request<GuestBoard>("GET", `/api/guest/${enc(token)}/board`),
  listGuestComments: (token: string, cardId: string) =>
    request<ItemsResponse<GuestComment>>(
      "GET",
      `/api/guest/${enc(token)}/cards/${enc(cardId)}/comments`,
    ),
};
