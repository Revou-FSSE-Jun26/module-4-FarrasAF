---
inclusion: always
---

# Product Overview

## Purpose
A collaborative, Trello-inspired task management web app. Work is organized
into Boards, Columns, and Cards, where each Card represents a task that moves
across Columns as it progresses.

## Target Users
- Small to medium teams, startups, and organizations that need a simple
  shared workspace (not an enterprise tool like Jira)
- Individuals using it for personal task tracking (their own Team of one)

## Roles
Board roles (per Board):
- **Admin**: all Member capabilities, plus managing Columns, members, settings, Invitation Links, and the Board lifecycle
- **Member**: works with Cards, Comments, search, Notifications, and analytics
- **Guest**: anonymous read-only access to one Board through an active Invitation Link; no account needed

Team roles (per Team):
- **Team_Admin**: the User who created the Team; generates and revokes Team Join Links
- **Team_Regular**: a User who joined through a Team Join Link

Any Team member can create Boards in the Team and becomes that Board's Admin.
Board access comes only from Board membership, and only Team members can be added to a Board.

## Core Value
- **User-friendly**: the main workflow is understandable without a tutorial
- **Fast**: responsive UI and quick API responses (target: 95% of regular
  requests under 300 ms). "Fast" does not mean real-time sync.
- **Simple**: a deliberately small feature set

## Core Features (V1)
- Email and password authentication
- Teams: create a Team and bring people in through Team Join Links
- Boards with ordered Columns and Cards
- Drag-and-drop Card movement and ordering
- A to-do list on each Card (add, edit, tick, delete) with a progress bar
- File attachments on Cards, stored in Cloudinary (up to 5 files of 5 MB each; Members upload, the uploader or an Admin deletes; not visible to Guests)
- Threaded Comments with @Mentions and Mention Notifications
- Card search by title
- Activity Log and basic Board Analytics
- Role-based access control for Board members
- Invitation Links for anonymous, read-only Guests

## Non-Goals (V1)
Do not implement or suggest these unless a spec explicitly adds them:
- Email notifications
- Third-party integrations
- Advanced analytics and burndown charts
- Real-time collaboration (WebSockets); Notifications use HTTP polling
- Password reset and email verification (no email in V1)
- Card labels, priorities, or multiple Assignees
- Cross-Board Card moves, Card archiving, or Board templates
- Removing members from a Team, leaving a Team, changing Team roles, or renaming or deleting a Team
- Guest accounts (Guests are always anonymous and read-only)
- Board visibility behavior (the setting is stored but has no effect in V1)

## Product Principles
- Minimal clicks: creating and moving a Card should feel instant
- Drag-and-drop is the primary interaction for changing Card status
- Usable on desktop and mobile (breakpoint at 1024 px)
- Clear, actionable error messages
- Prefer the simplest solution that satisfies the requirements; no
  speculative features

## Success Criteria
- All V1 requirements implemented and traceable from spec to code
- Deployed to a public URL and demoable with seed data
- Clean, consistent, tested code that reflects the steering conventions
- Spec-driven workflow (requirements, design, tasks) documented clearly

## Domain Glossary
- **Team**: a group of Users created by a User; owns Boards
- **Team_Admin / Team_Regular**: the two Team roles, kept separate from the Board roles (Admin, Member, Guest)
- **Team Join Link**: a shareable, revocable token (valid 7 days) that lets a logged-in User join a Team as Team_Regular
- **Board**: a workspace containing ordered Columns
- **Column**: an ordered container of Cards (default: To Do, Doing, Done). Analytics treats Columns named exactly "Done" as completed work.
- **Card**: a task with Title, Description, Assignee, and Due date
- **Comment**: a message on a Card, either top-level or a threaded reply
- **Mention**: a reference to a Member inside a Comment
- **Invitation Link**: a shareable token granting anonymous, read-only Guest access to one Board; not the same as a Team Join Link

See `card-conventions.md` for Card-specific rules.