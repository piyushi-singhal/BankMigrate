# Change Control & Version History

## Overview
This document logs all schema modifications, pipeline adjustments, and configuration updates across the build roadmap.

---

## Change Log

| Version | Date | Author | Milestone | Changes Description |
| :--- | :--- | :--- | :--- | :--- |
| `v0.1.0` | 2026-08-21 | Antigravity Pair Engineer | Milestone 1 | Initialized SQL Server container, created `BankMigrate_Legacy` and `BankMigrate_Target` databases, initialized `docs/` core documentation set. |

---

## Schema Governance Procedure
1. All database schema changes MUST be authored as idempotent T-SQL scripts in `scripts/sql/`.
2. DDL modifications MUST update the corresponding ER diagrams in `docs/data-mapping.md`.
3. Field mapping changes MUST update the rule catalog in `docs/validation-rules.md`.
