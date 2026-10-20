# Development contract

Find repeated directory trees even when the files inside them differ.

Version 1.1 adds explicit ignore/depth controls and deterministic structural fingerprints while remaining content-agnostic and read-only.

Preserve deterministic, source-safe behavior and the interpretation boundary documented in the README. Every feature release must update tests, version metadata, changelog, README claims, repository metadata, release assets, and the Forge catalog together.

The 1.2.1 audit unifies both scanners, preserves uncertainty for unreadable
subtrees and makes report creation exclusive. Keep the 90% branch-coverage gate
and strict type checking. No content equivalence may be inferred from topology.
