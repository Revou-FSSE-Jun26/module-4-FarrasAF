---
inclusion: fileMatch
fileMatchPattern: ["backend/flask_app/models/**/*.py", "backend/migrations/**/*.py"]
---

# Database Conventions (SQLAlchemy + PostgreSQL)

Entities, fields, and indexes are defined in the Data Models section of
`design.md`. This file defines how they are written.

## 1. Naming
**Rule:** Tables are plural snake_case; columns are snake_case; models are
PascalCase and singular; foreign keys are `<entity>_id`; membership and join
tables are plural (`team_memberships`). Constraints and indexes get
deterministic names from a `naming_convention` set on the metadata in
`extensions.py`.
**Rationale:** Predictable names, and stable Alembic migrations.
**Example:** model `BoardMembership`, table `board_memberships`, column `board_id`.

## 2. Base columns
**Rule:** Every model inherits `BaseModel` from `models/base.py`, which
defines exactly these four columns. Never redefine them in a model, except
the Card `updated_at` exception in rule 3.
**Rationale:** One consistent shape for every table.
**Example:**
```python
class BaseModel(db.Model):
    __abstract__ = True
    id = db.Column(db.Uuid, primary_key=True, default=uuid.uuid4)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False,
                           default=utc_now, onupdate=utc_now)
    deleted_at = db.Column(db.DateTime(timezone=True), nullable=True)
```

## 3. Timestamps
**Rule:** All timestamps are timezone-aware UTC, produced by `utc_now()` in
`flask_app/common/time.py` (`datetime.now(timezone.utc)`). Never use
`datetime.utcnow()` or naive datetimes. Exception: `Card` defines its own
`updated_at` with `default=utc_now` and NO `onupdate`; `Card_Service` sets it
explicitly: on creation `created_at` and `updated_at` share one value (R3.1),
on edit and on move only that Card's `updated_at` is set (R3.3, R4.7), and
reindexing other Cards never changes their `updated_at`.
**Rationale:** `onupdate` would bump the `updated_at` of every Card shifted by
reindexing, which breaks R4.7 and the search ordering in R7.6.
**Example:** `card.updated_at = now` where `now = utc_now()` is also used for
`card.created_at` on creation.

## 4. Data types
**Rule:** Use these types:
- Short strings (names, titles, email, display name): `db.String(255)`
- Long text (descriptions, comment bodies): `db.Text`
- Card and Column order index: `db.Integer`
- Hashed passwords (and other hashes): `db.String(255)`
- `version`: `db.Integer`, not null, default 1
- Enum-like values (roles, status, event type): `db.String(50)` plus a
  `CheckConstraint` listing the allowed values
- Foreign keys to a `BaseModel` table: `db.Uuid`
Length limits from the requirements (for example Board name 100, Card Title
255, Comment 5000) are enforced in the service layer, not by column length.
**Rationale:** Simple portable types; business limits live in one place.
**Example:** `name = db.Column(db.String(255), nullable=False)`

## 5. Relationships
**Rule:** Define every relationship on both sides with `db.relationship()`,
linked by `back_populates`, and always set `lazy` explicitly. Use
`lazy="select"` for single parents, `lazy="selectin"` for collections that
list endpoints load (to avoid N+1), and never `lazy="dynamic"`. Set
`cascade="all, delete-orphan"` and `passive_deletes=True` on the parent side
of cascading collections.
**Rationale:** Both sides stay visible to `mypy`, and loading behavior is
explicit.
**Example:**
```python
class Board(BaseModel):
    columns = db.relationship("Column", back_populates="board", lazy="selectin",
                              cascade="all, delete-orphan", passive_deletes=True,
                              order_by="Column.order_index")

class Column(BaseModel):
    board_id = db.Column(db.Uuid, db.ForeignKey("boards.id", ondelete="CASCADE"),
                         nullable=False, index=True)
    board = db.relationship("Board", back_populates="columns", lazy="select")
```

## 6. Constraints, ordering, and cascades
**Rule:**
- Primary keys are UUID v4. Ordering and tie-breaks by `id` only need to be
  deterministic, not chronological.
- Uniqueness of order positions, `(board_id, order_index)` for Columns and
  `(column_id, order_index)` for Cards, is `DEFERRABLE INITIALLY DEFERRED`,
  so a reindex inside one transaction does not violate it mid-statement.
- Cascades follow `design.md`: deleting a Board cascades to its Columns, Cards,
  Comments, Notifications, memberships, Invitation_Links, and Activity_Entries,
  declared with `ondelete="CASCADE"`. Other foreign keys keep the default
  (restrict).
- `ActivityEntry.resource_id` is not a foreign key, because its target may
  already be deleted.
- Add an index on every foreign key used for filtering, plus the indexes
  listed in `design.md`.
**Rationale:** Prevents reindex failures and leftover rows after deletes (R1.6).
**Example:**
```python
db.UniqueConstraint("column_id", "order_index", deferrable=True, initially="DEFERRED")
```

## 7. Deletion
**Rule:** All deletions in the requirements are hard deletes (R1.6, R2.5,
R3.5, R5.4). `deleted_at` exists on every table by project convention but is
unused in V1: it stays NULL, and no query filters on it. Do not implement soft
delete, trash, or restore.
**Rationale:** Soft delete would break permanent deletion and the unique
constraints on ordering, email, and membership.
**Example:** `db.session.delete(card)`, not `card.deleted_at = utc_now()`.

## 8. Migrations
**Rule:** Generate with `flask --app flask_app.app db migrate -m "<message>"`,
then review the file by hand before applying: autogenerate can miss
`CheckConstraint` and deferrable constraints. One logical change per migration,
every migration has a working `downgrade`, and applied migrations are never
edited. Models contain no business logic.
**Rationale:** Reviewed, reversible, reproducible schema changes.
**Example:** a new column means a new migration, not an edit to an old one.

## 9. Identifiers in code
**Rule:** IDs are UUIDs. Use `<uuid:...>` route converters so a malformed ID
returns 404 instead of a server error, and serialize IDs as strings. Timestamps
are serialized as ISO 8601 UTC with `Z` by `common/serialization.py`.
**Rationale:** Flask's default JSON provider formats datetimes in a non-ISO
style, which would mismatch the frontend types.
**Example:** `@cards_bp.post('/api/columns/<uuid:column_id>/cards')`---
inclusion: fileMatch
fileMatchPattern: ["backend/flask_app/models/**/*.py", "backend/migrations/**/*.py"]
---

# Database Conventions (SQLAlchemy + PostgreSQL)

Entities, fields, and indexes are defined in the Data Models section of
`design.md`. This file defines how they are written.

## 1. Naming
**Rule:** Tables are plural snake_case; columns are snake_case; models are
PascalCase and singular; foreign keys are `<entity>_id`; membership and join
tables are plural (`team_memberships`). Constraints and indexes get
deterministic names from a `naming_convention` set on the metadata in
`extensions.py`.
**Rationale:** Predictable names, and stable Alembic migrations.
**Example:** model `BoardMembership`, table `board_memberships`, column `board_id`.

## 2. Base columns
**Rule:** Every model inherits `BaseModel` from `models/base.py`, which
defines exactly these four columns. Never redefine them in a model, except
the Card `updated_at` exception in rule 3.
**Rationale:** One consistent shape for every table.
**Example:**
```python
class BaseModel(db.Model):
    __abstract__ = True
    id = db.Column(db.Uuid, primary_key=True, default=uuid.uuid4)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False,
                           default=utc_now, onupdate=utc_now)
    deleted_at = db.Column(db.DateTime(timezone=True), nullable=True)
```

## 3. Timestamps
**Rule:** All timestamps are timezone-aware UTC, produced by `utc_now()` in
`flask_app/common/time.py` (`datetime.now(timezone.utc)`). Never use
`datetime.utcnow()` or naive datetimes. Exception: `Card` defines its own
`updated_at` with `default=utc_now` and NO `onupdate`; `Card_Service` sets it
explicitly: on creation `created_at` and `updated_at` share one value (R3.1),
on edit and on move only that Card's `updated_at` is set (R3.3, R4.7), and
reindexing other Cards never changes their `updated_at`.
**Rationale:** `onupdate` would bump the `updated_at` of every Card shifted by
reindexing, which breaks R4.7 and the search ordering in R7.6.
**Example:** `card.updated_at = now` where `now = utc_now()` is also used for
`card.created_at` on creation.

## 4. Data types
**Rule:** Use these types:
- Short strings (names, titles, email, display name): `db.String(255)`
- Long text (descriptions, comment bodies): `db.Text`
- Card and Column order index: `db.Integer`
- Hashed passwords (and other hashes): `db.String(255)`
- `version`: `db.Integer`, not null, default 1
- Enum-like values (roles, status, event type): `db.String(50)` plus a
  `CheckConstraint` listing the allowed values
- Foreign keys to a `BaseModel` table: `db.Uuid`
Length limits from the requirements (for example Board name 100, Card Title
255, Comment 5000) are enforced in the service layer, not by column length.
**Rationale:** Simple portable types; business limits live in one place.
**Example:** `name = db.Column(db.String(255), nullable=False)`

## 5. Relationships
**Rule:** Define every relationship on both sides with `db.relationship()`,
linked by `back_populates`, and always set `lazy` explicitly. Use
`lazy="select"` for single parents, `lazy="selectin"` for collections that
list endpoints load (to avoid N+1), and never `lazy="dynamic"`. Set
`cascade="all, delete-orphan"` and `passive_deletes=True` on the parent side
of cascading collections.
**Rationale:** Both sides stay visible to `mypy`, and loading behavior is
explicit.
**Example:**
```python
class Board(BaseModel):
    columns = db.relationship("Column", back_populates="board", lazy="selectin",
                              cascade="all, delete-orphan", passive_deletes=True,
                              order_by="Column.order_index")

class Column(BaseModel):
    board_id = db.Column(db.Uuid, db.ForeignKey("boards.id", ondelete="CASCADE"),
                         nullable=False, index=True)
    board = db.relationship("Board", back_populates="columns", lazy="select")
```

## 6. Constraints, ordering, and cascades
**Rule:**
- Primary keys are UUID v4. Ordering and tie-breaks by `id` only need to be
  deterministic, not chronological.
- Uniqueness of order positions, `(board_id, order_index)` for Columns and
  `(column_id, order_index)` for Cards, is `DEFERRABLE INITIALLY DEFERRED`,
  so a reindex inside one transaction does not violate it mid-statement.
- Cascades follow `design.md`: deleting a Board cascades to its Columns, Cards,
  Comments, Notifications, memberships, Invitation_Links, and Activity_Entries,
  declared with `ondelete="CASCADE"`. Other foreign keys keep the default
  (restrict).
- `ActivityEntry.resource_id` is not a foreign key, because its target may
  already be deleted.
- Add an index on every foreign key used for filtering, plus the indexes
  listed in `design.md`.
**Rationale:** Prevents reindex failures and leftover rows after deletes (R1.6).
**Example:**
```python
db.UniqueConstraint("column_id", "order_index", deferrable=True, initially="DEFERRED")
```

## 7. Deletion
**Rule:** All deletions in the requirements are hard deletes (R1.6, R2.5,
R3.5, R5.4). `deleted_at` exists on every table by project convention but is
unused in V1: it stays NULL, and no query filters on it. Do not implement soft
delete, trash, or restore.
**Rationale:** Soft delete would break permanent deletion and the unique
constraints on ordering, email, and membership.
**Example:** `db.session.delete(card)`, not `card.deleted_at = utc_now()`.

## 8. Migrations
**Rule:** Generate with `flask --app flask_app.app db migrate -m "<message>"`,
then review the file by hand before applying: autogenerate can miss
`CheckConstraint` and deferrable constraints. One logical change per migration,
every migration has a working `downgrade`, and applied migrations are never
edited. Models contain no business logic.
**Rationale:** Reviewed, reversible, reproducible schema changes.
**Example:** a new column means a new migration, not an edit to an old one.

## 9. Identifiers in code
**Rule:** IDs are UUIDs. Use `<uuid:...>` route converters so a malformed ID
returns 404 instead of a server error, and serialize IDs as strings. Timestamps
are serialized as ISO 8601 UTC with `Z` by `common/serialization.py`.
**Rationale:** Flask's default JSON provider formats datetimes in a non-ISO
style, which would mismatch the frontend types.
**Example:** `@cards_bp.post('/api/columns/<uuid:column_id>/cards')`