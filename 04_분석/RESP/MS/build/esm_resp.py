# esm_resp.py — RESP 보충자료(ARBR, 2026-11-18, 단일 파일: Appendix A·Table S1-S8·Appendix B STROBE). 수치는 결과 CSV에서만.
import os, re, math, subprocess, pandas as pd
import content_resp as C
from numbers_resp import HYP, FORCED
from build_arbr import LABEL, SHORT, DIRN, GROUPS, TX, TITLE as DTITLE, foot_row, read_draft
HERE = os.path.dirname(os.path.abspath(__file__)); MSD = os.path.dirname(HERE); OUT = os.path.join(MSD, "out_arbr"); B = os.path.dirname(MSD)
N = C.N; f = lambda t: f"{t[0]:.2f} ({C.b(t[1])}-{C.b(t[2])})"
J = TX(cite="sup")
def TF(title, header, rows, foot="", fs=8):
    J.page_break(); J.table_fit(title, header, rows, "", fs_max=fs, title_bold=True)
    if foot: foot_row(J, foot, 8, 12)
J.para("<b>Supplementary material</b>"); J.para(f"Supplementary material for the manuscript entitled \"{DTITLE}\"")
J.para("Contents. Appendix A (supplementary methods); Tables S1-S8; Appendix B (STROBE checklist).")
_MT = pd.read_csv(os.path.join(B, "panel_META_RESP_std3.csv"), encoding="utf-8-sig").set_index("variable")
_imp = lambda v: int(_MT.loc[v, "n_imputed_interp"] + _MT.loc[v, "n_imputed_sgg_mean"] + _MT.loc[v, "n_imputed_year_mean"])
gate = open(os.path.join(B, "data_gate_RESP_std3_261112.txt"), encoding="utf-8").read(); z_ltc = re.search(r"\[전 연도 0인 지역\] ltc_hospitals_per_100k_65_raw: (\d+)곳", gate).group(1)
vif = _MT.vif_final.dropna(); vmax = vif.max(); vname = SHORT.get(vif.idxmax(), LABEL.get(vif.idxmax(), vif.idxmax()))
J.page_break(); J.head("Appendix A. Supplementary methods", 2)
SM = [("Outcome.", f"Deaths with pneumonia (International Classification of Diseases, 10th revision, J12-J18) or chronic lower respiratory disease (CLRD, J40-J47) as the underlying cause, by district of residence and year, came from the cause-of-death statistics of Statistics Korea. Districts followed the 229 units of the 2014 boundary file used for the adjacency graph. District-years with no pneumonia or CLRD death (n={N['n_pc_zero']}) would carry no information in the binomial likelihood; {N['n_pc_lt5']} district-years had fewer than five such deaths. The district totals matched the national totals by year within 1 percentage point of composition."),
      ("Expected composition.", f"Year-specific expected pneumonia and CLRD deaths were computed for each district-year by applying the national cause-specific death rates of that year in eighteen 5-year age groups (0-4 to 80-84 years and 85 years or older) to the district population by age, and were rescaled so that their national sum equalled the observed deaths. The logit of the expected pneumonia share (expected pneumonia deaths over expected pneumonia and CLRD deaths) entered as the offset. Within any year, the expected share ranged by at most {N['p0_within_year_range']:.3f} across districts, so the offset mainly carried the national cause composition of each year, adjusted for district age structure; a sensitivity analysis omitted it. The 2023 age-specific populations of Changwon, which repeated the 2022 values in the source file, were replaced with the official 2023 values (total 1,009,038)."),
      ("Covariates.", f"The ill-defined cause share is deaths with an underlying cause in R00-R99 divided by all deaths in the district-year; the senility share (R54) was used in a sensitivity analysis. Long-term care hospitals per 100,000 people aged 65 years or older came from care institution statistics; {z_ltc} districts had none in any year (true zeros). Internal medicine specialists per 100,000 and the basic livelihood recipient share came from a harmonised public district panel; basic livelihood values below 20% or above five times the adjacent-year values in 33 district-years (11 cities, 2021-2023) were set to missing and interpolated. Current smoking, influenza vaccination in the past year, walking, moderate-or-higher physical activity and chewing discomfort (adults aged 65 years or older) were district age-standardised estimates from the Community Health Survey. Suspected pulmonary tuberculosis is the share of general health screening attendees with suspected tuberculosis on chest radiography. Public sports facilities came from the national register. Final variance inflation factors were below {vmax:.1f} (largest, {vname})."),
      ("Models.", "Software: R 4.6.0 with R-INLA; Python 3.9 for data preparation and figures. Fixed effects had normal priors with mean 0 and precision 4 (intercept precision 0.001). The Besag-York-Mollié 2 district effect used penalised-complexity priors (P(σ>0.5)=0.01; P(φ<0.5)=2/3) on a 593-edge adjacency graph; random-walk and independent year effects used P(σ>0.5)=0.01. The speed model added f(district, time) with a second BYM2 structure on the slope (time centred at 2017.5 and scaled per decade) to the model with forced controls; the speed-determinant model added each characteristic's 2011-2013 mean, standardised, multiplied by time. Knorr-Held interactions were type I (independent), II (random walk in time by independent districts), III (independent years by intrinsic conditional autoregressive districts) and IV (random walk by intrinsic conditional autoregressive districts). Multiverse subsets were drawn with a fixed seed, each characteristic entering with probability 0.5; the forced controls were in every fit, and subset fits used empirical Bayes integration over hyperparameters, checked against the full-set fit. Between- and within-district components were the district mean and the deviation from it, fitted together."),
      ("Substitution analysis.", "For each district, pneumonia and CLRD deaths and expected deaths were summed over 2011-2015 and 2020-2024, and the change in log standardised mortality ratio (SMR) was computed for each cause. The Poisson sampling variance of each change (1/O1 + 1/O2) was averaged over districts and subtracted from the observed variance, and the covariance was taken as observed because sampling errors of the two causes are independent; the ratio gives the correlation of the true changes. Intervals are 2.5th and 97.5th percentiles over 2,000 bootstrap samples of districts (seed 37). The change in composition is the difference of the two changes. National death rates by sex and 5-year age group came from the national cause-of-death table for 2011 and 2024.")]
SM.append(("Departures from the design memo.", "The memo specified a random-walk year effect; an independent year effect was added to absorb year-specific shocks. The memo described the speed model as the principal model plus district slopes; it was fitted with the forced controls only (reported) and with all characteristics (slopes correlated 0.96). The speed-determinant model also contained the district slopes. Knorr-Held type IV was listed as optional and was fitted. The memo's interpretation of the sex-age gradient (a shift confined to the oldest ages suggests reassignment among deaths with multimorbidity; a large shift in middle-aged men suggests smoking cohorts) was checked with the absolute rate changes (table S2): the share rose in middle-aged men, but the combined rate fell from 65 to 84 years and rose at 85 years or older and in four groups aged 50-64 years, so neither interpretation applied alone. The substitution sensitivity analyses with other window pairs and the post hoc models were added after the principal results were seen."))
SM.append(("Sensitivity analyses.", "Eight sensitivity analyses each changed one element of the principal model: all respiratory deaths (J00-J98) as the denominator; CLRD among all respiratory deaths as the outcome; characteristics lagged by 1 year; exclusion of 2020-2022; addition of the senility share (R54); addition of the out-of-district outpatient share; omission of the expected-composition offset; and a queen-contiguity graph with 577 edges. The Spatial+-type check replaced each standardised characteristic by its residual from a district-level regression on the 23 lowest-frequency eigenvectors of the Laplacian of the 593-edge graph, restandardised, so its odds ratios refer to the spatially residualised characteristic."))
SM.append(("Interpretation of the substitution analysis.", "Because standardised mortality ratios use national rates of the same year, any change common to all districts, including a uniform change in certification, is absorbed into the expectation and cannot appear as a correlation between districts. Sampling errors of the two causes were treated as independent, and districts were resampled independently despite spatial clustering, so intervals may be too narrow."))
for h, t in SM: J.para(f"<b>{h}</b> {t}")
# ── Table S1 ──
SRC = {"ill_defined_death_share": "Cause-of-death statistics", "ltc_hospitals_per_100k_65": "Care institution statistics", "im_specialists_per_100k": "District panel", "current_smoking_rate": "Community Health Survey",
       "tb_suspected_screening": "Health screening", "influenza_vaccination_rate": "Community Health Survey", "chewing_discomfort_rate_65plus": "Community Health Survey", "basic_livelihood_rate": "District panel",
       "walking_practice_rate": "Community Health Survey", "moderate_pa_rate": "Community Health Survey", "public_sports_facilities_per_100k": "Sports facility register",
       "urban_population_share": "KOSIS local indicators", "physicians_per_1000": "KOSIS local indicators", "sex_ratio": "KOSIS local indicators", "fiscal_independence": "KOSIS local indicators", "pop80_share": "Resident registration"}
rows = []
for g, vs in GROUPS + [("Forced controls", FORCED)]:
    rows.append(["__H__", g])
    for v in vs:
        m = _MT.loc[v]; rows.append([f"  {LABEL[v]}", SRC[v], f"{int(m.obs_year_min)}-{int(m.obs_year_max)}", ("Forced" if m.role == "forced" else DIRN[v]), (f"{_imp(v):,} (+33 replaced)" if v == "basic_livelihood_rate" else f"{_imp(v):,}")])
TF("Table S1 Source, observed years, expected direction and filled cells for each district characteristic, South Korea, 2011-2024", ["Characteristic", "Source", "Years", "Direction", "Filled cells"], rows,
   "Direction, expected direction of the association with the pneumonia share among pneumonia and CLRD deaths; ±, either direction; forced, in every model. Filled cells of 3,206 district-years (interpolation, district means or yearly means) after construction of each indicator; for basic livelihood recipients, 33 implausible values (below 20% or above five times the adjacent-year values, 11 cities, 2021-2023) were set to missing and interpolated within districts before this step. KOSIS, Korean Statistical Information Service.")
# ── Table S2 ──
A = N["AS"].copy(); AGL = {"50 - 54세": "50-54", "55 - 59세": "55-59", "60 - 64세": "60-64", "65 - 69세": "65-69", "70 - 74세": "70-74", "75 - 79세": "75-79", "80 - 84세": "80-84", "85 - 89세": "85-89", "90세이상": "90+"}
rows = []
for sx, lab in (("남자", "Men"), ("여자", "Women")):
    rows.append(["__H__", lab])
    for _, r in A[A.sex == sx].iterrows():
        rows.append([f"  {AGL[r.age]}", f"{r.P_share_2011:.1f}", f"{r.P_share_2024:.1f}", f"{r.pneu_rate_ratio:.2f}", f"{r.clrd_rate_ratio:.2f}", f"{r.dPr:+.1f}", f"{r.dCr:+.1f}", f"{r.dSum:+.1f}"])
TF("Table S2 Pneumonia share and change in pneumonia and CLRD death rates by sex and age group, South Korea, 2011 and 2024", ["Age group, years", "Pneumonia share 2011, %", "Pneumonia share 2024, %", "Pneumonia rate ratio", "CLRD rate ratio", "Pneumonia rate change", "CLRD rate change", "Combined rate change"], rows,
   "Pneumonia share, pneumonia deaths as a percentage of pneumonia and CLRD deaths. Rate ratio, death rate in 2024 divided by that in 2011; rate change, 2024 minus 2011, per 100,000. Rates are published to one decimal place, so ratios in the youngest groups, where rates are low, are imprecise. Source, national cause-of-death statistics by sex and 5-year age group. CLRD, chronic lower respiratory disease.", fs=7.5)
# ── Table S3 ──
ROM = {"32060": "Sokcho-si, Gangwon", "36460": "Wando-gun, Jeonnam", "36040": "Naju-si, Jeonnam", "32390": "Inje-gun, Gangwon", "32310": "Hongcheon-gun, Gangwon", "32400": "Goseong-gun, Gangwon", "24020": "Seo-gu, Gwangju",
       "32380": "Yanggu-gun, Gangwon", "32320": "Hoengseong-gun, Gangwon", "36390": "Gangjin-gun, Jeonnam", "37410": "Bonghwa-gun, Gyeongbuk", "36310": "Damyang-gun, Jeonnam", "32030": "Gangneung-si, Gangwon",
       "24050": "Gwangsan-gu, Gwangju", "25040": "Yuseong-gu, Daejeon",
       "21310": "Gijang-gun, Busan", "21100": "Saha-gu, Busan", "21030": "Dong-gu, Busan", "21110": "Geumjeong-gu, Busan", "31250": "Gwangju-si, Gyeonggi", "21090": "Haeundae-gu, Busan", "11240": "Songpa-gu, Seoul",
       "11040": "Seongdong-gu, Seoul", "11070": "Jungnang-gu, Seoul", "21080": "Buk-gu, Busan", "26010": "Jung-gu, Ulsan", "21020": "Seo-gu, Busan", "26310": "Ulju-gun, Ulsan", "33370": "Eumseong-gun, Chungbuk",
       "31120": "Guri-si, Gyeonggi", "11050": "Gwangjin-gu, Seoul", "26040": "Buk-gu, Ulsan", "21050": "Busanjin-gu, Busan", "37050": "Gumi-si, Gyeongbuk", "34040": "Asan-si, Chungnam", "11150": "Yangcheon-gu, Seoul",
       "21150": "Sasang-gu, Busan", "11110": "Nowon-gu, Seoul", "11230": "Gangnam-gu, Seoul", "38110": "Changwon-si, Gyeongnam"}
S = N["speed"]; rows = []
for lab, q in (("Faster", S[S.P_gt0 > 0.95].sort_values("delta", ascending=False)), ("Slower", S[S.P_gt0 < 0.05].sort_values("delta"))):
    rows.append(["__H__", f"{lab} districts (n={len(q)})"])
    for _, r in q.iterrows(): assert r.cd in ROM, r.fbd_region; rows.append([f"  {ROM[r.cd]}", f"{math.exp(r.delta):.2f}", f"{C.b(math.exp(r.lo))}-{C.b(math.exp(r.hi))}", f"{r.P_gt0:.3f}"])
TF("Table S3 Districts where the shift from CLRD to pneumonia deaths was faster or slower than the national shift, South Korea, 2011-2024", ["District, province", "OR per decade", "95% CrI", "Posterior probability of a positive slope"], rows,
   f"Speed model: beta-binomial with the age offset, forced controls, a Besag-York-Mollié 2 district effect, year effects and a district-specific slope with its own Besag-York-Mollié 2 structure. OR per decade, exponentiated district slope relative to the national shift. Faster, one-sided posterior probability of a positive slope above 0.95; slower, below 0.05; the two-sided 95% CrI may include 1. Mean slope on the logit scale by district type: urban wards {N['delta_by_type']['ward']:.2f}, cities {N['delta_by_type']['city']:.2f}, counties {N['delta_by_type']['county']:.2f}. CLRD, chronic lower respiratory disease; CrI, credible interval; OR, odds ratio.")
# ── Table S4 ──
rows = []
for g, vs in GROUPS:
    rows.append(["__H__", g])
    for v in vs: t = N["m3"]["bx_" + v]; rows.append([f"  {SHORT[v]}", f(t), f"{t[4]:.3f}"])
TF("Table S4 Baseline district characteristics and the speed of the shift from CLRD to pneumonia deaths, South Korea, 2011-2024", ["Baseline characteristic (2011-2013)", "OR per SD per decade (95% CrI)", "Posterior probability OR>1"], rows,
   f"Speed-determinant model: the principal model plus a district-specific slope and each characteristic's standardised 2011-2013 mean multiplied by time (per decade). WAIC {N['waic_m3']:,.1f}. CLRD, chronic lower respiratory disease; CrI, credible interval; OR, odds ratio; SD, standard deviation; WAIC, widely applicable information criterion.")
# ── Table S5 ──
SN = {"SN1_pneu_of_all_resp": "Denominator all respiratory deaths (J00-J98)", "SN2_clrd_of_all_resp": "Outcome CLRD among all respiratory deaths", "SN3_lag1": "Characteristics lagged 1 year", "SN4_excl_2020_22": "Excluding 2020-2022",
      "SN5_plus_senility": "Adding senility (R54) share", "SN6_plus_outside_care": "Adding out-of-district outpatient share", "SN7_no_age_offset": "Without the expected-composition offset", "SN8_graph577": "Queen-contiguity graph (577 edges)"}
assert list(SN) == N["sens_models"]
KV = ["ill_defined_death_share", "current_smoking_rate", "basic_livelihood_rate", "ltc_hospitals_per_100k_65"]
rows = [["Principal model"] + [f((N["main"][v]["OR"], N["main"][v]["lo"], N["main"][v]["hi"])) for v in KV]] + [[SN[m]] + [f(N["sens"][(m, v)]) for v in KV] for m in SN] + [["Spatial+-type adjustment"] + [f(N["splus"][v]) for v in KV]]
TF("Table S5 Odds ratios per 1 SD in sensitivity analyses for selected characteristics, South Korea, 2011-2024", ["Analysis"] + [SHORT[v] for v in KV], rows,
   "Each analysis changes one element of the principal model; all other characteristics and forced controls are included. With CLRD among all respiratory deaths as the outcome, odds ratios below 1 indicate a lower CLRD share of all respiratory deaths. Bounds that round to 1.00 are given to three decimals. With the senility share added, its own odds ratio was " + C.ci(N["sens"][("SN5_plus_senility", "senility_share")]) + ". Estimates for the other characteristics are available from the author. CLRD, chronic lower respiratory disease; SD, standard deviation.", fs=7.5)
# ── Table S6 ──
PH = [("P1_smoking_alone", "current_smoking_rate", "Current smoking with forced controls only"), ("P4_main_minus_smoking", None, "Principal model without current smoking"),
      ("P2_lca_replaces_smoking", "lca_logsir", "Lung cancer treatment (log SMR) replacing current smoking"), ("P5_smoking_plus_lca", "current_smoking_rate", "Current smoking with lung cancer treatment, smoking"),
      ("P5_smoking_plus_lca", "lca_logsir", "Current smoking with lung cancer treatment, lung cancer"), ("P3_ltc_alone", "ltc_hospitals_per_100k_65", "Long-term care hospitals with forced controls only"),
      ("P6_chewing_alone", "chewing_discomfort_rate_65plus", "Chewing discomfort with forced controls only")]
rows = []
for sp, v, lab in PH:
    if v is None: t = N["ph"][(sp, "ill_defined_death_share")]; rows.append([lab + ", ill-defined cause share", f(t)]); continue
    rows.append([lab, f(N["ph"][(sp, v)])])
TF("Table S6 Post hoc models for associations opposite to the expected direction, South Korea, 2011-2024", ["Model", "OR per SD (95% CrI)"], rows,
   "Fitted after the principal results were seen. Lung cancer treatment is the district log standardised ratio of people treated for lung cancer, as a proxy for cumulative smoking exposure; its correlation with current smoking was close to 0. CrI, credible interval; OR, odds ratio; SD, standard deviation.")
# ── Table S7 (두 부분: 가로 폭) ──
for part, cols, hdr in (("a", [("kh", k) for k in ("I", "II", "III")] + [("mv", None)], ["Type I", "Type II", "Type III", "Subsets, %*"]),
                        ("b", [("win", w) for w in ("W1", "W2", "W3")], ["2011-2015", "2016-2019", "2020-2024"])):
    rows = []
    for g, vs in GROUPS:
        rows.append(["__H__", g])
        for v in vs:
            r = [f"  {SHORT[v]}"]
            for kind, k in cols:
                if kind == "kh": r.append(f(N["kh"][k][v]))
                elif kind == "win": r.append(f(N["win"][(k, v)]))
                else: r.append(f"{100*N['mv'][v]['cred']:.0f}/{100*max(N['mv'][v]['gt1'], 1-N['mv'][v]['gt1']):.0f}")
            rows.append(r)
    foot = (f"Type IV is in table 2. WAIC: principal {N['waic_m1']:,.1f}; type I {N['kh_waic']['I']:,.1f}; type II {N['kh_waic']['II']:,.1f}; type III {N['kh_waic']['III']:,.1f}; type IV {N['kh_waic']['IV']:,.1f}. "
            f"*Share of the {N['n_mv']} random-subset fits containing the characteristic in which the credible interval excluded 1 / share with the majority sign. SD, standard deviation; WAIC, widely applicable information criterion.") if part == "a" else \
           "Principal model refitted separately in each calendar window, with characteristics standardised over the full period. SD, standard deviation."
    TF(f"Table S7{part} Odds ratios per 1 SD (95% CrI) " + ("in Knorr-Held models and the multiverse" if part == "a" else "by calendar window") + ", South Korea, 2011-2024", ["Characteristic"] + hdr, rows, foot, fs=7.5)
# ── Table S8 ──
NCL = {"hit_and_run_rate": "Hit-and-run crashes", "traffic_culture_index": "Traffic culture index", "fires_per_10000": "Fires per 10,000"}
rows = [["__H__", "Forced controls in the principal model"]] + [[f"  {LABEL[v]}", f((N['main'][v]['OR'], N['main'][v]['lo'], N['main'][v]['hi']))] for v in FORCED]
rows += [["__H__", "Negative control exposures added one at a time"]] + [[f"  {NCL[v]}", f(N["nc"][v])] for v in NCL]
SET = {"S1_narrative_full": "All eleven characteristics", "S2_certification": "Certification practice only", "S3_epidemiology": "Disease epidemiology only", "S4_activity": "Physical activity only"}
rows += [["__H__", "WAIC by characteristic group (with forced controls)"], ["  Forced controls only", f"{N['waic_forced']:,.1f}"]] + [[f"  {SET[k]}", f"{N['set_waic'][k]:,.1f}"] for k in SET]
rows += [["  Binomial likelihood, forced controls only", f"{N['waic_binom']:,.1f}"], ["  Speed model (forced controls and district slopes)", f"{N['waic_m2a']:,.1f}"]]
TF("Table S8 Forced controls, negative control exposures and model comparison, South Korea, 2011-2024", ["Term or model", "OR per SD (95% CrI) or WAIC"], rows,
   "Lower WAIC indicates better expected predictive fit. CrI, credible interval; OR, odds ratio; SD, standard deviation; WAIC, widely applicable information criterion.")
# ── STROBE ──
DS = [x[4:].strip() for x in read_draft()["Discussion"] if x.startswith("### ")]; MH = [x[0] for x in C.METHODS]; RH = [x[0] for x in C.RESULTS]
CK = [("Title and abstract", "1", "Title; Abstract"), ("Background/rationale", "2", "Introduction"), ("Objectives", "3", "Introduction, final paragraph"), ("Study design", "4", f"Methods, {MH[0]}"), ("Setting", "5", f"Methods, {MH[0]}"),
      ("Participants", "6", f"Methods, {MH[0]} (district populations; ecological)"), ("Variables", "7", f"Methods, {MH[1]}; {MH[2]}; table S1"), ("Data sources/measurement", "8", "Methods; appendix A; table S1"),
      ("Bias", "9", f"Methods, {MH[3]}; {MH[4]}"), ("Study size", "10", f"Methods, {MH[0]} (all 229 districts)"), ("Quantitative variables", "11", f"Methods, {MH[2]}"),
      ("Statistical methods", "12", f"Methods, {MH[3]}; {MH[4]}; appendix A"), ("Participants (flow)", "13", "Not applicable (aggregate district data; no exclusions)"), ("Descriptive data", "14", f"Results, {RH[0]}; table 1"), ("Outcome data", "15", f"Results, {RH[0]}; table 1; figure 1"),
      ("Main results", "16", f"Results, {RH[1]}; {RH[2]}; {RH[3]}; table 2; figures 2-4"), ("Other analyses", "17", "Results; tables S3-S8"),
      ("Key results", "18", "Discussion, first paragraph"), ("Limitations", "19", "Discussion, Limitations"), ("Interpretation", "20", "Discussion"), ("Generalisability", "21", "Discussion, Limitations"), ("Funding", "22", "Authorship file, Funding")]
assert "Limitations" in DS
J.page_break()
J.table_fit("Appendix B STROBE checklist for this ecological study", ["Item", "No.", "Where reported"], [[a, b, c] for a, b, c in CK], "", fs_max=8, title_bold=True)
foot_row(J, "STROBE, Strengthening the Reporting of Observational Studies in Epidemiology.", 8, 12)
ps = os.path.join(OUT, "Supplementary_Material.docx"); J.doc_title = "Supplementary material"; J.save(ps)
subprocess.run(["/opt/homebrew/bin/soffice", "--headless", "-env:UserInstallation=file:///tmp/lo_resp_esm_arbr", "--convert-to", "pdf", "--outdir", OUT, ps], check=True, capture_output=True)
print("saved", os.path.basename(ps))
