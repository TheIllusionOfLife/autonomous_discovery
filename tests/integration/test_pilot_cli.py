from autonomous_discovery.gap_detector.pilot_cli import main


def test_pilot_cli_reports_missing_input(capsys) -> None:
    code = main(
        [
            "--premises-path",
            "does-not-exist-premises.txt",
            "--decl-types-path",
            "does-not-exist-decls.txt",
        ]
    )
    captured = capsys.readouterr()
    assert code != 0
    assert "not found" in captured.err.lower()
