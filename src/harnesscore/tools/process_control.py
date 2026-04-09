"""
Process control tool for agents.
Start, stop and query background shell processes (dev servers, test runners, etc.)
"""
from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class ManagedProcess:
    label: str
    command: list[str]
    cwd: Path
    proc: subprocess.Popen = field(repr=False)
    stdout_lines: list[str] = field(default_factory=list, repr=False)

    def is_alive(self) -> bool:
        return self.proc.poll() is None

    def tail_output(self, n: int = 20) -> str:
        """Return the last *n* lines from the captured stdout buffer."""
        try:
            # non-blocking read of any pending output
            while True:
                line = self.proc.stdout.readline()  # type: ignore[union-attr]
                if not line:
                    break
                self.stdout_lines.append(line.rstrip("\n"))
        except Exception:
            pass
        return "\n".join(self.stdout_lines[-n:])


class ProcessControlTool:
    """
    Manage background shell processes on behalf of agents.

    Processes are tracked in an in-memory registry keyed by *label*.
    Only one process per label may run at a time.
    """

    def __init__(self, working_dir: Path, timeout: int = 10) -> None:
        self.working_dir = working_dir.resolve()
        self.timeout = timeout
        self._registry: dict[str, ManagedProcess] = {}

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #
    def start(
        self,
        label: str,
        command: list[str],
        cwd: Optional[str] = None,
        wait_seconds: float = 1.5,
    ) -> str:
        """
        Launch *command* as a background process with *label*.

        If a process with *label* is already running it is stopped first.
        *wait_seconds* — time to sleep before checking if the process survived.
        """
        if label in self._registry and self._registry[label].is_alive():
            self.stop(label)

        proc = subprocess.Popen(
            command,
            cwd=Path(cwd).resolve() if cwd else self.working_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        managed = ManagedProcess(
            label=label,
            command=command,
            cwd=Path(cwd or self.working_dir),
            proc=proc,
        )
        self._registry[label] = managed

        time.sleep(wait_seconds)
        if not managed.is_alive():
            out = managed.tail_output()
            raise RuntimeError(
                f"Process '{label}' exited immediately.\nOutput:\n{out}"
            )
        return f"[{label}] started (PID {proc.pid})"

    def stop(self, label: str) -> str:
        """Terminate a managed process by *label*."""
        mp = self._registry.get(label)
        if not mp:
            return f"[{label}] not found in registry."
        if mp.is_alive():
            mp.proc.terminate()
            try:
                mp.proc.wait(timeout=self.timeout)
            except subprocess.TimeoutExpired:
                mp.proc.kill()
        del self._registry[label]
        return f"[{label}] stopped."

    def restart(self, label: str, wait_seconds: float = 1.5) -> str:
        """Restart an existing managed process."""
        mp = self._registry.get(label)
        if not mp:
            raise KeyError(f"No process with label '{label}' in registry.")
        cmd = mp.command
        cwd = str(mp.cwd)
        self.stop(label)
        return self.start(label, cmd, cwd=cwd, wait_seconds=wait_seconds)

    def status(self) -> list[dict]:
        """Return a status summary for all managed processes."""
        return [
            {
                "label": label,
                "pid": mp.proc.pid,
                "alive": mp.is_alive(),
                "command": " ".join(mp.command),
            }
            for label, mp in self._registry.items()
        ]

    def read_log(self, label: str, n: int = 30) -> str:
        """Return the last *n* output lines from a managed process."""
        mp = self._registry.get(label)
        if not mp:
            raise KeyError(f"No process with label '{label}' in registry.")
        return mp.tail_output(n)

    def stop_all(self) -> str:
        """Gracefully stop every managed process (called on app shutdown)."""
        labels = list(self._registry.keys())
        for label in labels:
            self.stop(label)
        return f"Stopped {len(labels)} process(es)."
