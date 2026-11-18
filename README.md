# Pneumonia share of pneumonia and chronic lower respiratory disease deaths in South Korea rises with ill-defined causes within districts

Analysis code for the manuscript

> Kim S. *Pneumonia share of pneumonia and chronic lower respiratory disease deaths in South Korea rises with ill-defined causes within districts.* Manuscript submitted for publication.

Version 1.0.0 of this repository is archived on Zenodo; the DOI is given in the article's Data availability statement.

## Contents

This repository contains code only. The processed district-year data (master table, analytic panel, expected deaths, result tables, adjacency graph and boundary file) are not included; they are available from the author on reasonable request. All source statistics are public (see Data sources).

| Path | What it is |
|---|---|
| `01_스크립트/` | Analysis scripts (below) |
| `04_분석/RESP/sets_RESP_std3.json`, `config_RESP_std3.json` | Characteristics with expected directions, forced controls, negative control exposures and model settings |
| `04_분석/RESP/MS/build/` | Scripts that read the result tables and write every number, table and figure in the manuscript and supplementary material, including `content_resp.py`, which generates the Methods and Results text (the draft source of the Introduction and Discussion is not included) |

Folder and some column names are in Korean because the source tables are Korean; each script has a header comment describing its inputs and outputs.

## Data sources

All inputs are public, aggregated statistics. No individual-level data are included.

- Deaths by underlying cause (pneumonia, ICD-10 J12-J18; chronic lower respiratory disease, J40-J47; all respiratory, J00-J98; ill-defined causes, R00-R99; senility, R54; all causes) by district of residence: Statistics Korea, cause-of-death statistics (KOSIS DT_1B34E13), 2011-2024.
- National deaths by cause, sex and 5-year age group: Statistics Korea (KOSIS DT_1B34E01), fetched by `34_fetch_national_cause_age_deaths.py` (requires a personal KOSIS API key in `~/.kosis_key`; the key is not included).
- Population by 5-year age group: Ministry of the Interior and Safety, resident registration statistics. The 2023 age block of Changwon duplicated the 2022 block and was corrected.
- District characteristics: the Community Health Survey (current smoking, influenza vaccination, chewing discomfort, walking, moderate physical activity), National Health Insurance Service general health screening (suspected pulmonary tuberculosis), care institution statistics (long-term care hospitals), the public sports facility register, Korean Statistical Information Service local indicators and a harmonised public district panel (internal medicine specialists, basic livelihood security recipients).

## Pipeline

Run from the repository root (set `ST_DATA_ROOT` and `ST_CANON` to the local copies of the public source files).

| Step | Script | Output |
|---|---|---|
| 0 | `34_fetch_national_cause_age_deaths.py`, `39m_build_Estd_mort.py` | National cause-by-age deaths and expected deaths by indirect standardisation in eighteen 5-year age groups |
| 1 | `99b_extra_canonical_pool.py`, `99c_extra_canonical_pool_pneu.py`, `99c_extra_canonical_pool_resp.py` | Ill-defined and senility shares, long-term care hospitals, internal medicine specialists and basic livelihood recipients (implausible values set to missing and interpolated), joined by district code |
| 2 | `80_build_disease_panel_v.py RESP` (`ST_VER=std3`), `37R_build_binom_panel.py` | Analytic panel with pneumonia and CLRD deaths, expected composition and logit offset |
| 3 | `37R_fit_binom.R` (`MODE=main`, `win`, `sens`, `mv` with `MV_RANGE`; `ST_GRAPH=04_분석/RESP/graph_593.graph`, `ST_THREADS=1`, wrapped in `rslot.sh`) | Likelihood choice, principal model, characteristic groups, negative controls, speed models, within-between decomposition, windows, sensitivity analyses, 200-subset multiverse |
| 4 | `37R_struct_kh_binom.R` (`KH=I..IV`) | Knorr-Held space-time interaction models |
| 5 | `37R_discriminate.py`, `37R_discriminate_sens.py` | National composition by sex and age, substitution test (with alternative window pairs) and ill-defined co-movement |
| 6 | `37R_posthoc_reverse.R`, `37R_spatialplus_posthoc2.R` | Post hoc models for associations opposite to the expected direction; Spatial+-type sensitivity analysis |
| 7 | `04_분석/RESP/MS/build/` (`build_refs_resp.py`, `figs_resp.py`, `build_arbr.py`, `esm_resp.py`, `authorship_arbr.py`, `cover_arbr.py`, `strobe_arbr.py`, `check_arbr.py`; `run_all_arbr.sh`) | Manuscript, supplementary material, STROBE checklist, figures and checks (`word_pdf.sh` renders the manuscript PDF with Microsoft Word for page and line numbers) |

The boundary file is found at `data/boundary/final.shp` by default; set `ST_SHP` to use another path.

## Software

R 4.6.0 with R-INLA 25.10.19, spdep and sf; Python 3.9 with pandas, geopandas, numpy, matplotlib and python-docx.

## Licence

MIT (see `LICENSE`).
