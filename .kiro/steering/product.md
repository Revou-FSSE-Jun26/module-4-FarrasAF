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
- Individuals using it for personal task tracking (a Team with a single Admin)

## Roles
- **Admin**: all Member capabilities, plus managing Boards, Columns, members, settings, and Invitation Links
- **Member**: works with Cards, Comments, search, Notifications, and analytics
- **Guest**: read-only access through an active Invitation Link

## Core Value
- **User-friendly**: the main workflow is understandable without a tutorial
- **Fast**: responsive UI and quick API responses (target: 95% of regular
  requests under 300 ms). "Fast" does not mean real-time sync.
- **Simple**: a deliberately small feature set

## Core Features (V1)
- Boards with ordered Columns and Cards
- Drag-and-drop Card movement and ordering
- Threaded Comments with @Mentions and Mention Notifications
- Card search by title
- Activity Log and basic Board Analytics
- Role-based access control and Invitation Links for Guests
- Email and password authentication

## Non-Goals (V1)
Do not implement or suggest these unless a spec explicitly adds them:
- File attachments
- Email notifications
- Third-party integrations
- Advanced analytics and burndown charts
- Real-time collaboration (WebSockets); Notifications use HTTP polling
- Password reset and email verification (no email in V1)
- Card labels, checklists, priorities, or multiple Assignees
- Cross-Board Card moves, Card archiving, or Board templates

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
- **Team**: a group of Users that owns Boards
- **Board**: a workspace containing ordered Columns
- **Column**: an ordered container of Cards (default: To Do, Doing, Done). Analytics treats Columns named exactly "Done" as completed work.
- **Card**: a task with Title, Description, Assignee, and Due date
- **Comment**: a message on a Card, either top-level or a threaded reply
- **Mention**: a reference to a Member inside a Comment
- **Invitation Link**: a shareable token granting Guest access to one Board

See `card-conventions.md` for Card-specific rules.