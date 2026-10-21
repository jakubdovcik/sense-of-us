# Sense of Us codebook (v0.1)

Generated from `codebook/codebook.yaml`. Do not edit by hand.

## Radius (`radius`)

*How many people does the operative 'us' include?*

Type ordinal.

| Code | Anchor |
| --- | --- |
| 0 | Kin, clan or locality only; the state is experienced as someone else's |
| 1 | One ethnic, religious or regional group within the state |
| 2 | A dominant group, with minorities tolerated but not fully 'us' |
| 3 | All citizens regardless of origin, language or faith |
| 4 | All citizens plus a wider supranational or universal community |

## Boundary permeability (`boundary`)

*How easily can an outsider become part of the 'us', in law and in practice?*

Type ordinal.

| Code | Anchor |
| --- | --- |
| 0 | Closed by descent; naturalisation rare; many roles reserved for nationals |
| 1 | Naturalisation possible but long and discretionary; strong informal exclusion |
| 2 | Formal routes exist; migrants accepted economically but not socially |
| 3 | Routine naturalisation; second generation broadly accepted as 'us' |
| 4 | Migrants seen as future members; few reserved roles; dual identities normal |

## Glue (`glue`)

*What primarily binds the 'us' together?*

Type multilabel.

| Option | Meaning |
| --- | --- |
| `language` | A shared language or the struggle to defend it |
| `religion` | A shared faith, church or religious mission |
| `descent` | Common ancestry, ethnicity or 'blood' |
| `civic` | A constitution, rights, institutions or political creed |
| `founding_struggle` | A revolution, war of independence or unification |
| `anti_colonial` | Resistance to a colonial or imperial power |
| `external_enemy` | A present or historical neighbour or rival |
| `shared_trauma` | A defining catastrophe, genocide, famine or defeat |
| `dynasty` | A monarchy, ruling family or founding leader cult |
| `territory` | Land, landscape, homeland or frontier |
| `modernisation` | A shared developmental or economic project |
| `ritual_culture` | Sport, music, cuisine, festivals or popular culture |
| `other` | Something the list misses (describe it in open_features) |

## Myth arc (`myth_arc`)

*Which elements of a foundational myth are present and widely taught?*

Type flags.

| Option | Meaning |
| --- | --- |
| `origin` | A story of how 'we' began |
| `golden_age` | A past period of greatness |
| `fall` | A betrayal, decline, defeat or occupation |
| `chosen_trauma` | A collective wound passed between generations |
| `redemption` | A rebirth, liberation or restoration |
| `heroes` | Founding heroes treated as shared property |
| `mission` | A sense of being chosen or having a special role |

## Orientation (`orientation`)

*Is the 'us' defined mainly by a shared project or against an enemy?*

Type ordinal.

| Code | Anchor |
| --- | --- |
| -2 | Strongly defined against an internal or external enemy |
| -1 | Mainly defined against others, with a weak project |
| 0 | Mixed or unclear |
| 1 | Mainly defined by a shared project, with some enemy framing |
| 2 | Strongly defined by a forward-looking shared project |

Extra field `named_others`. Groups or states cast as 'them' (list).

Extra field `named_project`. The shared project, if any (text).

## Contestation (`contestation`)

*How far do rival narratives of 'us' compete within the society?*

Type ordinal.

| Code | Anchor |
| --- | --- |
| 0 | One narrative, broadly uncontested |
| 1 | Minor dissent from small groups |
| 2 | A significant rival narrative held by a sizeable minority |
| 3 | Two or more rival narratives of comparable weight |
| 4 | Open conflict over who 'we' are; secession or civil war plausible |

Extra field `rival_narratives`. Each rival narrative, who holds it and its rough weight (list).

## Elite–mass bond (`vertical_bond`)

*Do elites and ordinary people share institutions, experiences and mutual regard?*

Type ordinal.

| Code | Anchor |
| --- | --- |
| 0 | Elites live apart (schools, health, residence often abroad) and are openly disdained |
| 1 | Largely separate lives; low trust in experts and officials |
| 2 | Partly shared institutions; trust divided by class or region |
| 3 | Mostly shared institutions (public schools, service, health); moderate trust |
| 4 | Shared schooling, service or civic rituals; elites identify with ordinary people |

## Salience (`salience`)

*How strongly is the 'us' felt and how easily can it be mobilised?*

Type ordinal.

| Code | Anchor |
| --- | --- |
| 0 | Barely felt; other identities dominate daily life |
| 1 | Felt weakly, mainly at ceremonies or sporting events |
| 2 | Moderately felt; can be mobilised in a crisis |
| 3 | Strongly felt; routinely invoked in politics |
| 4 | Overriding; most people would sacrifice heavily for it |

## Nesting (`nesting`)

*How does this 'us' relate to sub-national and supranational identities?*

Type relations.

| Relation | Meaning |
| --- | --- |
| `nested` | Compatible; people hold both comfortably |
| `competing` | In tension; gains for one feel like losses for the other |
| `absent` | No meaningful identity at that level |

## Hypothesised types

| Type | Profile |
| --- | --- |
| `civic_project` | Wide radius, permeable boundary, civic or modernisation glue, project orientation |
| `ethnic_defensive` | Narrow radius, closed boundary, descent or language glue, enemy orientation |
| `revolutionary` | Founding struggle glue, strong myth arc, enemy-leaning orientation, high salience |
| `dynastic_religious` | Dynasty or religion glue, low contestation, vertical bond through ritual |
| `consociational` | High contestation managed by power-sharing; nesting of competing sub-identities |
| `thin_state` | Low salience, narrow radius, sub-national identities dominate |
