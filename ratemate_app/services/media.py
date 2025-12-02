from typing import Optional
from uuid import uuid4
from urllib.parse import urlparse

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from fastapi import UploadFile

from azure.storage.blob.aio import BlobServiceClient
from azure.storage.blob import ContentSettings
from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError

from ratemate_app.core.config import settings
from ratemate_app.models.media import Media

_container_client: Optional[BlobServiceClient] = None

def _sanitize_filename(name: str) -> str:
    return name.replace("\\", "/").split("/")[-1]

async def _get_container_client():
    if not settings.AZURE_STORAGE_CONNECTION_STRING or not settings.AZURE_STORAGE_CONTAINER:
        raise RuntimeError("Azure storage settings are not configured")
    
    service = BlobServiceClient.from_connection_string(settings.AZURE_STORAGE_CONNECTION_STRING)
    container = service.get_container_client(settings.AZURE_STORAGE_CONTAINER)

    try:
        await container.create_container()
    except ResourceExistsError:
        pass
    return container


async def upload_media(db: AsyncSession, post_id: int, file: UploadFile) -> Media:
    container = await _get_container_client()
    filename = _sanitize_filename(file.filename or "file")
    blob_name = f"posts/{post_id}/{uuid4()}-{filename}"
    blob_client = container.get_blob_client(blob_name)
    data = await file.read()

    media_type = "image" if (file.content_type or "").startswith("image/") else ("video" if (file.content_type or "").startswith("video/") else "file")
    await blob_client.upload_blob(
        data,
        overwrite=True,
        content_settings=ContentSettings(content_type=file.content_type or "application/octet-stream"),
    )

    url = blob_client.url
    media = Media(post_id=post_id, url=url, media_type=media_type)

    db.add(media)
    await db.commit()
    await db.refresh(media)
    return media


async def list_post_media(db: AsyncSession, post_id: int) -> list[Media]:
    result = await db.execute(select(Media).where(Media.post_id == post_id))
    return result.scalars().all()


async def delete_media(db: AsyncSession, media_id: int) -> None:
    media = await db.get(Media, media_id)
    if not media:
        return
    
    container = await _get_container_client()
    try:
        path = urlparse(media.url).path
        prefix = "/" + settings.AZURE_STORAGE_CONTAINER + "/"
        blob_name = path[len(prefix):] if path.startswith(prefix) else path.lstrip("/")
        await container.delete_blob(blob_name, delete_snapshots="include")

    except (ResourceNotFoundError, ValueError):
        pass

    await db.execute(delete(Media).where(Media.id == media_id))
    await db.commit()

async def delete_all_post_media_blobs(db: AsyncSession, post_id: int) -> None:
    medias = await list_post_media(db, post_id)
    if not medias:
        return
    
    container = await _get_container_client()
    for m in medias:
        try:
            path = urlparse(m.url).path
            prefix = "/" + settings.AZURE_STORAGE_CONTAINER + "/"
            blob_name = path[len(prefix):] if path.startswith(prefix) else path.lstrip("/")
            await container.delete_blob(blob_name, delete_snapshots="include")
        except (ResourceNotFoundError, ValueError):
            continue

    await db.execute(delete(Media).where(Media.post_id == post_id))
    await db.commit()

async def upload_media_bulk(db: AsyncSession, post_id: int, files: list[UploadFile]) -> list[Media]:
    if not files:
        return []
    if len(files) > 5:
        raise ValueError("too_many_files")
    
    result: list[Media] = []
    for f in files:
        result.append(await upload_media(db, post_id, f))
    
    return result


async def upload_comment_media(db: AsyncSession, comment_id: int, file: UploadFile) -> Media:
    container = await _get_container_client()
    filename = _sanitize_filename(file.filename or "file")
    blob_name = f"comments/{comment_id}/{uuid4()}-{filename}"
    blob_client = container.get_blob_client(blob_name)
    data = await file.read()
    media_type = "image" if (file.content_type or "").startswith("image/") else ("video" if (file.content_type or "").startswith("video/") else "file")
    await blob_client.upload_blob(
        data,
        overwrite=True,
        content_settings=ContentSettings(content_type=file.content_type or "application/octet-stream"),
    )
    url = blob_client.url
    media = Media(comment_id=comment_id, url=url, media_type=media_type)
    db.add(media)
    await db.commit()
    await db.refresh(media)
    return media

async def upload_comment_media_bulk(db: AsyncSession, comment_id: int, files: list[UploadFile]) -> list[Media]:
    if not files:
        return []
    if len(files) > 5:
        raise ValueError("too_many_files")
    return [await upload_comment_media(db, comment_id, f) for f in files]

async def upload_user_avatar(user_id: int, file: UploadFile) -> tuple[str, str]:
    container = await _get_container_client()
    filename = _sanitize_filename(file.filename or "avatar")
    blob_name = f"users/{user_id}/avatar/{uuid4()}-{filename}"
    blob_client = container.get_blob_client(blob_name)
    data = await file.read()
    media_type = "image" if (file.content_type or "").startswith("image/") else ("video" if (file.content_type or "").startswith("video/") else "file")

    await blob_client.upload_blob(
        data,
        overwrite=True,
        content_settings=ContentSettings(content_type=file.content_type or "application/octet-stream")
    )
    return blob_client.url, media_type

async def delete_user_avatar_blob(url: str) -> None:
    if not url:
        return
    container = await _get_container_client()
    try:
        path = urlparse(url).path
        prefix = "/" + settings.AZURE_STORAGE_CONTAINER + "/"
        blob_name = path[len(prefix):] if path.startswith(prefix) else path.lstrip("/")

        await container.delete_blob(blob_name, delete_snapshots="include")
    except(ResourceNotFoundError, ValueError):
        return

async def upload_lowkey_media(lowkey_id: int, file: UploadFile) -> tuple[str, str]:
    container = await _get_container_client()
    filename = _sanitize_filename(file.filename or "media")
    blob_name = f"users/{user_id}/avatar/{uuid4()}-{filename}"
    blob_client = container.get_blob_client(blob_name)
    data = await file.read()
    media_type = "image" if (file.content_type or "").startswith("image/") else ("video" if (file.content_type or "").startswith("video/") else "file")

    await blob_client.upload_blob(
        data,
        overwrite=True,
        content_settings=ContentSettings(content_type=file.content_type or "application/octet-stream"),
    )
    return blob_client.url, media_type

async def delete_lowkey_media_blob(url: str) -> None:
    if not url:
        return
    container = await _get_container_client()
    try:
        path = urlparse(url).path
        prefix = "/" + settings.AZURE_STORAGE_CONTAINER + "/"
        blob_name = path[len(prefix):] if path.startswith(prefix) else path.lstrip("/")
        await container.delete_blob(blob_name, delete_snapshots="include")
    except (ResourceNotFoundError, ValueError):
        return
    

async def list_comment_media(db: AsyncSession, comment_id: int) -> list[Media]:
    result = await db.execute(select(Media).where(Media.comment_id == comment_id))
    return result.scalars().all()

async def delete_all_comment_media_blobs(db: AsyncSession, comment_id: int) -> None:
    medias = await list_comment_media(db, comment_id)
    if not medias:
        return 
    container = await _get_container_client()
    for m in medias:
        try:
            path = urlparse(m.url).path
            prefix = "/" + settings.AZURE_STORAGE_CONTAINER + "/"
            blob_name = path[len(prefix):] if path.startswith(prefix) else path.lstrip("/")
            await container.delete_blob(blob_name, delete_snapshots="include")
        except (ResourceNotFoundError, ValueError):
            continue
    await db.execute(delete(Media).where(Media.comment_id == comment_id))
    await db.commit()