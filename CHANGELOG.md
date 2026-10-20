# Changelog

## 1.2.1 — 2026-10-20

- Use one explicit scanner in both modes, pruning ignored branches and reporting unreadable paths.
- Withhold duplicate claims for incomplete trees while retaining verified sibling groups.
- Reject symlink roots and malformed input controls; skip descendant links consistently.
- Create reports exclusively and return status 1 for incomplete scans.

## 1.2.0 — 2026-10-15

- Explain shared and differing directory paths between two selected roots.
- Report unreadable comparisons as incomplete and skip descendant symlinks.

## 1.1.0 - 2026-07-27

- Added configurable ignored directory names and minimum descendant depth.
- Added deterministic structural fingerprints and descendant counts to duplicate groups.

## 1.0.0 - 2026-07-26

- Released the first complete Duplicate Folder Structure Detector command-line workflow.
- Added deterministic reporting, representative examples, cross-platform tests, and explicit limitations.
