# strobe_arbr.py — RESP STROBE 체크리스트(ARBR, 2026-11-18): 항목별 쪽·줄 번호를 Word 렌더 원고 PDF에서 핵심 문구로 자동 산출.
# 실행: python3 -W ignore strobe_arbr.py <Word로 저장한 원고 PDF>  → out_arbr/STROBE_Checklist.docx/.pdf + review/STROBE_쪽번호_대조표_ARBR_261118.md
import os, re, sys, subprocess
from build_arbr import TX, TITLE as DTITLE, foot_row, OUT
HERE = os.path.dirname(os.path.abspath(__file__)); MSD = os.path.dirname(HERE); REV = os.path.join(MSD, "review")
MS_PDF = sys.argv[1]
pages = subprocess.run(["pdftotext", "-layout", MS_PDF, "-"], capture_output=True, text=True, check=True).stdout.split("\f")
LN = []   # (line, page, text)
for pg, p in enumerate(pages, 1):
    for l in p.splitlines():
        m = re.match(r"\s*(\d+)\s+(\S.*)", l)
        if m and (not LN or int(m.group(1)) > LN[-1][0]): LN.append((int(m.group(1)), pg, m.group(2).strip()))
        elif LN and m: print("skip", pg, l[:60])
JOIN = ""; POS = []
for n, pg, t in LN: POS.append(len(JOIN)); JOIN += t + " "
def norm(s): return re.sub(r"\s+", " ", s)
def line_at(ix):
    k = max(i for i, p in enumerate(POS) if p <= ix); return LN[k]
BODY0 = JOIN.find("INTRODUCTION")
def span(a, b, body=True):
    i = JOIN.find(a, BODY0 if body else 0); assert i >= 0, a
    j = JOIN.find(b, i); assert j >= 0, (a, b)
    s, e = line_at(i), line_at(j + len(b) - 1)
    return (s[1], s[0], e[1], e[0])
def fmt(sp):
    p1, a, p2, b = sp
    if p1 == p2: return f"page {p1}, line{'s' if a != b else ''} {a}{'-' + str(b) if a != b else ''}"
    return f"pages {p1}-{p2}, lines {a}-{b}"
H = "__H__"
CK = [
 (H, "Title and abstract"),
 ("", "1a", "Indicate the study's design with a commonly used term in the title or the abstract", [("Pneumonia share of pneumonia", "causes within districts", False), ("In this ecological study", "ecological study", False)], ""),
 ("", "1b", "Provide in the abstract an informative and balanced summary of what was done and what was found", [("ABSTRACT", "disease change from certification.", False)], ""),
 (H, "Introduction"),
 ("Background/rationale", "2", "Explain the scientific background and rationale for the investigation being reported", [("Chronic respiratory diseases, led by", "has not been examined.")], ""),
 ("Objectives", "3", "State specific objectives, including any prespecified hypotheses", [("This study analysed the share", "deprivation and physical activity.")], ""),
 (H, "Methods"),
 ("Study design", "4", "Present key elements of study design early in the paper", [("This ecological study used all", "(STROBE) guideline")], ""),
 ("Setting", "5", "Describe the setting, locations and relevant dates, including periods of recruitment, exposure, follow-up and data collection", [("This ecological study used all", "the 2014 boundaries")], ""),
 ("Participants", "6a", "Give the eligibility criteria, and the sources and methods of selection of participants", [("This ecological study used all", "is the main component.")], ""),
 ("", "6b", "For matched studies, give matching criteria and number of exposed and unexposed", [], "NA, not a matched study"),
 ("Variables", "7", "Clearly define all outcomes, exposures, predictors, potential confounders and effect modifiers", [("The outcome was the share", "is the main component."), ("Eleven characteristics in four groups", "fiscal autonomy and the share aged 80")], "; supplementary table S1"),
 ("Data sources/measurement", "8", "For each variable of interest, give sources of data and details of methods of assessment (measurement)", [("Deaths by underlying cause", "(ICD-10)"), ("Survey items were district", "Community Health Survey")], "; supplementary table S1 and appendix A"),
 ("Bias", "9", "Describe any efforts to address potential sources of bias", [("The logit of the expected pneumonia share", "aged 80 years or older."), ("Robustness checks were", "not interpreted as total effects")], ""),
 ("Study size", "10", "Explain how the study size was arrived at", [("This ecological study used all", "district-years")], " (all districts included)"),
 ("Quantitative variables", "11", "Explain how quantitative variables were handled in the analyses", [("Expected deaths from each cause", "district departures from it."), ("Covariates were standardised", "interpolated (supplementary table S1).")], ""),
 ("Statistical methods", "12a", "Describe all statistical methods, including those used to control for confounding", [("The district-year count of pneumonia", "Laplace approximation in R"), ("If certification had moved", "with post hoc models.")], "; supplementary appendix A"),
 ("", "12b", "Describe any methods used to examine subgroups and interactions", [("A speed model added", "multiplied by time.")], ""),
 ("", "12c", "Explain how missing data were addressed", [("Covariates were standardised", "interpolated (supplementary table S1).")], ""),
 ("", "12d", "If applicable, describe analytical methods taking account of sampling strategy", [("Survey items were district", "Community Health Survey")], " (survey items used as district age-standardised estimates; deaths are complete national registration)"),
 ("", "12e", "Describe any sensitivity analyses", [("Robustness checks were", "eight sensitivity analyses"), ("The window pairs", "sensitivity analyses.")], "; supplementary appendix A"),
 (H, "Results"),
 ("Participants", "13a", "Report numbers of individuals at each stage of study", [("This ecological study used all", "district-years"), ("The districts recorded", "CLRD deaths")], ""),
 ("", "13b", "Give reasons for non-participation at each stage", [], "NA, all 229 districts and all registered deaths were included; no exclusions"),
 ("", "13c", "Consider use of a flow diagram", [], "NA, aggregate district data with no exclusions"),
 ("Descriptive data", "14a", "Give characteristics of study participants and information on exposures and potential confounders", [("The districts recorded", "(table 1)")], "; table 1"),
 ("", "14b", "Indicate number of participants with missing data for each variable of interest", [("Covariates were standardised", "interpolated (supplementary table S1).")], "; supplementary table S1 (filled cells by characteristic)"),
 ("", "14c", "Summarise follow-up time (cohort studies)", [], "NA, not a cohort study; annual district data, 2011-2024"),
 ("Outcome data", "15", "Report numbers of outcome events or summary measures", [("The districts recorded", "in 2021-2024.")], "; table 1; figure 1"),
 ("Main results", "16a", "Give unadjusted estimates and, if applicable, confounder-adjusted estimates and their precision", [("In the principal model, a 1 standard", "opposite to that expected.")], "; table 2; figure 4"),
 ("", "16b", "Report category boundaries when continuous variables were categorised", [], "NA, characteristics were analysed as continuous standardised variables"),
 ("", "16c", "If relevant, consider translating estimates of relative risk into absolute risk", [("In absolute terms, the combined", "85 years or older")], "; supplementary table S2"),
 ("Other analyses", "17", "Report other analyses done, eg, analyses of subgroups and interactions, and sensitivity analyses", [("In the principal model, residual", "(supplementary table S4)"), ("Across 229 districts, no correlation", "changes in pneumonia SMRs"), ("Current smoking was associated", "(supplementary table S8).")], "; supplementary tables S3-S8"),
 (H, "Discussion"),
 ("Key results", "18", "Summarise key results with reference to study objectives", [("In South Korea, the pneumonia share", "after the results were seen.")], ""),
 ("Limitations", "19", "Discuss limitations, taking into account sources of potential bias or imprecision", [("This was an ecological study", "carry sampling error.")], ""),
 ("Interpretation", "20", "Give a cautious overall interpretation of results", [("These absolute rates are compatible", "training of certifying doctors."), ("in South Korea was broad", "disease change from certification.")], ""),
 ("Generalisability", "21", "Discuss the generalisability (external validity) of the study results", [("This was an ecological study", "may not apply to individuals"), ("Only the underlying cause", "as a contributing cause.")], ""),
 (H, "Other information"),
 ("Funding", "22", "Give the source of funding and the role of the funders", [], "Authorship file, page 2 (Funding of the research): no specific grant"),
]
rows = []; rev = ["# RESP STROBE 쪽·줄 번호 대조표 (ARBR, 2026-11-18)", "", f"- 기준 원고 PDF(Microsoft Word 렌더): `{MS_PDF}` ({len(pages) - 1}쪽, 연속 줄 번호 {LN[-1][0]}줄)",
       "- 방법: 항목마다 시작·끝 핵심 문구를 원고 PDF 줄 텍스트에서 찾아 쪽·줄 번호를 자동 산출", "", "| 항목 | 체크리스트 기재 | 시작 줄(원문) |", "|---|---|---|"]
for r in CK:
    if r[0] == H: rows.append([H, r[1], "", ""]); continue
    sec, no, rec, anchors, extra = r
    sps = [span(a[0], a[1], a[2] if len(a) > 2 else True) for a in anchors]
    loc = ("; ".join(fmt(s) for s in sps) + extra) if sps else extra
    rows.append([sec, no, rec, loc])
    first = next((t for n, pg, t in LN if n == sps[0][1]), "")[:70] if sps else "(NA)"
    rev.append(f"| {no} | {loc} | {first} |")
nna = sum(1 for r in CK if r[0] != H and not r[3])
rev += ["", f"- 결과: {len(CK) - sum(1 for r in CK if r[0] == H)}개 항목, 빈칸 0, NA {nna}개(사유 기재), 모든 핵심 문구 발견(assert)"]
os.makedirs(REV, exist_ok=True); open(os.path.join(REV, "STROBE_쪽번호_대조표_ARBR_261118.md"), "w", encoding="utf-8").write("\n".join(rev) + "\n")
K = TX(cite="sup"); K.para("<b>STROBE checklist</b>"); K.para(f"Manuscript entitled \"{DTITLE}\"")
K.table("STROBE checklist for this ecological study, with page and line numbers in the main text file", ["Section/topic", "Item", "Recommendation", "Page and line numbers"], rows, [2.9, 1.0, 5.5, 6.5], "", fs=8.5, title_bold=True)
from docx.enum.text import WD_ALIGN_PARAGRAPH
for _r in K.doc.tables[-1].rows[1:]:
    for _c in _r.cells[2:]:
        for _p in _c.paragraphs: _p.alignment = WD_ALIGN_PARAGRAPH.LEFT
foot_row(K, "Page and line numbers refer to the main text file (page numbers in the footer; continuous line numbers in the left margin). NA, not applicable. STROBE, Strengthening the Reporting of Observational Studies in Epidemiology.", 8, 12)
pk = os.path.join(OUT, "STROBE_Checklist.docx"); K.doc_title = "STROBE checklist"; K.save(pk)
subprocess.run(["/opt/homebrew/bin/soffice", "--headless", "-env:UserInstallation=file:///tmp/lo_resp_st_arbr", "--convert-to", "pdf", "--outdir", OUT, pk], check=True, capture_output=True)
print(rev[-1]); print("saved", os.path.basename(pk))
