"""Conjecture generator implementations and interfaces."""

from autonomous_discovery.conjecture_generator.io import read_conjectures, write_conjectures
from autonomous_discovery.conjecture_generator.llm_generator import OllamaConjectureGenerator
from autonomous_discovery.conjecture_generator.models import ConjectureCandidate
from autonomous_discovery.conjecture_generator.protocol import ConjectureGenerator
from autonomous_discovery.conjecture_generator.template import TemplateConjectureGenerator

__all__ = [
    "ConjectureCandidate",
    "ConjectureGenerator",
    "OllamaConjectureGenerator",
    "TemplateConjectureGenerator",
    "read_conjectures",
    "write_conjectures",
]
