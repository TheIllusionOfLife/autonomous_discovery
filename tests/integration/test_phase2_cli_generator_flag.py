"""Tests for the --generator CLI flag on phase2_cli."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from autonomous_discovery.phase2_cli import build_parser, main

_PREMISES = """\
---
Group.one_mul
  * Group.one
---
Ring.one
  * OfNat.ofNat
"""

_DECL_TYPES = """\
---
theorem
Group.one_mul
Group.one_mul : Prop
---
theorem
Group.one
Group.one : Prop
---
theorem
Ring.one
Ring.one : Prop
---
theorem
OfNat.ofNat
OfNat.ofNat : Prop
"""


class TestGeneratorFlag:
    """Tests for the --generator argument on phase2_cli."""

    def test_parser_accepts_template(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["--generator", "template"])
        assert args.generator == "template"

    def test_parser_accepts_ollama(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["--generator", "ollama"])
        assert args.generator == "ollama"

    def test_parser_default_is_template(self) -> None:
        parser = build_parser()
        args = parser.parse_args([])
        assert args.generator == "template"

    def test_parser_rejects_invalid_generator(self) -> None:
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["--generator", "invalid"])

    @pytest.mark.integration
    def test_cli_with_template_generator(self, tmp_path: Path) -> None:
        premises = tmp_path / "premises.txt"
        decl_types = tmp_path / "decl_types.txt"
        output = tmp_path / "out"
        premises.write_text(_PREMISES)
        decl_types.write_text(_DECL_TYPES)

        code = main(
            [
                "--premises-path",
                str(premises),
                "--decl-types-path",
                str(decl_types),
                "--output-dir",
                str(output),
                "--top-k",
                "5",
                "--generator",
                "template",
                "--trusted-local-run",
                "--i-understand-unsafe",
            ]
        )

        assert code == 0
        metrics = json.loads((output / "phase2_cycle_metrics.json").read_text())
        assert "success_rate" in metrics

    @pytest.mark.integration
    def test_cli_with_ollama_generator_passes_instance(self, tmp_path: Path) -> None:
        """Verify that --generator ollama instantiates OllamaConjectureGenerator."""
        premises = tmp_path / "premises.txt"
        decl_types = tmp_path / "decl_types.txt"
        output = tmp_path / "out"
        premises.write_text(_PREMISES)
        decl_types.write_text(_DECL_TYPES)

        with (
            patch("autonomous_discovery.phase2_cli.run_phase2_cycle") as mock_cycle,
            patch("autonomous_discovery.phase2_cli.OllamaConjectureGenerator") as mock_gen_cls,
        ):
            mock_cycle.return_value = {"runtime_ready": True, "skipped_reason": None}
            mock_gen_instance = mock_gen_cls.return_value

            code = main(
                [
                    "--premises-path",
                    str(premises),
                    "--decl-types-path",
                    str(decl_types),
                    "--output-dir",
                    str(output),
                    "--top-k",
                    "5",
                    "--generator",
                    "ollama",
                    "--trusted-local-run",
                    "--i-understand-unsafe",
                ]
            )

        assert code == 0
        mock_cycle.assert_called_once()
        _, kwargs = mock_cycle.call_args
        assert kwargs["generator"] is mock_gen_instance
