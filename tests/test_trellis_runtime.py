from __future__ import annotations

import importlib.util
import json
import sys
import time
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
TRELLIS_SCRIPTS = ROOT / ".trellis" / "scripts"
if str(TRELLIS_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(TRELLIS_SCRIPTS))

from common import active_task, session_context, task_context  # noqa: E402


def _load_claude_session_start():
    path = ROOT / ".claude" / "hooks" / "session-start.py"
    spec = importlib.util.spec_from_file_location("claude_session_start", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CLAUDE_SESSION_START = _load_claude_session_start()


def _clear_context_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    keys = {"TRELLIS_CONTEXT_ID"}
    for _, names in (
        *active_task._ENV_SESSION_KEYS,
        *active_task._ENV_CONVERSATION_KEYS,
        *active_task._ENV_TRANSCRIPT_KEYS,
    ):
        keys.update(names)
    for key in keys:
        monkeypatch.delenv(key, raising=False)


def test_codex_does_not_consume_cursor_shell_ticket(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _clear_context_environment(monkeypatch)
    ticket_dir = tmp_path / ".trellis" / ".runtime" / "cursor-shell"
    ticket_dir.mkdir(parents=True)
    (ticket_dir / "ticket.json").write_text(
        json.dumps(
            {
                "platform": "cursor",
                "context_key": "cursor_other_window",
                "cwd": str(tmp_path),
                "created_at_epoch": time.time(),
                "subcommands": [{"name": "current"}],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["task.py", "current"])

    assert active_task.resolve_context_key(platform="codex") is None
    assert active_task.resolve_context_key(platform="cursor") == "cursor_other_window"


@pytest.mark.parametrize(
    ("platform", "env_name", "expected"),
    [
        ("claude", "CLAUDE_SESSION_ID", "claude_legacy"),
        ("codex", "CODEX_SESSION_ID", "codex_legacy"),
        ("cursor", "CURSOR_SESSION_ID", "cursor_legacy"),
        ("opencode", "OPENCODE_RUN_ID", "opencode_legacy"),
        ("droid", "FACTORY_SESSION_ID", "droid_legacy"),
        ("codebuddy", "CODEBUDDY_SESSION_ID", "codebuddy_legacy"),
        ("pi", "PI_SESSION_ID", "pi_legacy"),
        ("trae", "TRAE_SESSION_ID", "trae_legacy"),
    ],
)
def test_environment_adapter_contract(
    platform: str,
    env_name: str,
    expected: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _clear_context_environment(monkeypatch)
    monkeypatch.setenv(env_name, "legacy")

    assert active_task.resolve_context_key(platform=platform) == expected


@pytest.mark.parametrize(
    ("platform", "env_name", "expected_prefix"),
    [
        ("claude", "CLAUDE_TRANSCRIPT_PATH", "claude_transcript_"),
        ("codex", "CODEX_TRANSCRIPT_PATH", "codex_transcript_"),
    ],
)
def test_transcript_adapter_contract(
    platform: str,
    env_name: str,
    expected_prefix: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _clear_context_environment(monkeypatch)
    monkeypatch.setenv(env_name, "/tmp/session.jsonl")

    context_key = active_task.resolve_context_key(platform=platform)

    assert context_key is not None and context_key.startswith(expected_prefix)


@pytest.mark.parametrize(
    "later_statement",
    ["unset TRELLIS_CONTEXT_ID", "TRELLIS_CONTEXT_ID=claude_other"],
)
def test_claude_env_file_restores_identity_after_later_override(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    later_statement: str,
) -> None:
    env_file = tmp_path / "claude-env.sh"
    env_file.write_text(
        f"export TRELLIS_CONTEXT_ID=claude_same\n{later_statement}\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("CLAUDE_ENV_FILE", str(env_file))

    CLAUDE_SESSION_START._persist_context_key_for_bash("claude_same")

    assert env_file.read_text(encoding="utf-8").splitlines()[-1] == (
        "export TRELLIS_CONTEXT_ID=claude_same"
    )


def test_claude_env_file_does_not_duplicate_effective_export(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    env_file = tmp_path / "claude-env.sh"
    original = "export TRELLIS_CONTEXT_ID=claude_same\n"
    env_file.write_text(original, encoding="utf-8")
    monkeypatch.setenv("CLAUDE_ENV_FILE", str(env_file))

    CLAUDE_SESSION_START._persist_context_key_for_bash("claude_same")

    assert env_file.read_text(encoding="utf-8") == original


def test_update_hint_is_scoped_and_emitted_once(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    trellis_dir = tmp_path / ".trellis"
    trellis_dir.mkdir()
    (trellis_dir / ".version").write_text("0.6.12\n", encoding="utf-8")
    monkeypatch.setattr(
        session_context,
        "_resolve_available_update_version",
        lambda: "0.6.13",
    )

    hint = session_context.get_update_hint(tmp_path, "claude_window")

    assert hint == "Trellis update available: 0.6.12 -> 0.6.13, run trellis update"
    assert session_context.get_update_hint(tmp_path, "claude_window") is None
    assert "Also relay this Trellis maintenance notice" in (
        CLAUDE_SESSION_START._build_first_reply_notice(hint)
    )


def test_archived_jsonl_self_reference_maps_to_archive_copy(tmp_path: Path) -> None:
    task_dir = tmp_path / ".trellis" / "tasks" / "archive" / "2026-08" / "08-11-demo"
    research_file = task_dir / "research" / "notes.md"
    research_file.parent.mkdir(parents=True)
    research_file.write_text("notes\n", encoding="utf-8")

    resolved = task_context._resolve_context_entry_path(
        ".trellis/tasks/08-11-demo/research/notes.md",
        tmp_path,
        task_dir,
    )

    assert resolved == research_file.resolve()
