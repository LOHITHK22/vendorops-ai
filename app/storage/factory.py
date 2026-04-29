from app.config.settings import Settings
from app.storage.backends import (
    LocalObjectStorage,
    ObjectStorageBackend,
    UnsupportedStorageBackendError,
)


def get_object_storage(settings: Settings) -> ObjectStorageBackend:
    if settings.storage_backend == "local":
        return LocalObjectStorage(settings.local_storage_dir)

    raise UnsupportedStorageBackendError(
        f"Storage backend '{settings.storage_backend}' is configured but not implemented. "
        "Use STORAGE_BACKEND=local for this build, or add the cloud provider adapter."
    )


def get_report_storage(settings: Settings) -> ObjectStorageBackend:
    if settings.storage_backend == "local":
        return LocalObjectStorage(settings.reports_dir)

    return get_object_storage(settings)
