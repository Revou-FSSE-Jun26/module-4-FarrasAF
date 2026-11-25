// API request and response types. They mirror design.md (API Design and
// API Response Schemas). All fields are camelCase; all ids are UUID strings;
// timestamps are ISO 8601 UTC strings.

// ---------- Shared enums ----------

export type TeamRole = "team_admin" | "team_regular";
export type BoardRole = "admin" | "member";
export type BoardVisibility = "private" | "team";
export type BoardStatus = "active" | "archived";
export type LinkStatus = "active" | "inactive";
export type NotificationStatus = "unread" | "read";

export type ActivityEventType =
  | "card_created"
  | "card_updated"
  | "card_moved"
  | "card_deleted"
  | "comment_created"
  | "comment_edited"
  | "comment_deleted"
  | "column_created"
  | "column_deleted"
  | "member_joined"
  | "member_removed";

// ---------- Errors ----------

export interface ApiErrorBody {
  code: string;
  message: string;
  field?: string;
}

export interface ApiErrorEnvelope {
  error: ApiErrorBody;
}

// ---------- Profile requests ----------

export interface UpdateProfileRequest {
  displayName: string;
}

export interface ChangePasswordRequest {
  currentPassword: string;
  newPassword: string;
}

// ---------- Response shapes ----------

export interface User {
  id: string;
  email: string;
  displayName: string;
}

export interface Team {
  id: string;
  name: string;
  currentUserTeamRole: TeamRole;
  createdAt: string;
}

export interface TeamMember {
  userId: string;
  displayName: string;
  teamRole: TeamRole;
}

export interface TeamJoinLink {
  id: string;
  teamId: string;
  token: string;
  status: LinkStatus;
  expiresAt: string;
  createdAt: string;
  isExpired: boolean;
}

export interface TeamJoinLinkPreview {
  teamName: string;
}

export interface AcceptJoinLinkResponse {
  teamId: string;
}

export interface Board {
  id: string;
  teamId: string;
  name: string;
  description: string;
  visibility: BoardVisibility;
  status: BoardStatus;
  currentUserRole: BoardRole;
  createdAt: string;
}

export interface BoardColumn extends Column {
  cards: Card[];
}

// Result of GET /api/boards/{boardId}: the Board with Columns and Cards nested.
export interface BoardDetail extends Board {
  columns: BoardColumn[];
}

export interface BoardMember {
  userId: string;
  displayName: string;
  role: BoardRole;
}

export interface Column {
  id: string;
  boardId: string;
  name: string;
  orderIndex: number;
  createdAt: string;
}

export interface Card {
  id: string;
  columnId: string;
  boardId: string;
  title: string;
  description: string;
  assigneeId: string | null;
  dueDate: string | null;
  createdById: string;
  orderIndex: number;
  version: number;
  createdAt: string;
  updatedAt: string;
}

export interface Comment {
  id: string;
  cardId: string;
  authorId: string;
  parentCommentId: string | null;
  body: string;
  version: number;
  createdAt: string;
  editedAt: string | null;
}

export interface Notification {
  id: string;
  recipientId: string;
  commentId: string;
  boardId: string;
  status: NotificationStatus;
  createdAt: string;
}

export interface ActivityEntry {
  id: string;
  boardId: string;
  actorId: string;
  eventType: ActivityEventType;
  resourceId: string;
  secondaryResourceId: string | null;
  createdAt: string;
}

export interface InvitationLink {
  id: string;
  boardId: string;
  token: string;
  status: LinkStatus;
  createdAt: string;
}

export interface ColumnCardCount {
  columnId: string;
  count: number;
}

export interface DayCount {
  day: string;
  count: number;
}

export interface Analytics {
  totalCards: number;
  perColumn: ColumnCardCount[];
  completionRate: number;
  activityByDay: DayCount[];
}

// Search result: a Card summary carrying its Board and Column (R7.2).
export interface SearchResult {
  id: string;
  title: string;
  description: string;
  assigneeId: string | null;
  dueDate: string | null;
  orderIndex: number;
  createdAt: string;
  updatedAt: string;
  board: { id: string; name: string };
  column: { id: string; name: string };
}

// ---------- Guest shapes ----------

export interface GuestUser {
  id: string;
  displayName: string;
}

export interface GuestCard {
  id: string;
  title: string;
  description: string;
  orderIndex: number;
  dueDate: string | null;
  assignee: GuestUser | null;
}

export interface GuestColumn {
  id: string;
  name: string;
  orderIndex: number;
  cards: GuestCard[];
}

export interface GuestBoard {
  id: string;
  name: string;
  description: string;
  currentUserRole: "guest";
  columns: GuestColumn[];
}

export interface GuestComment {
  id: string;
  parentCommentId: string | null;
  body: string;
  author: GuestUser;
  createdAt: string;
  editedAt: string | null;
}

// ---------- Collections and pages ----------

export interface ItemsResponse<T> {
  items: T[];
}

export interface NotificationPage {
  items: Notification[];
  nextCursor: string | null;
}

export interface ActivityPage {
  items: ActivityEntry[];
  page: number;
  pageSize: number;
}

// ---------- Request shapes ----------

export interface RegisterRequest {
  email: string;
  password: string;
  displayName: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface CreateTeamRequest {
  name: string;
}

export interface CreateBoardRequest {
  teamId: string;
  name: string;
}

export interface UpdateBoardRequest {
  name?: string;
  description?: string;
  visibility?: BoardVisibility;
}

export interface ListBoardsParams {
  archived?: boolean;
}

export interface CreateColumnRequest {
  name: string;
}

export interface RenameColumnRequest {
  name: string;
}

export interface ReorderColumnRequest {
  targetIndex: number;
}

export interface CreateCardRequest {
  title: string;
  description?: string;
  assigneeId?: string | null;
  dueDate?: string | null;
}

export interface UpdateCardRequest {
  title?: string;
  description?: string;
  assigneeId?: string | null;
  dueDate?: string | null;
  version: number;
}

export interface MoveCardRequest {
  targetColumnId: string;
  targetIndex: number;
}

export interface CreateCommentRequest {
  body: string;
  parentCommentId?: string | null;
}

export interface UpdateCommentRequest {
  body: string;
  version: number;
}

export interface ListNotificationsParams {
  cursor?: string;
  unreadOnly?: boolean;
}

export interface AddBoardMemberRequest {
  userId: string;
  role: BoardRole;
}

export interface ChangeBoardMemberRoleRequest {
  role: BoardRole;
}
