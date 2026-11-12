---
inclusion: always
---

# Card Conventions (task-management-app)

## 1. Thin route handlers
**Rule:** Route handlers only authorize, parse the request, call one service
function, and return the response (max 5 lines). No business logic or
validation in the handler. Request bodies are read with `read_json()` and
responses built with `json_response()`, both from `common/serialization.py`;
they convert camelCase JSON to snake_case and back. Services only receive
and return snake_case data and never rename fields themselves.
**Rationale:** Logic in a service is unit-testable without an HTTP request,
and field-name conversion lives in exactly one place.
**Example:**
```python
@cards_bp.post('/api/columns/<column_id>/cards')
@require_role('member')
def create_card(column_id):
    card = create_card_service(column_id, read_json(), current_user())
    return json_response(card, 201)
```

## 2. Typed errors
**Rule:** Services raise a subclass of `AppError` from `exceptions.py`
(`ValidationError`, `NotFoundError`, `ConflictError`, `AuthorizationError`,
`AuthenticationError`). Never raise a bare `AppError` or return error dicts.
A central handler maps them to `{ "error": { "code", "message", "field?" } }`.
**Rationale:** One error type maps to one consistent JSON response and HTTP status.
**Example:** `raise ValidationError('Card title is required', field='title')`

## 3. Naming
**Rule:** Handlers and services are snake_case; services end with `_service`;
tables are plural_snake_case; Models are PascalCase and singular (`Card`).
**Rationale:** Predictable names; matches PEP 8 and SQL conventions.
**Example:** `create_card_service()`; table `cards`

## 4. Card domain rules
**Rule:** Card logic must always satisfy these invariants:
- Title is trimmed, 1-255 chars; Description max 5000 chars.
- A new Card is appended at the end of its Column.
- After create, delete, move, or reorder, `order_index` in every affected
  Column is contiguous from 0 (use the shared `reindex()` helper).
- Assignee must be a current Member of the Card's Board.
- Card edits (PATCH) require `version`; a mismatch or missing value raises
  `ConflictError`. A successful edit sets `updated_at` and increments `version`.
- A multi-field edit is atomic: any invalid field rejects the whole request.
- An Activity_Entry is written in the same transaction as the mutation.
- A move target must be a Column of the same Board, and the target index
  must be an integer from 0 to the number of Cards in the target Column
  after the moved Card is removed from its source.
- Activity event types: `card_created`, `card_updated`, `card_moved`,
  `card_deleted`.
**Rationale:** These are the invariants most likely to be broken by generated code.
**Example:** `move_card_service(card_id, target_column_id, target_index, actor)`
validates the target, moves the Card, calls `reindex()` on the source and
target Columns, and records "card moved", all in one transaction.

## 5. Tests
**Rule:** Every service function ships with a pytest unit test. Invariants in
rule 4 are also covered by Hypothesis property tests per `design.md`. Tests live in `backend/tests/unit/test_<module>.py`.
**Rationale:** No untested business logic enters the codebase.
**Example:**
```python
def test_create_card_service_appends_to_end(db_session, member, column):
    card = create_card_service(column.id, {'title': 'Task'}, member)
    assert card['order_index'] == 0
```