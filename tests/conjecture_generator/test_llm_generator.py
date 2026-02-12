"""Tests for Ollama-backed LLM conjecture generator."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import httpx

from autonomous_discovery.config import LLMConfig
from autonomous_discovery.conjecture_generator.llm_generator import OllamaConjectureGenerator
from autonomous_discovery.gap_detector.analogical import GapCandidate


def _make_gap(
    source_decl: str = "Group.mul_assoc",
    target_family: str = "Ring.",
    missing_decl: str = "Ring.mul_assoc",
    score: float = 0.85,
) -> GapCandidate:
    return GapCandidate(
        source_decl=source_decl,
        target_family=target_family,
        missing_decl=missing_decl,
        score=score,
        signals={"dependency_overlap": 0.7},
    )


def _ollama_response(content: str) -> MagicMock:
    """Build a mock httpx response mimicking Ollama /api/chat."""
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = 200
    resp.json.return_value = {
        "model": "gpt-oss-20b",
        "message": {"role": "assistant", "content": content},
        "done": True,
    }
    resp.raise_for_status.return_value = None
    return resp


VALID_THEOREM = (
    "theorem Ring_mul_assoc (R : Type*) [CommRing R] (a b c : R) :\n"
    "  a * (b * c) = a * b * c := by\n"
    "  ring"
)

VALID_LEMMA = "lemma Ring_one_mul (R : Type*) [Ring R] (a : R) :\n  1 * a = a := by\n  simp"

LLM_RESPONSE_WITH_CODE_BLOCK = (
    "Here is a conjecture for the missing declaration:\n\n"
    "```lean\n"
    "theorem Ring_foo (R : Type*) [Ring R] : (1 : R) = 1 := by rfl\n"
    "```\n"
)


# ---------------------------------------------------------------------------
# generate() tests
# ---------------------------------------------------------------------------


class TestGenerate:
    @patch("autonomous_discovery.conjecture_generator.llm_generator.httpx")
    def test_returns_candidate_from_valid_response(self, mock_httpx: MagicMock) -> None:
        mock_httpx.post.return_value = _ollama_response(VALID_THEOREM)

        gen = OllamaConjectureGenerator()
        candidates = gen.generate([_make_gap()], max_candidates=1)

        assert len(candidates) == 1
        c = candidates[0]
        assert c.gap_missing_decl == "Ring.mul_assoc"
        assert "Ring_mul_assoc" in c.lean_statement
        assert "CommRing R" in c.lean_statement
        assert ":= by" not in c.lean_statement
        assert c.model_id == "gpt-oss-20b"
        assert c.temperature == 0.7

    @patch("autonomous_discovery.conjecture_generator.llm_generator.httpx")
    def test_respects_max_candidates(self, mock_httpx: MagicMock) -> None:
        mock_httpx.post.return_value = _ollama_response(VALID_THEOREM)

        gaps = [_make_gap(missing_decl=f"Ring.thm_{i}", score=0.9 - i * 0.1) for i in range(5)]
        gen = OllamaConjectureGenerator()
        candidates = gen.generate(gaps, max_candidates=2)

        assert len(candidates) <= 2

    @patch("autonomous_discovery.conjecture_generator.llm_generator.httpx")
    def test_empty_gaps_returns_empty(self, mock_httpx: MagicMock) -> None:
        gen = OllamaConjectureGenerator()
        candidates = gen.generate([], max_candidates=5)
        assert candidates == []
        mock_httpx.post.assert_not_called()

    @patch("autonomous_discovery.conjecture_generator.llm_generator.httpx")
    def test_max_candidates_zero_returns_empty(self, mock_httpx: MagicMock) -> None:
        gen = OllamaConjectureGenerator()
        candidates = gen.generate([_make_gap()], max_candidates=0)
        assert candidates == []
        mock_httpx.post.assert_not_called()

    @patch("autonomous_discovery.conjecture_generator.llm_generator.httpx")
    def test_handles_connection_error_gracefully(self, mock_httpx: MagicMock) -> None:
        mock_httpx.HTTPError = httpx.HTTPError
        mock_httpx.post.side_effect = httpx.ConnectError("Connection refused")

        gen = OllamaConjectureGenerator()
        candidates = gen.generate([_make_gap()], max_candidates=1)
        assert candidates == []

    @patch("autonomous_discovery.conjecture_generator.llm_generator.httpx")
    def test_retries_on_parse_failure_then_succeeds(self, mock_httpx: MagicMock) -> None:
        """First two calls return garbage, third returns valid theorem."""
        mock_httpx.post.side_effect = [
            _ollama_response("Here is some text without theorems."),
            _ollama_response("Still no theorem here."),
            _ollama_response(VALID_THEOREM),
        ]

        config = LLMConfig(parse_retries=2)
        gen = OllamaConjectureGenerator(config=config)
        candidates = gen.generate([_make_gap()], max_candidates=1)

        assert len(candidates) == 1
        assert mock_httpx.post.call_count == 3

    @patch("autonomous_discovery.conjecture_generator.llm_generator.httpx")
    def test_skips_gap_after_exhausting_retries(self, mock_httpx: MagicMock) -> None:
        mock_httpx.post.return_value = _ollama_response("No valid Lean here.")

        config = LLMConfig(parse_retries=2)
        gen = OllamaConjectureGenerator(config=config)
        candidates = gen.generate([_make_gap()], max_candidates=1)

        assert candidates == []
        # 1 initial + 2 retries = 3 calls
        assert mock_httpx.post.call_count == 3

    @patch("autonomous_discovery.conjecture_generator.llm_generator.httpx")
    def test_uses_configured_model_and_temperature(self, mock_httpx: MagicMock) -> None:
        mock_httpx.post.return_value = _ollama_response(VALID_THEOREM)

        config = LLMConfig(model_name="custom-model", temperature=0.3)
        gen = OllamaConjectureGenerator(config=config)
        candidates = gen.generate([_make_gap()], max_candidates=1)

        call_kwargs = mock_httpx.post.call_args
        payload = call_kwargs.kwargs.get("json") or call_kwargs[1]["json"]
        assert payload["model"] == "custom-model"
        assert payload["options"]["temperature"] == 0.3

        assert candidates[0].model_id == "custom-model"
        assert candidates[0].temperature == 0.3

    @patch("autonomous_discovery.conjecture_generator.llm_generator.httpx")
    def test_sends_request_to_configured_url(self, mock_httpx: MagicMock) -> None:
        mock_httpx.post.return_value = _ollama_response(VALID_THEOREM)

        config = LLMConfig(ollama_base_url="http://my-server:9999")
        gen = OllamaConjectureGenerator(config=config)
        gen.generate([_make_gap()], max_candidates=1)

        url = mock_httpx.post.call_args[0][0]
        assert url == "http://my-server:9999/api/chat"

    @patch("autonomous_discovery.conjecture_generator.llm_generator.httpx")
    def test_prompt_includes_gap_context(self, mock_httpx: MagicMock) -> None:
        mock_httpx.post.return_value = _ollama_response(VALID_THEOREM)

        gap = _make_gap(
            source_decl="Group.mul_inv_cancel",
            target_family="Ring.",
            missing_decl="Ring.mul_inv_cancel",
        )
        gen = OllamaConjectureGenerator()
        gen.generate([gap], max_candidates=1)

        call_kwargs = mock_httpx.post.call_args
        payload = call_kwargs.kwargs.get("json") or call_kwargs[1]["json"]
        messages = payload["messages"]
        assert len(messages) >= 2
        user_msg = messages[-1]["content"]
        assert "Group.mul_inv_cancel" in user_msg
        assert "Ring." in user_msg
        assert "Ring.mul_inv_cancel" in user_msg

    @patch("autonomous_discovery.conjecture_generator.llm_generator.httpx")
    def test_extracts_lemma_declarations(self, mock_httpx: MagicMock) -> None:
        mock_httpx.post.return_value = _ollama_response(VALID_LEMMA)

        gen = OllamaConjectureGenerator()
        candidates = gen.generate([_make_gap()], max_candidates=1)

        assert len(candidates) == 1
        assert "Ring_one_mul" in candidates[0].lean_statement

    @patch("autonomous_discovery.conjecture_generator.llm_generator.httpx")
    def test_metadata_includes_source_and_score(self, mock_httpx: MagicMock) -> None:
        mock_httpx.post.return_value = _ollama_response(VALID_THEOREM)

        gap = _make_gap(source_decl="Group.mul_assoc", score=0.85)
        gen = OllamaConjectureGenerator()
        [candidate] = gen.generate([gap], max_candidates=1)

        assert candidate.metadata["source_decl"] == "Group.mul_assoc"
        assert candidate.metadata["target_family"] == "Ring."
        assert candidate.metadata["score"] == "0.850000"

    @patch("autonomous_discovery.conjecture_generator.llm_generator.httpx")
    def test_sorts_gaps_by_score_descending(self, mock_httpx: MagicMock) -> None:
        mock_httpx.post.return_value = _ollama_response(VALID_THEOREM)

        gaps = [
            _make_gap(missing_decl="Ring.low", score=0.3),
            _make_gap(missing_decl="Ring.high", score=0.9),
            _make_gap(missing_decl="Ring.mid", score=0.6),
        ]
        gen = OllamaConjectureGenerator()
        candidates = gen.generate(gaps, max_candidates=1)

        assert len(candidates) == 1
        assert candidates[0].gap_missing_decl == "Ring.high"

    @patch("autonomous_discovery.conjecture_generator.llm_generator.httpx")
    def test_handles_http_status_error(self, mock_httpx: MagicMock) -> None:
        mock_httpx.HTTPError = httpx.HTTPError
        resp = MagicMock(spec=httpx.Response)
        resp.status_code = 500
        resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Server Error", request=MagicMock(), response=resp
        )
        mock_httpx.post.return_value = resp

        gen = OllamaConjectureGenerator()
        candidates = gen.generate([_make_gap()], max_candidates=1)
        assert candidates == []


# ---------------------------------------------------------------------------
# _parse_lean_statements() tests
# ---------------------------------------------------------------------------


class TestParseLeanStatements:
    def test_extracts_theorem_without_proof(self) -> None:
        gen = OllamaConjectureGenerator()
        stmts = gen._parse_lean_statements(VALID_THEOREM)
        assert len(stmts) == 1
        assert ":= by" not in stmts[0]
        assert "Ring_mul_assoc" in stmts[0]
        assert "a * (b * c) = a * b * c" in stmts[0]

    def test_extracts_from_code_block(self) -> None:
        gen = OllamaConjectureGenerator()
        stmts = gen._parse_lean_statements(LLM_RESPONSE_WITH_CODE_BLOCK)
        assert len(stmts) >= 1
        assert "Ring_foo" in stmts[0]

    def test_returns_empty_for_no_theorems(self) -> None:
        gen = OllamaConjectureGenerator()
        stmts = gen._parse_lean_statements("Just some explanation text.")
        assert stmts == []

    def test_handles_multiline_statement(self) -> None:
        raw = (
            "theorem Ring_mul_comm\n"
            "    (R : Type*) [CommRing R] (a b : R) :\n"
            "    a * b = b * a := by\n"
            "  ring"
        )
        gen = OllamaConjectureGenerator()
        stmts = gen._parse_lean_statements(raw)
        assert len(stmts) == 1
        assert "Ring_mul_comm" in stmts[0]
        assert "a * b = b * a" in stmts[0]

    def test_extracts_lemma(self) -> None:
        gen = OllamaConjectureGenerator()
        stmts = gen._parse_lean_statements(VALID_LEMMA)
        assert len(stmts) == 1
        assert "Ring_one_mul" in stmts[0]

    def test_handles_where_clause(self) -> None:
        raw = (
            "theorem Ring_mul_comm {R : Type*} [CommRing R] (a b : R) :\n"
            "    a * b = b * a where\n"
            "  aux := sorry"
        )
        gen = OllamaConjectureGenerator()
        stmts = gen._parse_lean_statements(raw)
        assert len(stmts) >= 1
        assert "Ring_mul_comm" in stmts[0]
        assert ":=" not in stmts[0]
        assert "where" not in stmts[0]

    def test_returns_empty_for_empty_string(self) -> None:
        gen = OllamaConjectureGenerator()
        assert gen._parse_lean_statements("") == []
