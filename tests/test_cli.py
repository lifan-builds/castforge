# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 lifan-builds. CastForge; Section 7 attribution terms in ATTRIBUTION.md.
from __future__ import annotations

import pytest

from castforge.cli import main


def test_init_run_and_validate(tmp_path) -> None:
    project = tmp_path / "show"
    assert main(["init", str(project)]) == 0
    config = project / "podcast.yaml"
    assert main(["run", "--config", str(config), "--date", "2026-08-11"]) == 0
    assert main(["validate", "--config", str(config), "--date", "2026-08-11"]) == 0


def test_init_refuses_to_overwrite(tmp_path) -> None:
    assert main(["init", str(tmp_path)]) == 0
    assert main(["init", str(tmp_path)]) == 1


def test_version_prints_agpl_attribution(capsys) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    assert "Based on CastForge by lifan-builds (https://github.com/lifan-builds/castforge)" in capsys.readouterr().out
