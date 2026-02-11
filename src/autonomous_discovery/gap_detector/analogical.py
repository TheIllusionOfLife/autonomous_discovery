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
    min_cross_family_hits: int = 1
    min_cross_family_overlap: float = 0.25
    require_namespace_stem_match: bool = True


@dataclass(slots=True)
class AnalogicalGapDetector:
    """Detects missing theorem counterparts across declaration families."""

    config: GapDetectorConfig = field(default_factory=GapDetectorConfig)

    def detect(self, graph: MathlibGraph, top_k: int | None = None) -> list[GapCandidate]:
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
        family_stems = {
            prefix: {
                stem
                for name in family_nodes.get(prefix, set())
                if (stem := self._namespace_stem(self._suffix_after_prefix(name, prefix)))
                is not None
            }
            for prefix in self.config.family_prefixes
        }

        for source_prefix in self.config.family_prefixes:
            for source_decl in family_nodes.get(source_prefix, set()):
                suffix = self._suffix_after_prefix(source_decl, source_prefix)
                if not suffix:
                    continue
                suffix_stem = self._namespace_stem(suffix)
                source_deps = graph.dependencies_of(source_decl)

                pr_signal = pagerank.get(source_decl, 0.0) / max_pr if max_pr > 0 else 0.0
                descendants = graph.descendants_count(source_decl)
                descendant_signal = descendants / (descendants + 10) if descendants > 0 else 0.0

                for target_prefix in self.config.family_prefixes:
                    if target_prefix == source_prefix:
                        continue
                    if not family_nodes.get(target_prefix):
                        continue

                    missing_decl = f"{target_prefix}{suffix}"
                    if missing_decl in nodes:
                        continue

                    namespace_stem_match = suffix_stem is None or suffix_stem in family_stems.get(
                        target_prefix, set()
                    )
                    if self.config.require_namespace_stem_match and not namespace_stem_match:
                        continue

                    translated_total, translated_hits, cross_total, cross_hits = (
                        self._translated_dependency_stats(
                            source_deps=source_deps,
                            source_prefix=source_prefix,
                            target_prefix=target_prefix,
                            nodes=nodes,
                        )
                    )
                    dep_overlap = (
                        translated_hits / translated_total if translated_total > 0 else 0.0
                    )
                    cross_overlap = cross_hits / cross_total if cross_total > 0 else 0.0
                    if cross_hits < self.config.min_cross_family_hits:
                        continue
                    if cross_overlap < self.config.min_cross_family_overlap:
                        continue

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
                                "cross_family_hits": float(cross_hits),
                                "cross_family_total": float(cross_total),
                                "cross_family_overlap": cross_overlap,
                                "namespace_stem_match": 1.0 if namespace_stem_match else 0.0,
                            },
                        )
                    )

        ranked.sort(key=lambda c: (-c.score, c.missing_decl, c.source_decl, c.target_family))
        effective_top_k = self.config.top_k if top_k is None else top_k
        return ranked[:effective_top_k]

    def _translated_dependency_stats(
        self,
        *,
        source_deps: list[str],
        source_prefix: str,
        target_prefix: str,
        nodes: set[str],
    ) -> tuple[int, int, int, int]:
        if not source_deps:
            return 0, 0, 0, 0

        translated_total = len(source_deps)
        translated_hits = 0
        cross_total = 0
        cross_hits = 0
        for dep in source_deps:
            if dep.startswith(source_prefix):
                cross_total += 1
                translated_dep = f"{target_prefix}{dep[len(source_prefix) :]}"
            else:
                translated_dep = dep
            if translated_dep in nodes:
                translated_hits += 1
                if dep.startswith(source_prefix):
                    cross_hits += 1
        return translated_total, translated_hits, cross_total, cross_hits

    def _namespace_stem(self, suffix: str) -> str | None:
        if "." not in suffix:
            return None
        stem = suffix.split(".", maxsplit=1)[0]
        return stem if stem else None

    def _suffix_after_prefix(self, decl_name: str, prefix: str) -> str:
        suffix = decl_name[len(prefix) :]
        return suffix.lstrip(".")
