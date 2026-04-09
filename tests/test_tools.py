"""Smoke tests for IR-002: Agent Tools."""
import subprocess
import tempfile
from pathlib import Path

import pytest

from harnesscore.tools import FileIOTool, GitTool, PathGuardError


# ------------------------------------------------------------------ #
#  FileIOTool tests                                                    #
# ------------------------------------------------------------------ #
@pytest.fixture()
def tmp_root(tmp_path: Path) -> Path:
    return tmp_path


def test_write_and_read(tmp_root: Path) -> None:
    tool = FileIOTool(tmp_root)
    tool.write_file("hello.txt", "Hello, Harness!\n")
    content = tool.view_file("hello.txt")
    assert "Hello, Harness!" in content


def test_append(tmp_root: Path) -> None:
    tool = FileIOTool(tmp_root)
    tool.write_file("log.txt", "line1\n")
    tool.append_file("log.txt", "line2\n")
    assert "line2" in tool.view_file("log.txt")


def test_replace_content(tmp_root: Path) -> None:
    tool = FileIOTool(tmp_root)
    tool.write_file("src.py", "x = 1\n")
    tool.replace_content("src.py", "x = 1", "x = 42")
    assert "x = 42" in tool.view_file("src.py")


def test_path_guard_blocks_escape(tmp_root: Path) -> None:
    tool = FileIOTool(tmp_root)
    with pytest.raises(PathGuardError):
        tool.view_file("../../etc/passwd")


def test_search_files(tmp_root: Path) -> None:
    tool = FileIOTool(tmp_root)
    tool.write_file("a.py", "def foo(): pass\n")
    tool.write_file("b.py", "def bar(): pass\n")
    results = tool.search_files("foo", pattern="**/*.py")
    assert len(results) == 1
    assert results[0]["file"] == "a.py"


# ------------------------------------------------------------------ #
#  GitTool tests                                                       #
# ------------------------------------------------------------------ #
@pytest.fixture()
def git_repo(tmp_path: Path) -> Path:
    """Initialize a bare git repo for testing."""
    subprocess.run(["git", "init", str(tmp_path)], check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@harness.ai"],
        cwd=tmp_path, check=True, capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Harness Test"],
        cwd=tmp_path, check=True, capture_output=True,
    )
    # initial commit so HEAD exists
    (tmp_path / "README.md").write_text("init")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "initial"],
        cwd=tmp_path, check=True, capture_output=True,
    )
    return tmp_path


def test_git_status(git_repo: Path) -> None:
    tool = GitTool(git_repo)
    # clean repo should return empty
    assert tool.status() == ""


def test_git_create_and_list_branches(git_repo: Path) -> None:
    tool = GitTool(git_repo)
    tool.create_branch("feature/test-branch")
    branches = tool.list_branches()
    assert "feature/test-branch" in branches


def test_git_add_commit(git_repo: Path) -> None:
    tool = GitTool(git_repo)
    (git_repo / "new_file.py").write_text("x = 1")
    tool.add("new_file.py")
    tool.commit("add new_file.py")
    log = tool.log(n=1)
    assert "add new_file.py" in log


def test_git_disallow_unknown_subcommand(git_repo: Path) -> None:
    tool = GitTool(git_repo)
    with pytest.raises(PermissionError):
        tool._run(["push", "origin", "main"])
