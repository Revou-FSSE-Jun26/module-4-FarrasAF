# Requirements Document

## Introduction

This document specifies the requirements for a collaborative team task management web application inspired by Trello. Teams organize work using Boards that contain ordered Columns, and each Column contains ordered Cards representing tasks. Members create and manage Cards, assign ownership, move Cards between Columns via drag-and-drop, communicate through threaded Comments, receive Notifications when mentioned, search Cards, view an Activity Log, and view Board Analytics. Access to each Board is governed by role-based access control (RBAC) across three Board roles: Guest, Member, and Admin. Membership in a Team is governed by two Team_Roles: Team_Admin and Team_Regular.

The application targets clear visibility into task progress, task ownership, and team activity within shared Team workspaces. Users register and authenticate with an account using an email address and password before accessing Boards, except that Guests read a single Board through an Invitation_Link without an account or authentication. Successful authentication issues a JWT-based access token that identifies the User on subsequent requests. Authenticated Users create Teams and bring others into a Team through Team_Join_Links. The initial version (V1) excludes file attachments, email notifications, password reset and email verification, third-party integrations, advanced analytics, burndown charts, real-time collaboration via WebSockets, removing Team_Members from a Team, leaving a Team, changing Team_Roles, and renaming or deleting a Team.

## Glossary

- **System**: The complete task management web application, including frontend and backend components.
- **Board_Service**: The backend component responsible for Board creation, visibility, archival, deletion, and settings.
- **Column_Service**: The backend component responsible for Column creation, editing, deletion, and ordering.
- **Card_Service**: The backend component responsible for Card creation, editing, deletion, movement, and ordering.
- **Comment_Service**: The backend component responsible for Comment creation, threaded replies, editing, and deletion.
- **Notification_Service**: The backend component responsible for creating, storing, retrieving, and updating Notifications.
- **Search_Service**: The backend component responsible for searching Cards across accessible Boards.
- **Activity_Service**: The backend component responsible for recording and retrieving Board activity entries.
- **Analytics_Service**: The backend component responsible for computing and returning Board analytics.
- **Access_Control_Service**: The backend component that enforces role-based access control and invitation link validation.
- **Authentication_Service**: The backend component responsible for User registration, credential verification, issuance of Access_Tokens and Refresh_Tokens, token refresh, Refresh_Token revocation, and authentication enforcement.
- **Session**: An authenticated context for a User represented by an Access_Token and a Refresh_Token, established upon successful login and ended when the Refresh_Token is revoked (logout) or expires.
- **Access_Token**: A short-lived JSON Web Token (JWT) issued upon successful authentication that carries the User's identity and authenticates API requests until it expires.
- **Refresh_Token**: A longer-lived credential issued upon successful authentication that the Authentication_Service uses to mint new Access_Tokens, and that is revoked upon logout.
- **Account_Lockout**: A state in which an account is temporarily barred from authenticating, entered after a defined number of consecutive failed login attempts and cleared after a defined lockout period elapses or a successful login occurs.
- **Team**: A group of Users created by a User and owning one or more Boards.
- **Board**: A workspace that belongs to a Team and contains an ordered set of Columns.
- **Column**: An ordered container within a Board that holds an ordered list of Cards.
- **Card**: A task item within a Column containing Title, Description, Assignee, Due date, Created by, Created timestamp, and Updated timestamp.
- **Comment**: A text message attached to a Card that may be a top-level Comment or a threaded reply to another Comment.
- **Notification**: A stored record informing a Member of an event, with a read or unread status.
- **Notification_Cursor**: A pagination marker composed of a Notification's creation timestamp and its identifier that encodes a stable position within the ordering of Notifications used to retrieve subsequent pages.
- **Invitation_Link**: A shareable token that grants Guest access to a specific Board while active.
- **User**: An individual with a registered account who authenticates via the Authentication_Service and may hold a Board role on one or more Boards and a Team_Role in one or more Teams.
- **Guest**: A role that grants read-only access to a Board through an active Invitation_Link, without requiring a registered account or authentication.
- **Member**: A Board role that grants Card, Comment, search, notification, and analytics capabilities on a Board.
- **Admin**: A Board role that grants all Member capabilities plus Column, member, settings, and Board lifecycle management.
- **Assignee**: The Member designated as responsible for a Card.
- **Mention**: A reference to a Member within a Comment body using a mention token.
- **Activity_Entry**: A recorded log item describing a Board event with a timestamp and the acting User.
- **Card_Position**: The ordered placement of a Card, defined by its Column assignment and its order index within that Column.
- **Team_Service**: The backend component responsible for Team creation, Team membership listing, and Team_Join_Link lifecycle.
- **Team_Member**: A User who belongs to a Team regardless of Team_Role.
- **Team_Admin**: The Team_Role held by the User who created the Team; permits generating and revoking Team_Join_Links.
- **Team_Role**: The role of a Team_Member within a Team, either Team_Admin or Team_Regular. Distinct from Board roles.
- **Team_Join_Link**: A shareable token that lets an authenticated User become a Team_Member of a specific Team while the link is active and unexpired.

## Requirements

### Requirement 1: Board Management

**User Story:** As a Team_Member, I want to create Boards for my Team, and as an Admin of a Board I want to manage it, so that my Team has a shared workspace for organizing work.

#### Acceptance Criteria

1. WHEN a Team_Member submits a Board creation request specifying a Team of which the User is a Team_Member and a Board name containing 1 to 100 characters after trimming leading and trailing whitespace, THE Board_Service SHALL create a Board associated with that Team, grant the requesting User the Admin role on the Board, and return the created Board identifier.
2. WHEN an Admin creates a Board, THE Board_Service SHALL create three default Columns named "To Do", "Doing", and "Done" in that order.
3. WHEN an Admin submits a Board update request containing any subset of a Board name of 1 to 100 characters, a Board description of 0 to 2000 characters, and a Board visibility set to one of "private" or "team", THE Board_Service SHALL persist the supplied fields, leave any field not included in the request unchanged, and return the updated Board.
4. WHEN an Admin submits a Board archive request, THE Board_Service SHALL set the Board status to archived and exclude the Board from active Board listings.
5. WHEN an Admin submits a restore request for a Board whose status is archived, THE Board_Service SHALL set the Board status to active and include the Board in active Board listings.
6. WHEN an Admin submits a permanent deletion request for a Board, THE Board_Service SHALL delete the Board together with its Columns, Cards, Comments, and Activity_Entries.
7. IF a User without the Admin role submits a Board settings, archive, restore, or deletion request, THEN THE Access_Control_Service SHALL reject the request with an authorization error and SHALL leave the Board unchanged.
8. IF a User submits a Board creation or Board name update request whose Board name is empty after trimming whitespace or exceeds 100 characters, THEN THE Board_Service SHALL reject the request with a validation error indicating the invalid Board name and SHALL leave Board data unchanged.
9. IF an Admin submits a restore request for a Board whose status is not archived, THEN THE Board_Service SHALL reject the request with a validation error indicating the Board is not archived and SHALL leave the Board status unchanged.
10. IF an Admin submits a Board update request in which any supplied field among Board name, Board description, and Board visibility is invalid, THEN THE Board_Service SHALL reject the entire request atomically with a validation error indicating the invalid field and SHALL leave all Board fields unchanged.
11. IF a User who is not a Team_Member of the specified Team submits a Board creation request, THEN THE Access_Control_Service SHALL reject the request with an authorization error and SHALL create no Board.
12. WHEN a Board is created, THE Access_Control_Service SHALL make the creator's Admin role on that Board effective for the creator's subsequent requests without requiring the creator to log in again.
13. WHEN a User requests the list of Boards, THE Board_Service SHALL return only the Boards on which the User holds the Member or Admin role, limited to active Boards unless an archived filter is supplied, in which case only archived Boards on which the User holds the Admin role are returned.
14. THE Board_Service SHALL store the Board visibility setting without changing which Users can access the Board in V1.

### Requirement 2: Column Management

**User Story:** As an Admin, I want to create, edit, reorder, and delete Columns, so that I can structure the workflow stages on a Board.

#### Acceptance Criteria

1. WHEN an Admin submits a Column creation request with a Column name that is non-empty after trimming leading and trailing whitespace and is at most 100 characters in length, THE Column_Service SHALL create the Column and append it as the last Column in the Board's Column order so that the new Column's order index equals the current count of Columns on the Board.
2. WHEN an Admin submits a Column name edit with a name that is non-empty after trimming leading and trailing whitespace and is at most 100 characters in length, THE Column_Service SHALL persist the updated name and return the updated Column.
3. WHEN an Admin submits a Column reorder request specifying a target order index in the range from zero to the count of Columns on the Board minus one inclusive, THE Column_Service SHALL place the Column at the target order index and reindex the Board's Columns so that Column order indices form a contiguous sequence starting at zero with no gaps or duplicates.
4. IF an Admin submits a Column deletion request for a Column that contains one or more Cards, THEN THE Column_Service SHALL reject the request with a validation error indicating that the Column must be empty before deletion, and SHALL leave the Column and its Cards unchanged.
5. WHEN an Admin submits a Column deletion request for an empty Column, THE Column_Service SHALL delete the Column and reindex the Board's remaining Columns so that order indices form a contiguous sequence starting at zero with no gaps or duplicates.
6. IF an Admin submits a Column creation or name edit request with a name that is empty after trimming leading and trailing whitespace or exceeds 100 characters in length, THEN THE Column_Service SHALL reject the request with a validation error indicating the name is invalid and SHALL leave the Columns unchanged.
7. IF an Admin submits a Column reorder request specifying a target order index that is negative or greater than the count of Columns on the Board minus one, THEN THE Column_Service SHALL reject the request with a validation error indicating the target index is out of range and SHALL leave the Column order unchanged.
8. IF a User without the Admin role submits a Column creation, edit, reorder, or deletion request, THEN THE Access_Control_Service SHALL reject the request with an authorization error and SHALL leave the Columns unchanged.

### Requirement 3: Card Management

**User Story:** As a Member, I want to create, edit, and delete task Cards, so that I can capture and maintain the Team's work items.

#### Acceptance Criteria

1. WHEN a Member submits a Card creation request with a Title that contains at least 1 and at most 255 characters after leading and trailing whitespace is removed for a Column, THE Card_Service SHALL create a Card in that Column with the submitted Title, the requesting Member as Created by, a Created timestamp set to the creation time, and an Updated timestamp equal to the Created timestamp.
2. WHEN a Member submits a Card creation request, THE Card_Service SHALL append the Card as the last Card in the target Column's Card order.
3. WHEN a Member edits a Card Title to a value that contains at least 1 and at most 255 characters after leading and trailing whitespace is removed, or edits a Card Description to a value of at most 5000 characters, Assignee, or Due date, THE Card_Service SHALL persist the changed values and set the Updated timestamp to the edit time.
4. WHEN a Member assigns a Card to an Assignee who is a current Member of the Card's Board, THE Card_Service SHALL set the Assignee to that Member.
5. WHEN a Member submits a Card deletion request, THE Card_Service SHALL delete the Card and SHALL reindex the remaining Cards in the Column so that order indices form a contiguous sequence starting at zero.
6. IF a Guest submits a Card creation, edit, or deletion request, THEN THE Access_Control_Service SHALL reject the request with an authorization error and SHALL leave the Cards unchanged.
7. IF a Member submits a Card creation or Title edit request whose Title is empty after leading and trailing whitespace is removed or exceeds 255 characters, THEN THE Card_Service SHALL reject the request with a validation error indicating an invalid Title and SHALL leave the Cards unchanged.
8. IF a Member submits a Card assignment request specifying an Assignee who is not a current Member of the Card's Board, THEN THE Card_Service SHALL reject the request with a validation error indicating an invalid Assignee and SHALL leave the Card's Assignee unchanged.
9. IF a Member submits a Card edit or deletion request referencing a Card that does not exist, THEN THE Card_Service SHALL reject the request with a not-found error and SHALL leave the Cards unchanged.
10. IF a Member submits a single Card edit request that modifies more than one field among Title, Description, Assignee, and Due date and any one of the supplied fields is invalid, THEN THE Card_Service SHALL reject the entire request atomically with a validation error indicating the invalid field and SHALL leave all Card fields unchanged.

### Requirement 4: Drag-and-Drop Card Movement and Ordering

**User Story:** As a Member, I want to move Cards between Columns and reorder Cards within a Column using drag-and-drop, so that I can reflect task progress.

#### Acceptance Criteria

1. WHEN an authorized non-Guest User (a Member or Admin) moves a Card to a target Column at a target order index that is an integer from 0 to the current number of Cards in the target Column (counting the moved Card once it is removed from its source Column), THE Card_Service SHALL set the Card's Column assignment to the target Column and the Card's order index to the target order index.
2. WHEN a Member moves or reorders a Card, THE Card_Service SHALL reindex the affected Columns so that each affected Column's Card order indices form a contiguous sequence starting at zero with no gaps or duplicates.
3. WHEN a Card movement or reorder operation completes successfully, THE Card_Service SHALL persist the updated Card_Position so that a subsequent retrieval returns the same Column assignment and order index.
4. IF a Member submits a move request targeting a Column that does not belong to the same Board as the Card, THEN THE Card_Service SHALL reject the request with a validation error indicating the target Column is outside the Card's Board, and SHALL leave the Card_Position unchanged.
5. IF a Member submits a move or reorder request with a target order index that is not an integer, is negative, or exceeds the maximum valid target order index for the target Column, THEN THE Card_Service SHALL reject the request with a validation error indicating the target order index is out of range, and SHALL leave the Card_Position unchanged.
6. IF a Guest submits a Card move or reorder request, THEN THE Access_Control_Service SHALL reject the request with an authorization error and SHALL leave the Card_Position unchanged.
7. WHEN a Card move or reorder operation completes successfully, THE Card_Service SHALL set the moved Card's Updated timestamp to the time of the operation, and SHALL leave the Updated timestamp of every other Card unchanged, including Cards whose order indices were shifted by reindexing.

### Requirement 5: Comments and Threaded Replies

**User Story:** As a Member, I want to comment on Cards and reply to existing Comments, so that the Team can discuss tasks in context.

#### Acceptance Criteria

1. WHEN a Member submits a Comment on a Card with Comment text containing 1 to 5000 non-whitespace characters, THE Comment_Service SHALL create a top-level Comment associated with the Card, recording the requesting Member as author and a creation timestamp.
2. WHEN a Member submits a reply with text containing 1 to 5000 non-whitespace characters referencing an existing parent Comment on the same Card, THE Comment_Service SHALL create a Comment linked to the parent Comment as a threaded reply.
3. WHEN a Member edits a Comment authored by the requesting Member with text containing 1 to 5000 non-whitespace characters, THE Comment_Service SHALL persist the updated Comment text and set an edited timestamp.
4. WHEN a Member deletes a Comment authored by the requesting Member, THE Comment_Service SHALL delete the Comment together with all replies directly or indirectly linked to that Comment.
5. IF a Member submits an edit or deletion request for a Comment authored by a different User, THEN THE Access_Control_Service SHALL reject the request with an authorization error and SHALL leave the Comment unchanged.
6. IF a Guest submits a Comment creation, edit, or deletion request, THEN THE Access_Control_Service SHALL reject the request with an authorization error and SHALL leave the Comments unchanged.
7. IF a Member submits a Comment creation, reply, or edit request whose text is empty, contains only whitespace, or exceeds 5000 characters, THEN THE Comment_Service SHALL reject the request with a validation error indicating the Comment text is invalid and SHALL leave the Comments unchanged.
8. IF a Member submits a reply referencing a parent Comment that does not exist or that belongs to a different Card, THEN THE Comment_Service SHALL reject the request with a validation error indicating the parent Comment is invalid and SHALL leave the Comments unchanged.

### Requirement 6: Mention Notifications

**User Story:** As a Member, I want to be notified when I am mentioned in a Comment, so that I can respond to items that require my attention.

#### Acceptance Criteria

1. WHEN a Comment containing one or more Mentions of a Member is created, THE Notification_Service SHALL create and store exactly one Notification per distinct mentioned Member for that Comment, each with an initial status of unread.
2. WHEN a Member requests their Notifications without a cursor, THE Notification_Service SHALL return the newest page of Notifications addressed to the requesting Member ordered by creation timestamp from most recent to least recent using the Notification identifier in descending order as a tie-break, with at most 50 Notifications per page, each including its read or unread status, and SHALL include a cursor representing the position of the last Notification in the returned page.
3. WHEN a Member requests their Notifications with a cursor, THE Notification_Service SHALL return the next page of Notifications addressed to the requesting Member that fall strictly after the cursor position in the ordering of creation timestamp descending with the Notification identifier descending as a tie-break, with at most 50 Notifications per page, each including its read or unread status, and SHALL include a cursor representing the position of the last Notification in the returned page.
4. WHEN a Member requests their Notifications with an unread-only filter enabled, THE Notification_Service SHALL return only the Notifications addressed to the requesting Member whose status is unread, applying the same cursor pagination, ordering, and page-size limit as the unfiltered request.
5. WHEN a Member marks a Notification addressed to the requesting Member as read, THE Notification_Service SHALL set that Notification's status to read and persist the status.
6. WHEN the frontend issues an HTTP request for new Notifications without a cursor, THE Notification_Service SHALL return the newest page of Notifications addressed to the requesting Member, ordered by creation timestamp from most recent to least recent using the Notification identifier in descending order as a tie-break, with at most 50 Notifications per page, and SHALL include a cursor representing the position of the last Notification in the returned page.
7. WHEN the frontend issues an HTTP request for new Notifications with a cursor composed of a creation timestamp and a Notification identifier, THE Notification_Service SHALL return the next page of Notifications addressed to the requesting Member that fall strictly after the cursor position in the ordering of creation timestamp descending with Notification identifier descending as a tie-break, with at most 50 Notifications per page, and SHALL include a cursor representing the position of the last Notification in the returned page.
8. IF a Comment mentions a User who is not a Member of the Board, THEN THE Notification_Service SHALL create no Notification for that User.
9. IF a Member submits a request to mark a Notification that is not addressed to the requesting Member as read, THEN THE Notification_Service SHALL reject the request with an authorization error and SHALL leave the Notification's status unchanged.
10. IF a Notification retrieval request, whether for the general Notification list or for new Notifications, supplies a cursor that is malformed or that does not encode a valid creation-timestamp-and-identifier pair, THEN THE Notification_Service SHALL reject the request with a validation error and SHALL return no Notifications.

### Requirement 7: Card Search

**User Story:** As a Member, I want to search Cards by Title across the Boards I can access, so that I can quickly locate specific tasks.

#### Acceptance Criteria

1. WHEN a Member submits a search request with a Title keyword of 1 to 100 characters, THE Search_Service SHALL return Cards whose Title contains the keyword as a case-insensitive substring and that belong to Boards the requesting Member can access.
2. WHEN THE Search_Service returns a search result, THE Search_Service SHALL include the Board and the Column associated with each returned Card.
3. THE Search_Service SHALL exclude from search results Cards that belong to Boards the requesting Member cannot access.
4. WHEN a search request matches no Cards, THE Search_Service SHALL return an empty result set.
5. IF a Member submits a search request whose keyword is empty, contains only whitespace, or exceeds 100 characters, THEN THE Search_Service SHALL reject the request with a validation error indicating the keyword is invalid and SHALL return no search results.
6. WHEN THE Search_Service returns a search result containing more than 100 matching Cards, THE Search_Service SHALL order the Cards by Updated timestamp from most recent to least recent, using the Card identifier in descending order as a tie-break for Cards with equal Updated timestamps, and SHALL return at most the first 100 Cards.

### Requirement 8: Activity Log

**User Story:** As a Member, I want to view a history of important Board activities, so that I can track what has changed and who changed it.

#### Acceptance Criteria

1. WHEN a Card is created, THE Activity_Service SHALL record an Activity_Entry with the event type "card created", the acting User's identity, the created Card's identifier, and a timestamp.
2. WHEN a Card is updated, THE Activity_Service SHALL record an Activity_Entry with the event type "card updated", the acting User's identity, the updated Card's identifier, and a timestamp.
3. WHEN a Card is moved, THE Activity_Service SHALL record an Activity_Entry with the event type "card moved", the acting User's identity, the moved Card's identifier, and a timestamp.
4. WHEN a Comment is created, THE Activity_Service SHALL record an Activity_Entry with the event type "comment created", the acting User's identity, the Card identifier the Comment is associated with, and a timestamp.
5. WHEN a Card is deleted, THE Activity_Service SHALL record an Activity_Entry with the event type "card deleted", the acting User's identity, the deleted Card's identifier, and a timestamp.
6. WHEN a Comment is deleted, THE Activity_Service SHALL record an Activity_Entry with the event type "comment deleted", the acting User's identity, the deleted Comment's identifier together with the Card identifier the Comment is associated with, and a timestamp.
7. WHEN a Comment is edited, THE Activity_Service SHALL record an Activity_Entry with the event type "comment edited", the acting User's identity, the edited Comment's identifier together with the Card identifier the Comment is associated with, and a timestamp.
8. WHEN a Column is created, THE Activity_Service SHALL record an Activity_Entry with the event type "column created", the acting User's identity, the created Column's identifier, and a timestamp.
9. WHEN a Column is deleted, THE Activity_Service SHALL record an Activity_Entry with the event type "column deleted", the acting User's identity, the deleted Column's identifier, and a timestamp.
10. WHEN an Admin grants a User a role on a Board so that the User becomes a Member of the Board, THE Activity_Service SHALL record an Activity_Entry with the event type "member joined", the acting User's identity, the granted Member's User identity, and a timestamp.
11. WHEN an Admin removes a Member from a Board, THE Activity_Service SHALL record an Activity_Entry with the event type "member removed", the acting User's identity, the removed Member's User identity, and a timestamp.
12. WHEN a Member requests a page of the activity history for a Board with a page index, THE Activity_Service SHALL return the Activity_Entries for that page ordered from most recent timestamp to least recent, using the Activity_Entry identifier in descending order as a tie-break for Activity_Entries with equal timestamps, with at most 100 Activity_Entries per page.
13. WHEN THE Activity_Service returns an Activity_Entry, THE Activity_Service SHALL include the event type, the timestamp, the acting User's identity, and the affected resource identifier.
14. IF a request to retrieve a Board's activity history is submitted by a requester who does not hold the Member or Admin role on that Board, including a Guest, THEN THE Access_Control_Service SHALL reject the request with an authorization error and SHALL return no Activity_Entries.
15. IF a Member requests a page of the activity history with a page index that is negative or that exceeds the index of the last available page, THEN THE Activity_Service SHALL return an empty page of Activity_Entries.

### Requirement 9: Board Analytics

**User Story:** As a Member, I want to view analytics for a Board, so that I can understand task distribution and completion progress.

#### Acceptance Criteria

1. WHEN a Member requests analytics for a Board, THE Analytics_Service SHALL return the total count of Cards on the Board as a non-negative integer.
2. WHEN a Member requests analytics for a Board, THE Analytics_Service SHALL return, for each Column of the Board, the Column identifier and the count of Cards in that Column as a non-negative integer.
3. WHEN a Member requests analytics for a Board that contains at least one Column named "Done" and at least one Card, THE Analytics_Service SHALL return a task completion rate computed as the sum of the counts of Cards across all Columns whose name is "Done" divided by the total number of Cards on the Board, expressed as a decimal value in the closed range 0.0 to 1.0.
4. IF a Member requests analytics for a Board that contains zero Cards, THEN THE Analytics_Service SHALL return a total Card count of zero, a Card count of zero for each Column, and a task completion rate of zero.
5. WHEN a Member requests analytics for a Board, THE Analytics_Service SHALL return the count of Activity_Entries grouped by calendar day, where day boundaries are determined in UTC.
6. IF a Member requests analytics for a Board that contains no Column named "Done", THEN THE Analytics_Service SHALL return a task completion rate of zero.

### Requirement 10: Board Members and Roles

**User Story:** As an Admin, I want to manage Board members and their roles, so that I can control who can access and modify a Board.

#### Acceptance Criteria

1. WHEN an Admin invites a User who is a Team_Member of the Board's Team and is not already a Member of the Board, with a specified role that is either Member or Admin, THE Access_Control_Service SHALL grant the User the specified role on the Board.
2. WHEN an Admin removes a Member from a Board, THE Access_Control_Service SHALL revoke the removed Member's access to the Board for every subsequent request.
3. WHEN an Admin changes a Member's role on a Board, THE Access_Control_Service SHALL apply the permissions of the new role to every request the Member submits after the change.
4. IF an Admin submits a member invitation request specifying a role that is neither Member nor Admin, THEN THE Access_Control_Service SHALL reject the request with a validation error indicating the role is invalid and SHALL leave Board membership unchanged.
5. IF an Admin submits a member invitation request for a User who is already a Member of the Board, THEN THE Access_Control_Service SHALL reject the request with a validation error indicating the User is already a Member and SHALL leave Board membership unchanged.
6. IF an Admin submits a member removal or role change request that would leave the Board with zero Admins, THEN THE Access_Control_Service SHALL reject the request with a validation error indicating the Board must retain at least one Admin and SHALL leave Board membership unchanged.
7. IF a User without the Admin role submits a member invitation, removal, or role change request, THEN THE Access_Control_Service SHALL reject the request with an authorization error and SHALL leave Board membership unchanged.
8. IF an Admin submits a member invitation request for a User who is not a Team_Member of the Board's Team, THEN THE Access_Control_Service SHALL reject the request with a validation error indicating the User is not a Team_Member and SHALL leave Board membership unchanged.

### Requirement 11: Invitation Links and Guest Access

**User Story:** As an Admin, I want to generate and revoke Invitation_Links, so that I can share a Board with Guests in a controlled manner.

#### Acceptance Criteria

1. WHEN an Admin generates an Invitation_Link for a Board, THE Access_Control_Service SHALL create an active Invitation_Link that is uniquely identifiable, bound to exactly that Board, and SHALL return the Invitation_Link token to the requesting Admin.
2. WHEN an Admin revokes an Invitation_Link identified by its token, THE Access_Control_Service SHALL set that Invitation_Link status to inactive and SHALL leave the status of all other Invitation_Links unchanged.
3. WHEN a request presents an active Invitation_Link token, THE Access_Control_Service SHALL, without requiring authentication, grant read access to the Board's name and description and to its Columns, Cards, and Comments, and SHALL reject any write operation on that Board.
4. IF a Guest, including a request that presents only an Invitation_Link token without authentication, submits a request to create, edit, delete, or move a Card, or to create, edit, or delete a Comment, or to perform any Column, member, settings, or Board lifecycle operation, THEN THE Access_Control_Service SHALL reject the request with an authorization error and SHALL leave the affected resource unchanged.
5. IF a Guest accesses a Board through an inactive Invitation_Link, THEN THE Access_Control_Service SHALL reject the access request with an authorization error.
6. IF a request presents an Invitation_Link token that does not match any Invitation_Link, THEN THE Access_Control_Service SHALL reject the access request with an authorization error.
7. IF a User without the Admin role submits an Invitation_Link generation or revocation request, THEN THE Access_Control_Service SHALL reject the request with an authorization error and SHALL leave all Invitation_Links unchanged.

### Requirement 12: Role-Based Access Control

**User Story:** As a Team, we want access to each Board governed by role-based access control, so that each User can perform only the actions permitted by their role.

#### Acceptance Criteria

1. WHEN THE System receives a request to act on a Board, THE Access_Control_Service SHALL determine the requesting User's role on that Board from the stored Board membership at the time of the request and, IF the role permits the requested operation, SHALL forward the request to the target service for execution.
2. WHILE a requester holds the Guest role on a Board, THE Access_Control_Service SHALL permit read retrieval operations on Columns, Cards, and Comments, and SHALL reject create, edit, delete, move, and reorder operations on Columns, Cards, and Comments with an authorization error and SHALL leave that Board unchanged.
3. WHILE a User holds the Member role on a Board, THE Access_Control_Service SHALL permit Card operations, Comment operations, search, notification retrieval, and analytics retrieval, and SHALL reject Column management, member management, and Board settings operations.
4. WHILE a User holds the Admin role on a Board, THE Access_Control_Service SHALL permit all Member operations and SHALL permit Column management, member management, Board settings, and Board lifecycle operations.
5. IF a request references a Board on which the requesting User holds no role and presents no active Invitation_Link, THEN THE Access_Control_Service SHALL reject the request with an authorization error and SHALL leave that Board unchanged.
6. IF THE System receives a request from an unauthenticated User, THEN THE Access_Control_Service SHALL reject the request with an authentication error before evaluating any Board role, except a request that presents an Invitation_Link token, which is governed by Requirement 11.

### Requirement 13: Concurrency Control

**User Story:** As a Member, I want simultaneous updates to be detected, so that my changes are not silently overwritten by another User's changes.

#### Acceptance Criteria

1. WHEN a Member retrieves a Card or Comment, THE System SHALL include the current version identifier of the retrieved resource.
2. IF a Member submits an update whose supplied version identifier does not match the current version identifier of the resource, THEN THE System SHALL reject the update with a conflict error indicating a version conflict and SHALL leave the resource unchanged.
3. WHEN a Member submits an update whose supplied version identifier matches the current version identifier, THE System SHALL apply the update and SHALL assign a new version identifier that is distinct from every prior version identifier of that resource.
4. WHEN a Card or Comment is created, THE System SHALL assign the resource an initial version identifier.
5. IF a Member submits an update that supplies no version identifier, THEN THE System SHALL reject the update with a conflict error indicating a missing version identifier and SHALL leave the resource unchanged.
6. THE System SHALL NOT require a version identifier for Card move, Card reorder, Card deletion, or Comment deletion requests, and SHALL NOT change a Card's version identifier as a result of a move or reorder.

### Requirement 14: Non-Functional Requirements

**User Story:** As a Team, we want the application to meet defined performance, availability, and usability targets, so that it is dependable for daily collaborative use.

#### Acceptance Criteria

1. WHILE THE System serves up to 100 concurrent active Users, WHEN THE System processes API requests other than search, analytics, and Board permanent deletion requests, THE System SHALL return responses within 300 milliseconds for at least 95 percent of those requests measured over each rolling one-hour window.
2. THE System SHALL maintain at least 99.5 percent availability measured over each calendar month, where availability is the percentage of one-minute intervals in which the System returns a successful response to a health-check request.
3. WHERE a client viewport width is at least 1024 pixels, THE System SHALL render the Board layout such that all Columns, Cards, and primary navigation are reachable without horizontal page scrolling.
4. WHERE a client viewport width is less than 1024 pixels, THE System SHALL render a layout in which all interactive controls remain visible and operable without horizontal page scrolling and without content overlapping.
5. WHILE at least two Users act on distinct Boards or distinct Cards simultaneously, THE System SHALL apply each User's changes independently so that no change is lost and each affected resource reflects the applied changes on subsequent retrieval.

### Requirement 15: User Authentication

**User Story:** As a new user, I want to create an account using my email and password, so that I can access the system as a registered user.

#### Acceptance Criteria

1. WHEN a User submits valid registration details, THE Authentication_Service SHALL create a new User account and store the User's password using a secure password hashing algorithm.
2. WHEN a registered User submits valid login credentials, THE Authentication_Service SHALL issue a short-lived Access_Token that is a JSON Web Token containing the User's identity, and SHALL issue a Refresh_Token.
3. IF a User submits invalid login credentials, THEN THE Authentication_Service SHALL reject the request with an authentication error without revealing whether the email or password was incorrect.
4. WHEN a login attempt for an account fails and that failure is the third consecutive failed login attempt for that account, THE Authentication_Service SHALL lock the account for 15 minutes starting at the time of the third consecutive failure.
5. WHILE an account is locked, THE Authentication_Service SHALL reject every login attempt for that account with an authentication error and SHALL issue no Access_Token or Refresh_Token, regardless of whether the submitted credentials are correct, and the authentication error SHALL NOT reveal whether the account is locked.
6. WHEN a User completes a successful login, THE Authentication_Service SHALL reset that account's consecutive failed login attempt count to zero.
7. WHEN the 15-minute lockout period for an account has elapsed, THE Authentication_Service SHALL permit subsequent login attempts for that account and SHALL reset that account's consecutive failed login attempt count to zero.
8. WHEN an authenticated User submits a logout request, THE Authentication_Service SHALL revoke the User's Refresh_Token so that it can no longer be used to mint an Access_Token.
9. IF an unauthenticated User attempts to access a protected resource other than a request governed by Requirement 11, THEN THE Authentication_Service SHALL reject the request with an authentication error.
10. WHEN an authenticated User submits a request bearing an expired or invalid Access_Token, THE Authentication_Service SHALL reject the request with an authentication error.
11. WHEN the Authentication_Service receives a token refresh request presenting a valid, non-revoked Refresh_Token, THE Authentication_Service SHALL issue a new short-lived Access_Token containing the User's identity.
12. IF a token refresh request presents a Refresh_Token that is revoked, expired, or invalid, THEN THE Authentication_Service SHALL reject the request with an authentication error and SHALL issue no Access_Token.
13. THE Authentication_Service SHALL NOT embed Board or Team role assignments in an Access_Token; the Access_Control_Service determines roles from stored membership for each request.
14. WHEN a User submits a registration request, THE Authentication_Service SHALL require an email address in a valid email format, a password of at least 8 characters, and a display name containing 1 to 50 characters after trimming leading and trailing whitespace.
15. IF a User submits a registration request with an email that is already associated with an existing account, THEN THE Authentication_Service SHALL reject the request with a validation error indicating the email is already registered and SHALL create no new account.
16. IF a User submits a registration request with an email that is not in a valid email format, a password shorter than 8 characters, or a display name that is empty after trimming leading and trailing whitespace or exceeds 50 characters, THEN THE Authentication_Service SHALL reject the request with a validation error indicating the invalid field and SHALL create no new account.

### Requirement 16: Team Management

**User Story:** As a User, I want to create a Team and see its members, so that I can organize Boards with the people I work with.

#### Acceptance Criteria

1. WHEN a User submits a Team creation request with a Team name containing 1 to 100 characters after trimming leading and trailing whitespace, THE Team_Service SHALL create the Team, make the requesting User a Team_Member with the Team_Role Team_Admin, and return the created Team identifier.
2. IF a User submits a Team creation request whose Team name is empty after trimming or exceeds 100 characters, THEN THE Team_Service SHALL reject the request with a validation error indicating the invalid Team name and SHALL create no Team.
3. WHEN a User requests the list of Teams, THE Team_Service SHALL return only the Teams of which the requesting User is a Team_Member.
4. WHEN a Team_Member requests the members of a Team, THE Team_Service SHALL return each Team_Member's User identifier, display name, and Team_Role.
5. IF a User who is not a Team_Member of a Team requests that Team's members, THEN THE Access_Control_Service SHALL reject the request with an authorization error and SHALL return no member data.
6. THE Team_Service SHALL evaluate Team membership and Team_Role against the stored membership at the time of each request.

### Requirement 17: Team Join Links

**User Story:** As a Team_Admin, I want to generate and revoke Team_Join_Links, so that I can bring people into my Team in a controlled manner.

#### Acceptance Criteria

1. WHEN a Team_Admin generates a Team_Join_Link for a Team, THE Team_Service SHALL create an active Team_Join_Link that is uniquely identifiable, bound to exactly that Team, and expires 7 days after creation, and SHALL return the Team_Join_Link token to the requesting Team_Admin.
2. WHEN a Team_Admin revokes a Team_Join_Link identified by its token, THE Team_Service SHALL set that Team_Join_Link status to inactive and SHALL leave the status of all other Team_Join_Links unchanged.
3. WHEN an authenticated User accepts an active, unexpired Team_Join_Link, THE Team_Service SHALL make the User a Team_Member of the bound Team with the Team_Role Team_Regular, effective for the User's subsequent requests, and SHALL return the Team identifier.
4. IF a User accepts a token that matches no Team_Join_Link, or that identifies an inactive or expired Team_Join_Link, THEN THE Team_Service SHALL reject the request with a validation error indicating the Team_Join_Link is invalid and SHALL leave Team membership unchanged.
5. IF a User who is already a Team_Member of the bound Team accepts the Team_Join_Link, THEN THE Team_Service SHALL reject the request with a validation error indicating the User is already a Team_Member and SHALL leave the User's Team_Role unchanged.
6. IF a User who does not hold the Team_Role Team_Admin submits a Team_Join_Link generation or revocation request, THEN THE Access_Control_Service SHALL reject the request with an authorization error and SHALL leave all Team_Join_Links unchanged.
7. IF an unauthenticated User submits a Team_Join_Link acceptance request, THEN THE Access_Control_Service SHALL reject the request with an authentication error and SHALL leave Team membership unchanged.