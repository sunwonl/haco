"""
Custom LangGraph file-based checkpointer.

Persists agent state to:
  - .harness/state.json   (machine-readable, resumable)
  - .harness/journals.md  (human-readable activity log)
"""
from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, Optional, Sequence, Tuple

from langgraph.checkpoint.base import (
    BaseCheckpointSaver,
    Checkpoint,
    CheckpointMetadata,
    CheckpointTuple,
    get_checkpoint_id,
)


class FileCheckpointer(BaseCheckpointSaver):
    """Saves checkpoints to local JSON files instead of a database."""

    def __init__(self, harness_dir: Path) -> None:
        super().__init__()
        self.harness_dir = harness_dir
        self.state_path = harness_dir / "state.json"
        self.journal_path = harness_dir / "journals.md"
        self._lock = threading.Lock()
        harness_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ #
    #  Internal helpers                                                    #
    # ------------------------------------------------------------------ #
    def _load_raw(self) -> dict:
        if self.state_path.exists():
            try:
                with self.state_path.open(encoding="utf-8") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {}
        return {}

    def _save_raw(self, data: dict) -> None:
        # Use a custom encoder to handle Pydantic models
        class PydanticEncoder(json.JSONEncoder):
            def default(self, obj):
                if hasattr(obj, "model_dump"):
                    return obj.model_dump()
                if isinstance(obj, datetime):
                    return obj.isoformat()
                return super().default(obj)

        with self.state_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, cls=PydanticEncoder, ensure_ascii=False)

    # ------------------------------------------------------------------ #
    #  BaseCheckpointSaver interface                                       #
    # ------------------------------------------------------------------ #
    def get_tuple(self, config: dict) -> Optional[CheckpointTuple]:
        thread_id = config["configurable"]["thread_id"]
        with self._lock:
            data = self._load_raw()
        entry = data.get(thread_id)
        if not entry:
            return None
        return CheckpointTuple(
            config=config,
            checkpoint=entry["checkpoint"],
            metadata=entry["metadata"],
        )

    def list(
        self,
        config: Optional[dict],
        *,
        filter: Optional[dict] = None,
        before: Optional[dict] = None,
        limit: Optional[int] = None,
    ) -> Iterator[CheckpointTuple]:
        with self._lock:
            data = self._load_raw()
        thread_id = (config or {}).get("configurable", {}).get("thread_id")
        for tid, entry in data.items():
            if thread_id and tid != thread_id:
                continue
            yield CheckpointTuple(
                config={"configurable": {"thread_id": tid}},
                checkpoint=entry["checkpoint"],
                metadata=entry["metadata"],
            )

    def put(
        self,
        config: dict,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: Any = None,
    ) -> dict:
        thread_id = config["configurable"]["thread_id"]
        with self._lock:
            data = self._load_raw()
            data[thread_id] = {
                "checkpoint": checkpoint,
                "metadata": metadata,
            }
            self._save_raw(data)
        return config

    def put_writes(
        self,
        config: dict,
        writes: Sequence[Tuple[str, Any]],
        task_id: str,
        task_path: Sequence[str] = (),
    ) -> None:
        # Lightweight: we persist only full checkpoints, not intermediate writes.
        pass
