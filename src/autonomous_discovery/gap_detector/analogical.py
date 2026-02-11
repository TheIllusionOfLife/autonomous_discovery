"""Analogical gap detector for declaration-family counterparts."""

from __future__ import annotations

from dataclasses import dataclass, field

from autonomous_discovery.knowledge_base.graph import MathlibGraph


@dataclass(frozen=True, slots=True)
class GapCandidate:
    """A ranked candidate gap inferred by cross-family analogy."""

    source_decl: str
    target_family: str
    missing_decl: str
    score: float
    signals: dict[str, float]


@dataclass(frozen=True, slots=True)
class GapDetectorConfig:
    """Configuration for analogical gap detection."""

    family_prefixes: tuple[str, ...] = ("Group.", "Ring.", "Module.")
    min_score: float = 0.20
    top_k: int = 20
    seed_sources_enabled: bool = True
    weight_dependency_overlap: float = 0.55
    weight_pagerank: float = 0.30
    weight_descendants: float = 0.15


@dataclass(slots=True)
class AnalogicalGapDetector:
    """Detects missing theorem counterparts across declaration families."""

    config: GapDetectorConfig = field(default_factory=GapDetectorConfig)

    def detect(self, graph: MathlibGraph, top_k: int = 20) -> list[GapCandidate]:
        """Return top-k ranked gap candidates."""
        nodes = set(graph.nodes())
        if not nodes:
            return []

        ranked: list[GapCandidate] = []
        pagerank = graph.pagerank()
        max_pr = max(pagerank.values()) if pagerank else 1.0

        family_nodes = {
            prefix: {n for n in nodes if n.startswith(prefix)}
            for prefix in self.config.family_prefixes
        }

        for source_prefix in self.config.family_prefixes:
            for source_decl in family_nodes.get(source_prefix, set()):
                suffix = source_decl[len(source_prefix) :]
                if not suffix:
                    continue

                for target_prefix in self.config.family_prefixes:
                    if target_prefix == source_prefix:
                        continue
                    if not family_nodes.get(target_prefix):
                        continue

                    missing_decl = f"{target_prefix}{suffix}"
                    if missing_decl in nodes:
                        continue

                    translated_total, translated_hits = self._translated_dependency_stats(
                        graph=graph,
                        source_decl=source_decl,
                        source_prefix=source_prefix,
                        target_prefix=target_prefix,
                        nodes=nodes,
                    )
                    dep_overlap = (
                        translated_hits / translated_total if translated_total > 0 else 0.0
                    )
                    pr_signal = pagerank.get(source_decl, 0.0) / max_pr if max_pr > 0 else 0.0
                    descendants = graph.descendants_count(source_decl)
                    descendant_signal = (
                        descendants / (descendants + 10) if descendants > 0 else 0.0
                    )

                    score = (
                        self.config.weight_dependency_overlap * dep_overlap
                        + self.config.weight_pagerank * pr_signal
                        + self.config.weight_descendants * descendant_signal
                    )

                    if score < self.config.min_score:
                        continue

                    ranked.append(
                        GapCandidate(
                            source_decl=source_decl,
                            target_family=target_prefix,
                            missing_decl=missing_decl,
                            score=score,
                            signals={
                                "dependency_overlap": dep_overlap,
                                "translated_dependency_hits": float(translated_hits),
                                "translated_dependency_total": float(translated_total),
                                "source_pagerank": pr_signal,
                                "source_descendants": float(descendants),
                            },
                        )
                    )

        ranked.sort(key=lambda c: (-c.score, c.missing_decl, c.source_decl, c.target_family))
        effective_k = min(top_k, self.config.top_k)
        return ranked[:effective_k]

    def _translated_dependency_stats(
        self,
        *,
        graph: MathlibGraph,
        source_decl: str,
        source_prefix: str,
        target_prefix: str,
        nodes: set[str],
    ) -> tuple[int, int]:
        deps = graph.dependencies_of(source_decl)
        if not deps:
            return 0, 0

        translated_total = 0
        translated_hits = 0
        for dep in deps:
            if dep.startswith(source_prefix):
                translated_dep = f"{target_prefix}{dep[len(source_prefix) :]}"
            else:
                translated_dep = dep
            translated_total += 1
            if translated_dep in nodes:
                translated_hits += 1
        return translated_total, translated_hits
