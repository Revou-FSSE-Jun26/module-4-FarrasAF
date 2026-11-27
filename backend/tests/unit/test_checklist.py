"""Unit tests for the Card to-do list service (R20)."""

import uuid
from collections.abc import Callable
from typing import Any

import pytest

from flask_app.cards.service import get_card_service
from flask_app.checklist.schema import CreateChecklistItemSchema, UpdateChecklistItemSchema
from flask_app.checklist.service import (
    MAX_CHECKLIST_ITEMS,
    create_checklist_item_service,
    delete_checklist_item_service,
    update_checklist_item_service,
)
from flask_app.common.exceptions import NotFoundError, ValidationError
from flask_app.common.validation import load_schema
from flask_app.models import Card


def test_text_is_trimmed_and_limited() -> None:
    assert load_schema(CreateChecklistItemSchema(), {"text": "  a  "})["text"] == "a"
    for bad in ("   ", "x" * 256):
        with pytest.raises(ValidationError):
            load_schema(CreateChecklistItemSchema(), {"text": bad})
    assert load_schema(UpdateChecklistItemSchema(), {"text": "x" * 255})


def test_is_done_must_be_a_boolean() -> None:
    assert load_schema(UpdateChecklistItemSchema(), {"is_done": True}) == {"is_done": True}
    with pytest.raises(ValidationError):
        load_schema(UpdateChecklistItemSchema(), {"is_done": "yes"})


def test_new_items_go_last_and_start_unchecked(
    db_session: Any, make_card: Callable[..., Card]
) -> None:
    card = make_card()
    first = create_checklist_item_service(card.id, {"text": "one"})
    second = create_checklist_item_service(card.id, {"text": "two"})
    assert first["is_done"] is False
    assert (first["order_index"], second["order_index"]) == (0, 1)
    # Deleting the first item must not make a later item reuse an index.
    delete_checklist_item_service(first["id"])
    third = create_checklist_item_service(card.id, {"text": "three"})
    assert third["order_index"] == 2
    items = get_card_service(card.id)["checklist_items"]
    assert [i["text"] for i in items] == ["two", "three"]


def test_update_changes_only_supplied_fields_and_keeps_card_version(
    db_session: Any, make_card: Callable[..., Card]
) -> None:
    card = make_card()
    version, updated_at = card.version, card.updated_at
    item = create_checklist_item_service(card.id, {"text": "one"})
    ticked = update_checklist_item_service(item["id"], {"is_done": True})
    assert (ticked["text"], ticked["is_done"]) == ("one", True)
    renamed = update_checklist_item_service(item["id"], {"text": "uno"})
    assert (renamed["text"], renamed["is_done"]) == ("uno", True)
    unticked = update_checklist_item_service(item["id"], {"is_done": False})
    assert unticked["is_done"] is False
    db_session.refresh(card)
    assert (card.version, card.updated_at) == (version, updated_at)


def test_update_without_fields_is_rejected(db_session: Any, make_card: Callable[..., Card]) -> None:
    item = create_checklist_item_service(make_card().id, {"text": "one"})
    with pytest.raises(ValidationError):
        update_checklist_item_service(item["id"], {})


def test_limit_of_items_per_card(db_session: Any, make_card: Callable[..., Card]) -> None:
    card = make_card()
    for n in range(MAX_CHECKLIST_ITEMS):
        create_checklist_item_service(card.id, {"text": f"item {n}"})
    with pytest.raises(ValidationError):
        create_checklist_item_service(card.id, {"text": "one too many"})


def test_missing_targets_raise_not_found(db_session: Any) -> None:
    with pytest.raises(NotFoundError):
        create_checklist_item_service(uuid.uuid4(), {"text": "x"})
    with pytest.raises(NotFoundError):
        update_checklist_item_service(uuid.uuid4(), {"is_done": True})
    with pytest.raises(NotFoundError):
        delete_checklist_item_service(uuid.uuid4())
