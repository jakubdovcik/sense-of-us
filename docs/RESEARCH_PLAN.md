# Research plan

The end product is the Sense of Us atlas, a dashboard on GitHub Pages that rebuilds from the data every time the repository changes.

## 1. Set up

- [ ] Push the repository to GitHub and switch on the dashboard (see `CLAUDE.md`)
- [ ] Add an Anthropic API key to `.env` and set a monthly spend limit
- [ ] Confirm current model names and prices; update `config.yaml`

## 2. Pin down the theory

- [ ] Watch the GEM18 lecture and record every claim about the sense of us in `docs/hausmann_notes.md`
- [ ] Read the Hausmann sources in `docs/LITERATURE.md`
- [ ] Write each causal claim as "X leads to Y because Z" and map it to a dimension and hypothesis in `docs/FRAMEWORK.md`
- [ ] Read the empirical nation-building papers and note what each implies for measurement
- [ ] Write a one-page definition memo
- [ ] Decide whether the atlas is mainly a teaching tool, a diagnostic input or an academic dataset

## 3. Calibrate the codebook by hand

- [ ] Build source packs for Czechoslovakia 1990–92, Slovakia 2015–24 and Czechia 2015–24
- [ ] Hand-code all three with the rating forms
- [ ] Record every anchor that did not fit in `docs/DECISIONS.md`
- [ ] Revise `codebook/codebook.yaml` and regenerate the schema and docs

## 4. Harden the pipeline

- [ ] Run one real profile per calibration case and compare it with the hand codes
- [ ] Tune the prompts until the model reads the anchors correctly
- [ ] Add batch processing, narrative-only mode, per-unit comparison reports and the hindsight flag (tasks T1 to T4 in `CLAUDE.md`)

## 5. Run the pilot

- [ ] Build source packs for the other nine pilot units
- [ ] Run a two-unit test and check cost and quality
- [ ] Run the full pilot across two models, two source languages and three runs
- [ ] Run group perspectives for the contested units
- [ ] Check every evidence item in four units for fabricated sources (task T5)
- [ ] Commit the profiles so the dashboard rebuilds with real data

## 6. Validate with people

- [ ] Recruit two nationals per pilot unit as raters
- [ ] Collect blind ratings and enter them in `data/ratings/ratings.csv`
- [ ] Run `sou compare-ratings`
- [ ] Interview the raters behind the largest disagreements
- [ ] Add a human-agreement view to the dashboard (task T6)

## 7. Build the typology

- [ ] Run `sou open-code` and accept or reject each proposed category
- [ ] Revise the codebook by the rules in `docs/FRAMEWORK.md` section 7 and re-run changed dimensions
- [ ] Pick the clustering solution that is most interpretable and name each type in `docs/TYPOLOGY.md`
- [ ] Freeze the codebook at v0.5

## 8. Study change over time

- [ ] Run the historical slices in `data/countries/dynamics.csv`
- [ ] Code each transition between periods and its trigger
- [ ] Run the hindsight check on Venezuela 1990–98 and Yugoslavia 1974–80
- [ ] Write case studies of Germany, Yugoslavia, Venezuela and the EU in `docs/DYNAMICS.md`

## 9. Link to outcomes

- [ ] Load economic complexity, state capacity, fractionalisation and survey trust data (task T7)
- [ ] Compute myth gaps from narrative-only profiles against survey identification (task T8)
- [ ] Add an outcomes view to the dashboard plotting each hypothesis (task T9)
- [ ] Record which hypotheses look promising and the sample size needed to test them in `docs/FINDINGS.md`

## 10. Publish

- [ ] Write the working paper or memo
- [ ] Prepare a ten-slide presentation built around dashboard screenshots
- [ ] Write the scale-up proposal (countries, cost, validation)
- [ ] Tag release v0.5 (task T10)
