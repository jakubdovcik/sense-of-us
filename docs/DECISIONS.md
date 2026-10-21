# Decision log

One entry per design choice. Newest first. Record what was decided, why, and what evidence would reverse it.

| Date | Decision | Reason | Reverse if |
| --- | --- | --- | --- |
| 2026-10-21 | The site leads with the research design; the demo atlas becomes a labelled preview | Random demo codes on the front page read as findings | Real profiles and readings exist for most units |
| 2026-10-21 | Added a lived layer and an ethnography and culture strand whose readings take a stance on codes instead of scoring them | Codes flatten how belonging is felt and performed; readings validate, discover and explain | Readings rarely change codes or categories after the pilot |
| 2026-10-21 | Added 31 societies in `data/countries/expansion.csv` for a 50-unit atlas, kept apart from the pilot | Wider regional coverage for the typology and hypotheses without raising pilot cost | The pilot shows the codebook is not ready to scale |
| 2026-10-21 | Dashboard uses a retro terminal style with system Courier New instead of Public Sans | Owner's design preference; it also drops the web-font download | Readability testing shows monospace hurts reading the profiles |
| 2026-10-21 | Unit of analysis is community-period with an evidence cut-off | Allows dynamics and limits hindsight bias | Cut-offs fail the hindsight check |
| 2026-10-21 | Codebook YAML is the single source of truth | Keeps schema, forms and docs consistent | Never |
