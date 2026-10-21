# Decision log

One entry per design choice. Newest first. Record what was decided, why, and what evidence would reverse it.

| Date | Decision | Reason | Reverse if |
| --- | --- | --- | --- |
| 2026-10-21 | Dashboard uses a retro terminal style with system Courier New instead of Public Sans | Owner's design preference; it also drops the web-font download | Readability testing shows monospace hurts reading the profiles |
| 2026-10-21 | Unit of analysis is community-period with an evidence cut-off | Allows dynamics and limits hindsight bias | Cut-offs fail the hindsight check |
| 2026-10-21 | Codebook YAML is the single source of truth | Keeps schema, forms and docs consistent | Never |
