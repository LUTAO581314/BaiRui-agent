from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from .storage import DocumentIngestRun, create_document_ingest_run, list_document_ingests, utc_now


@dataclass(frozen=True)
class DocumentPipelineResult:
    status: str
    detail: str
    ingest: dict[str, object] | None
    run: DocumentIngestRun | None


def run_document_ingest(data_dir: Path, ingest_id: str, *, timeout_seconds: int) -> DocumentPipelineResult:
    ingest = _find_ingest(data_dir, ingest_id)
    if ingest is None:
        return DocumentPipelineResult(status="not_found", detail=f"document ingest not found: {ingest_id}", ingest=None, run=None)

    command = tuple(str(part) for part in ingest.get("parser_command", ()))
    if not command:
        run = create_document_ingest_run(
            data_dir,
            ingest_id=ingest_id,
            status="failed",
            command=(),
            cwd="",
            exit_code=None,
            error="parser_command is empty",
        )
        return DocumentPipelineResult(status="failed", detail="parser_command is empty", ingest=ingest, run=run)

    cwd = str(Path.cwd())
    started_at = utc_now()
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
        status = "completed" if completed.returncode == 0 else "failed"
        run = create_document_ingest_run(
            data_dir,
            ingest_id=ingest_id,
            status=status,
            command=command,
            cwd=cwd,
            exit_code=completed.returncode,
            stdout=completed.stdout[-8000:],
            stderr=completed.stderr[-8000:],
            started_at=started_at,
            finished_at=utc_now(),
        )
        return DocumentPipelineResult(status=status, detail=f"command exited with {completed.returncode}", ingest=ingest, run=run)
    except FileNotFoundError as exc:
        error = f"executable not found: {command[0]} ({exc})"
        run = create_document_ingest_run(
            data_dir,
            ingest_id=ingest_id,
            status="failed",
            command=command,
            cwd=cwd,
            exit_code=None,
            error=error,
            started_at=started_at,
            finished_at=utc_now(),
        )
        return DocumentPipelineResult(status="failed", detail="parser executable was not found", ingest=ingest, run=run)
    except subprocess.TimeoutExpired as exc:
        run = create_document_ingest_run(
            data_dir,
            ingest_id=ingest_id,
            status="timeout",
            command=command,
            cwd=cwd,
            exit_code=None,
            stdout=(exc.stdout or "")[-8000:] if isinstance(exc.stdout, str) else "",
            stderr=(exc.stderr or "")[-8000:] if isinstance(exc.stderr, str) else "",
            error=f"command timed out after {timeout_seconds}s",
            started_at=started_at,
            finished_at=utc_now(),
        )
        return DocumentPipelineResult(status="timeout", detail=f"command timed out after {timeout_seconds}s", ingest=ingest, run=run)


def _find_ingest(data_dir: Path, ingest_id: str) -> dict[str, object] | None:
    for ingest in reversed(list_document_ingests(data_dir, limit=1000)):
        if ingest.get("id") == ingest_id:
            return ingest
    return None
