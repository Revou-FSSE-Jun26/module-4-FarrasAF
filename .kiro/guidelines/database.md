---
inclusion: manual
---

# Database Guidelines (PostgreSQL)

This document defines database modeling conventions and implementation rules for all database models using PostgreSQL and SQLAlchemy.

All models must follow these guidelines to maintain consistency, readability, and predictable database behavior across the application.

## 1. Naming Conventions

### Rule
- Model table names must use plural nouns in `snake_case`.
- Column names must use singular nouns in `snake_case`.
- SQLAlchemy models must explicitly define their table name using `__tablename__`.
- Avoid abbreviations unless they are widely recognized and unambiguous.

### Rationale
Consistent naming conventions make database schemas easier to understand, navigate, and maintain. Using plural table names represents collections of records, while singular column names describe individual attributes.

### Example

```python
class CardEntity(db.Model):
    __tablename__ = "cards"

    column_id = db.Column(db.UUID, nullable=False)
    card_title = db.Column(db.String(255), nullable=False)
```

## 2. Required Columns

### Rule
Every model must define the following four standard columns:

| Column | Data Type | Constraint / Default |
|---|---|---|
| `id` | `db.UUID` | Primary key, default `uuid.uuid4` |
| `created_at` | `db.DateTime` | Non-nullable, default current UTC time |
| `updated_at` | `db.DateTime` | Non-nullable, default current UTC time, updated automatically |
| `deleted_at` | `db.DateTime` | Nullable, default `None` |

Additional requirements:
- UUIDs must be generated using Python's `uuid.uuid4`.
- Timestamp values must use UTC.
- `created_at` must represent when the record was initially created.
- `updated_at` must be updated whenever the record changes.
- `deleted_at` must be used to support soft deletion instead of immediately removing records.

### Rationale
Standardized metadata columns provide consistent record identification, auditing, and lifecycle management across all entities.

Using soft deletion preserves historical records and allows recovery or auditing when necessary.

### Example

```python
import uuid
from datetime import datetime, timezone

class CardEntity(db.Model):
    __tablename__ = "cards"

    id = db.Column(
        db.UUID,
        primary_key=True,
        default=uuid.uuid4
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    deleted_at = db.Column(
        db.DateTime(timezone=True),
        nullable=True,
        default=None
    )
```

## 3. Data Types

### Rule
Use the following standardized SQLAlchemy data types:

| Field | Data Type |
|---|---|
| `title` | `db.String(255)` |
| `description` | `db.Text` |
| `position` | `db.Integer` |
| Password fields | `db.String(255)` |

Additional requirements:
- Use `db.String(length)` for character fields with a defined maximum length.
- Use `db.Text` for long-form text without a predefined character limit.
- Use `db.Integer` for whole-number values.
- Password fields must store hashed passwords, never plaintext passwords.
- Select other data types based on the actual nature and constraints of the data.

### Rationale
Standardized data types improve schema consistency, prevent unnecessary storage constraints, and make the intended use of each column clear.

Password hashing is mandatory to prevent storing sensitive credentials in plaintext.

### Example

```python
class UserEntity(db.Model):
    __tablename__ = "users"

    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    position = db.Column(db.Integer, nullable=False)

    password = db.Column(db.String(255), nullable=False)
```

## 4. Relationships

### Rule
- Define relationships on both sides of the relationship whenever applicable.
- Use `db.relationship()` to declare ORM relationships.
- Explicitly define the relationship's `backref` and `lazy` loading strategy.
- Foreign key columns must reference the correct target table and column.
- Relationship names must clearly describe the related entity.
- Avoid creating relationships without a corresponding foreign key unless there is a specific architectural reason.

### Rationale
Explicitly defined relationships make entity associations easier to understand and maintain.

Defining both sides ensures that related records can be accessed consistently from either entity. Explicit loading strategies also make database access behavior more predictable.

### Example

```python
class BoardColumnEntity(db.Model):
    __tablename__ = "board_columns"

    id = db.Column(
        db.UUID,
        primary_key=True,
        default=uuid.uuid4
    )

    cards = db.relationship(
        "CardEntity",
        backref=db.backref(
            "board_column",
            lazy="select"
        ),
        lazy="select"
    )


class CardEntity(db.Model):
    __tablename__ = "cards"

    id = db.Column(
        db.UUID,
        primary_key=True,
        default=uuid.uuid4
    )

    board_column_id = db.Column(
        db.UUID,
        db.ForeignKey("board_columns.id"),
        nullable=False
    )
```

**Note:** The example uses `backref` to automatically create the reverse relationship. Do not define a second explicit relationship for the same association when using this approach. If using `back_populates` instead, define it explicitly on both sides.

---

## 5. General Guidelines

### Rule
- Every model must follow the conventions defined in this document.
- Use explicit column constraints such as `nullable`, `unique`, and `index` when required by the business rules.
- Define foreign key constraints for relational references.
- Avoid duplicating data across tables unless there is a clear architectural justification.
- Ensure that database changes are managed through migrations.
- Do not modify the database schema manually outside the migration workflow.

### Rationale
Consistent schema definitions and migration practices reduce unexpected database behavior, prevent schema drift, and make changes easier to review and deploy.

### Example

```python
class UserEntity(db.Model):
    __tablename__ = "users"

    id = db.Column(
        db.UUID,
        primary_key=True,
        default=uuid.uuid4
    )

    email = db.Column(
        db.String(255),
        nullable=False,
        unique=True,
        index=True
    )
```

