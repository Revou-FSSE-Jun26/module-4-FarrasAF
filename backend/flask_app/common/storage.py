"""Cloudinary file storage. The only module that imports `cloudinary`."""

from dataclasses import dataclass

import cloudinary
import cloudinary.uploader
from flask import current_app


@dataclass(frozen=True)
class StoredFile:
    """What Cloudinary returns for a stored file."""

    public_id: str
    url: str
    resource_type: str


def _configure() -> None:
    config = current_app.config
    cloudinary.config(
        cloud_name=config["CLOUDINARY_CLOUD_NAME"],
        api_key=config["CLOUDINARY_API_KEY"],
        api_secret=config["CLOUDINARY_API_SECRET"],
        secure=True,
    )


def upload_file(data: bytes, folder: str, public_id: str, resource_type: str) -> StoredFile:
    """Upload bytes as `resource_type` ("image" or "raw") and return the stored file."""
    _configure()
    result = cloudinary.uploader.upload(
        data,
        folder=folder,
        public_id=public_id,
        resource_type=resource_type,
        overwrite=False,
        unique_filename=False,
        use_filename=False,
    )
    return StoredFile(
        public_id=str(result["public_id"]),
        url=str(result["secure_url"]),
        resource_type=str(result["resource_type"]),
    )


def delete_file(public_id: str, resource_type: str) -> None:
    """Delete a stored file. Raises if Cloudinary cannot be reached."""
    _configure()
    cloudinary.uploader.destroy(public_id, resource_type=resource_type, invalidate=True)
