---
inclusion: fileMatch
fileMatchPattern: "app/blueprints/**/*"
---

# Backend Guidelines (Flask)

## Blueprint Structure

- RULE: Each feature is a Blueprint under app/blueprints/<feature>/ with routes.py, service.py, schema.py.
  RATIONALE: Identical layout per feature; the agent always knows where code goes.
  EXAMPLE: app/blueprints/cards/{routes,service,schema}.py
- RULE: A route handler is <= 5 lines: validate, call a service, return the envelope. No business logic.
  RATIONALE: Thin handlers keep logic in testable services.
  EXAMPLE: reorder_card() loads via schema, calls move_card(), returns { "data": card }

## Input Validation

- RULE: Every JSON body is validated by a Marshmallow schema before the service runs; failure -> 400 { "error": { field: msg } }.
  RATIONALE: Bad input never reaches the database.
  EXAMPLE: CreateCardSchema validates title (1..255) and column_id (UUID)

## Response Envelope

- RULE: Success -> { "data": ... }; error -> { "error": ... }.
  RATIONALE: The frontend parses every response identically.
  EXAMPLE: GET /api/boards/<id> -> { "data": { ...board, columns: [...] } }

## Authentication

- RULE: @token_required on every route except POST /api/auth/register and POST /api/auth/login.
  RATIONALE: Protected resources reject unauthenticated requests with 401 before the handler runs.
  EXAMPLE: PATCH /api/cards/<id>/position carries @token_required

## Error Handling

- RULE: Services raise typed exceptions (app/exceptions.py); one global handler maps them to status + { "error" }; never a traceback.
  RATIONALE: One place owns error->HTTP mapping; clients always get JSON.
  EXAMPLE: CardNotFoundException -> 404 { "error": "Card not found" }