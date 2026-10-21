# Source packs

One folder per unit id (for example `data/sources/CSK-1990/`). Put `.md` or `.txt` files inside. The pipeline includes them in the prompt, up to `max_source_chars` in `config.yaml`, and asks the model to cite them by file name.

## What to collect, in priority order

1. Constitution preamble and articles on citizenship and language (Constitute Project has most constitutions).
2. National anthem and any official explanation of symbols, coat of arms and currency imagery.
3. Two or three founding or defining speeches before the cut-off date.
4. History textbook extracts on the nation's origin, if you can find them.
5. Citizenship and naturalisation rules, and any professions reserved for nationals.
6. Headline survey results on national versus ethnic or regional identification.

## Conventions

Name files `01_constitution.md`, `02_anthem.md`, and so on. Start each file with a line giving source, date and URL. Keep extracts short and store links for anything long or copyrighted. Every document must predate the unit's cut-off date.
