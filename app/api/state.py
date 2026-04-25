from threading import Lock
from uuid import UUID

from app.api.schemas import FileRecord, JobRecord


class InMemoryState:
    """Temporary Phase 1 state store.

    Phase 2 replaces this with SQLAlchemy-backed repositories while keeping
    route behavior stable.
    """

    def __init__(self) -> None:
        self._files: dict[UUID, FileRecord] = {}
        self._jobs: dict[UUID, JobRecord] = {}
        self._lock = Lock()

    def add_file(self, file_record: FileRecord) -> FileRecord:
        with self._lock:
            self._files[file_record.file_id] = file_record
        return file_record

    def get_file(self, file_id: UUID) -> FileRecord | None:
        with self._lock:
            return self._files.get(file_id)

    def add_job(self, job_record: JobRecord) -> JobRecord:
        with self._lock:
            self._jobs[job_record.job_id] = job_record
        return job_record

    def get_job(self, job_id: UUID) -> JobRecord | None:
        with self._lock:
            return self._jobs.get(job_id)

    def reset(self) -> None:
        with self._lock:
            self._files.clear()
            self._jobs.clear()


app_state = InMemoryState()


def get_app_state() -> InMemoryState:
    return app_state

