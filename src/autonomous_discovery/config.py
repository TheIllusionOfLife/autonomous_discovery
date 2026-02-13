"""Central configuration for the autonomous discovery system."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


@dataclass(frozen=True)
class LLMConfig:
    """Configuration for LLM inference via Ollama."""

    ollama_base_url: str = "http://localhost:11434"
    model_name: str = "gpt-oss:20b"
    temperature: float = 0.7
    max_tokens: int = 2048
    parse_retries: int = 2
    timeout: float = 120.0


@dataclass(frozen=True)
class ProjectConfig:
    """Immutable project-wide configuration."""

    # Paths
    project_root: Path = PROJECT_ROOT
    data_raw_dir: Path = field(init=False)
    data_processed_dir: Path = field(init=False)
    lean_project_dir: Path = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "data_raw_dir", self.project_root / "data" / "raw")
        object.__setattr__(self, "data_processed_dir", self.project_root / "data" / "processed")
        object.__setattr__(self, "lean_project_dir", self.project_root / "lean" / "LeanExtract")

    # Data files
    premises_file: str = "premises.txt"
    decl_types_file: str = "decl_types.txt"

    # Domain scope — declaration name prefixes for algebra subset
    # (Lean names use short prefixes, not full module paths)
    algebra_name_prefixes: tuple[str, ...] = (
        "Algebra.",
        "CommRing.",
        "Field.",
        "Group.",
        "Ideal.",
        "LinearMap.",
        "Matrix.",
        "Module.",
        "MonoidHom.",
        "MulAction.",
        "Polynomial.",
        "Ring.",
        "RingHom.",
        "Subgroup.",
        "Submodule.",
        "Subring.",
    )

    # Data leakage cutoff — theorems after this date are held out
    cutoff_date: date = date(2024, 8, 1)

    # Go/no-go thresholds (from project spec)
    min_post_cutoff_theorems: int = 30
    min_detection_rate: float = 0.05
    min_top20_precision: float = 0.60
    min_nontrivial_gaps: int = 20

    # Lean bridge
    lean_timeout: int = 300  # seconds
    proof_local_retries: int = 3

    # LLM inference (Ollama)
    llm: LLMConfig = field(default_factory=lambda: LLMConfig())

    @property
    def premises_path(self) -> Path:
        return self.data_raw_dir / self.premises_file

    @property
    def decl_types_path(self) -> Path:
        return self.data_raw_dir / self.decl_types_file
