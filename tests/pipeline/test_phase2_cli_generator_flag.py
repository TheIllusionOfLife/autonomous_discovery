"""Unit tests for the --generator CLI flag on phase2_cli."""

import pytest

from autonomous_discovery.phase2_cli import build_parser


class TestGeneratorFlagParser:
    """Parser-level tests for the --generator argument."""

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
