"""Unit tests for the Card attachments service (R22). Cloudinary is replaced by a fake."""

from collections.abc import Callable
from typing import Any

import pytest

from flask_app.attachments import service
from flask_app.attachments.service import (
    ALLOWED_EXTENSIONS,
    MAX_ATTACHMENT_BYTES,
    MAX_ATTACHMENTS_PER_CARD,
    build_download_url,
    delete_attachment_service,
    upload_attachment_service,
    validate_upload,
)
from flask_app.cards.service import delete_card_service, get_card_service
from flask_app.common.exceptions import AuthorizationError, NotFoundError, ValidationError
from flask_app.common.serialization import UploadedFile
from flask_app.common.storage import StoredFile
from flask_app.models import ActivityEntry, Attachment, BoardMembership, Card, User


class FakeStorage:
    """Records what would have been sent to Cloudinary."""

    def __init__(self) -> None:
        self.uploads: list[dict[str, str]] = []
        self.deleted: list[tuple[str, str]] = []
        self.fail_upload = False
        self.fail_delete = False

    def upload(self, data: bytes, folder: str, public_id: str, resource_type: str) -> StoredFile:
        if self.fail_upload:
            raise ConnectionError("cloudinary down")
        full_id = f"{folder}/{public_id}"
        self.uploads.append({"public_id": full_id, "resource_type": resource_type})
        base = f"https://res.cloudinary.com/demo/{resource_type}/upload/v1/{full_id}"
        return StoredFile(public_id=full_id, url=base, resource_type=resource_type)

    def delete(self, public_id: str, resource_type: str) -> None:
        if self.fail_delete:
            raise ConnectionError("cloudinary down")
        self.deleted.append((public_id, resource_type))


@pytest.fixture
def storage(monkeypatch: pytest.MonkeyPatch) -> FakeStorage:
    fake = FakeStorage()
    monkeypatch.setattr(service, "upload_file", fake.upload)
    monkeypatch.setattr(service, "delete_file", fake.delete)
    return fake


def _file(name: str = "report.pdf", size: int = 10) -> UploadedFile:
    return UploadedFile(file_name=name, content_type="application/pdf", data=b"x" * size)


def _add_member(db_session: Any, card: Card, user: User, role: str = "member") -> None:
    db_session.add(BoardMembership(board_id=card.board_id, user_id=user.id, role=role))
    db_session.flush()


# ----- validate_upload (pure) -----


@pytest.mark.parametrize("extension", sorted(ALLOWED_EXTENSIONS))
def test_every_allowed_extension_is_accepted_in_any_case(extension: str) -> None:
    assert validate_upload(f"file.{extension.upper()}", 1) == f"file.{extension.upper()}"


@pytest.mark.parametrize("name", ["virus.exe", "archive.zip", "noextension", "script.js", "a."])
def test_other_extensions_are_rejected(name: str) -> None:
    with pytest.raises(ValidationError) as error:
        validate_upload(name, 10)
    assert error.value.field == "file"


def test_size_limits() -> None:
    assert validate_upload("a.png", MAX_ATTACHMENT_BYTES) == "a.png"
    with pytest.raises(ValidationError):
        validate_upload("a.png", MAX_ATTACHMENT_BYTES + 1)
    with pytest.raises(ValidationError):
        validate_upload("a.png", 0)


def test_file_name_rules() -> None:
    assert validate_upload("  C:\\Users\\me\\notes.txt ", 1) == "notes.txt"
    assert validate_upload("../../etc/data.csv", 1) == "data.csv"
    for bad in ("", "   ", "x" * 252 + ".pdf"):
        with pytest.raises(ValidationError):
            validate_upload(bad, 1)
    assert validate_upload("x" * 251 + ".pdf", 1)


def test_download_url_forces_download_only_for_images() -> None:
    image = "https://res.cloudinary.com/demo/image/upload/v1/a/b"
    raw = "https://res.cloudinary.com/demo/raw/upload/v1/a/b.pdf"
    assert build_download_url(image, "image") == (
        "https://res.cloudinary.com/demo/image/upload/fl_attachment/v1/a/b"
    )
    assert build_download_url(raw, "raw") == raw


# ----- upload -----


def test_upload_saves_record_activity_and_keeps_card_version(
    db_session: Any, make_card: Callable[..., Card], make_user: Callable[..., User], storage: Any
) -> None:
    card = make_card()
    user = make_user(display_name="Ada")
    _add_member(db_session, card, user)
    version, updated_at = card.version, card.updated_at

    result = upload_attachment_service(card.id, _file("Plan.PDF", 123), user)

    assert result["file_name"] == "Plan.PDF"
    assert result["size_bytes"] == 123
    assert result["uploaded_by"] == {"id": user.id, "display_name": "Ada"}
    assert result["card_id"] == card.id
    assert storage.uploads[0]["resource_type"] == "raw"
    assert storage.uploads[0]["public_id"].endswith(".pdf")
    assert f"task-management-app/cards/{card.id}/" in storage.uploads[0]["public_id"]
    entry = db_session.query(ActivityEntry).filter_by(event_type="attachment_added").one()
    assert (entry.resource_id, entry.secondary_resource_id) == (result["id"], card.id)
    assert entry.details == {"card_title": card.title, "file_name": "Plan.PDF"}
    db_session.refresh(card)
    assert (card.version, card.updated_at) == (version, updated_at)


def test_images_are_stored_as_image_resources(
    db_session: Any, make_card: Callable[..., Card], make_user: Callable[..., User], storage: Any
) -> None:
    card = make_card()
    result = upload_attachment_service(card.id, _file("photo.jpg"), make_user())
    assert storage.uploads[0]["resource_type"] == "image"
    assert not storage.uploads[0]["public_id"].endswith(".jpg")
    assert "/fl_attachment/" in result["download_url"]


def test_card_payload_lists_attachments_oldest_first(
    db_session: Any, make_card: Callable[..., Card], make_user: Callable[..., User], storage: Any
) -> None:
    card = make_card()
    user = make_user()
    first = upload_attachment_service(card.id, _file("a.pdf"), user)
    second = upload_attachment_service(card.id, _file("b.txt"), user)
    names = [a["file_name"] for a in get_card_service(card.id)["attachments"]]
    assert names == ["a.pdf", "b.txt"]
    assert {first["id"], second["id"]}


def test_rejected_uploads_store_nothing(
    db_session: Any, make_card: Callable[..., Card], make_user: Callable[..., User], storage: Any
) -> None:
    card = make_card()
    user = make_user()
    for bad in (_file("a.exe"), _file("a.pdf", 0), _file("a.pdf", MAX_ATTACHMENT_BYTES + 1)):
        with pytest.raises(ValidationError):
            upload_attachment_service(card.id, bad, user)
    assert storage.uploads == []
    assert db_session.query(Attachment).count() == 0


def test_limit_of_attachments_per_card(
    db_session: Any, make_card: Callable[..., Card], make_user: Callable[..., User], storage: Any
) -> None:
    card = make_card()
    user = make_user()
    for n in range(MAX_ATTACHMENTS_PER_CARD):
        upload_attachment_service(card.id, _file(f"f{n}.pdf"), user)
    with pytest.raises(ValidationError):
        upload_attachment_service(card.id, _file("extra.pdf"), user)
    assert len(storage.uploads) == MAX_ATTACHMENTS_PER_CARD
    assert db_session.query(Attachment).count() == MAX_ATTACHMENTS_PER_CARD


def test_unknown_card_is_not_found(db_session: Any, make_user: Callable[..., User]) -> None:
    import uuid

    with pytest.raises(NotFoundError):
        upload_attachment_service(uuid.uuid4(), _file(), make_user())


def test_cloudinary_failure_saves_no_record_and_hides_details(
    db_session: Any, make_card: Callable[..., Card], make_user: Callable[..., User], storage: Any
) -> None:
    card = make_card()
    storage.fail_upload = True
    with pytest.raises(RuntimeError) as error:
        upload_attachment_service(card.id, _file(), make_user())
    assert "cloudinary" not in str(error.value).lower()
    assert error.value.__cause__ is None
    assert db_session.query(Attachment).count() == 0


def test_failed_save_removes_the_stored_file(
    db_session: Any,
    make_card: Callable[..., Card],
    make_user: Callable[..., User],
    storage: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    card = make_card()

    def broken(*args: Any, **kwargs: Any) -> None:
        raise RuntimeError("database error")

    monkeypatch.setattr(service, "record_activity", broken)
    with pytest.raises(RuntimeError, match="database error"):
        upload_attachment_service(card.id, _file(), make_user())
    assert [d[0] for d in storage.deleted] == [storage.uploads[0]["public_id"]]


# ----- delete -----


def test_uploader_can_delete_and_the_file_is_removed(
    db_session: Any, make_card: Callable[..., Card], make_user: Callable[..., User], storage: Any
) -> None:
    card = make_card()
    user = make_user()
    _add_member(db_session, card, user)
    result = upload_attachment_service(card.id, _file("a.pdf"), user)

    delete_attachment_service(result["id"], user)

    assert db_session.query(Attachment).count() == 0
    assert storage.deleted == [(storage.uploads[0]["public_id"], "raw")]
    entry = db_session.query(ActivityEntry).filter_by(event_type="attachment_deleted").one()
    assert entry.details == {"card_title": card.title, "file_name": "a.pdf"}


def test_other_member_cannot_delete_but_admin_can(
    db_session: Any, make_card: Callable[..., Card], make_user: Callable[..., User], storage: Any
) -> None:
    card = make_card()
    uploader, other, admin = make_user(), make_user(), make_user()
    _add_member(db_session, card, uploader)
    _add_member(db_session, card, other)
    _add_member(db_session, card, admin, role="admin")
    result = upload_attachment_service(card.id, _file(), uploader)

    with pytest.raises(AuthorizationError):
        delete_attachment_service(result["id"], other)
    assert db_session.query(Attachment).count() == 1

    delete_attachment_service(result["id"], admin)
    assert db_session.query(Attachment).count() == 0


def test_delete_succeeds_when_cloudinary_fails(
    db_session: Any, make_card: Callable[..., Card], make_user: Callable[..., User], storage: Any
) -> None:
    card = make_card()
    user = make_user()
    result = upload_attachment_service(card.id, _file(), user)
    storage.fail_delete = True
    delete_attachment_service(result["id"], user)
    assert db_session.query(Attachment).count() == 0


def test_delete_unknown_attachment_is_not_found(
    db_session: Any, make_user: Callable[..., User]
) -> None:
    import uuid

    with pytest.raises(NotFoundError):
        delete_attachment_service(uuid.uuid4(), make_user())


def test_deleting_a_card_removes_its_files(
    db_session: Any, make_card: Callable[..., Card], make_user: Callable[..., User], storage: Any
) -> None:
    card = make_card()
    user = make_user()
    _add_member(db_session, card, user)
    upload_attachment_service(card.id, _file("a.pdf"), user)
    upload_attachment_service(card.id, _file("b.png"), user)

    delete_card_service(card.id, user)

    assert db_session.query(Attachment).count() == 0
    assert sorted(r for _, r in storage.deleted) == ["image", "raw"]
