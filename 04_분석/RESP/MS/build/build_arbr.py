# build_arbr.py — RESP 원고(Archivos de Bronconeumología, Elsevier, Original article) 조립(2026-11-18).
#  규정(journal author guidelines): 본문 ≤3,000, 구조 초록 ≤250(Objectives/Methods/Results/Conclusions), 키워드 3-6(세미콜론),
#   그림 ≤6·표 ≤6, 참고문헌 ≤40(위첨자 번호, 저자 6명 + et al., 권 볼드, 끝 쪽 줄임, https://doi.org/), 초록에 인용 금지,
#   본문 파일 1쪽 = 제목 + 초록(저자 정보는 별도 authorship file), 고찰 마지막 문단 = 결론, 세로선·음영 없는 표, 범례는 그림과 별도.
import os, re, json, subprocess
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.shared import Pt
from jkms_engine import JKMS
from british import brit
import content_resp as C
from numbers_resp import HYP, FORCED
HERE = os.path.dirname(os.path.abspath(__file__)); MS = os.path.dirname(HERE); OUT = os.path.join(MS, "out_arbr"); os.makedirs(OUT, exist_ok=True)
PAPER = os.environ.get("ST_PAPER_DIR", MS)
N = C.N; REFS = json.load(open(os.path.join(HERE, "refs_resp.json"), encoding="utf-8"))
DRAFT = os.path.join(MS, "draft", "01_manuscript_arbr.md")
_zf = os.path.join(PAPER, "06_GitHub_Zenodo", "zenodo_doi_arbr.txt"); ZENODO = open(_zf).read().strip() if os.path.exists(_zf) else "10.5281/zenodo.PENDING"
REPO = "pneumonia-share-ill-defined-deaths-korea"; GITHUB = f"https://github.com/Seongdae-Kim-Hongik/{REPO}"
TITLE = C.TITLE; ORCID = "0000-0002-1525-0091"
AFFIL = "Department of Biohealth Convergence Open Sharing System, Hongik University, Seoul, Republic of Korea"
ADDRESS = "Department of Biohealth Convergence Open Sharing System, Hongik University, 94 Wausan-ro, Mapo-gu, Seoul 04066, Republic of Korea"
AI_STATEMENT = "The author used Claude (Anthropic) and ChatGPT (OpenAI) only for translation and English-language editing of the manuscript. The author reviewed and edited all output and takes full responsibility for the content of this publication."
IRB = "The Institutional Review Board of Hongik University approved the study on 4 November 2025 (7002340-202511-HR-012) and its continuing review on 3 November 2026 (7002340-202611-HR-040), and waived informed consent because only published aggregate statistics were used."
FUNDING = "This research did not receive any specific grant from funding agencies in the public, commercial, or not-for-profit sectors."
COI = "The author declares not to have any conflicts of interest that may be considered to influence directly or indirectly the content of the manuscript."
CONTRIB = "SK: conceptualisation, methodology, data curation, formal analysis, software, visualisation, writing of the original draft, and review and editing. SK is the guarantor of the work."
def data_statement(): return f"All source data are publicly available aggregate statistics from Statistics Korea, the Ministry of the Interior and Safety, the National Health Insurance Service, the Health Insurance Review and Assessment Service, the public sports facility register and the Community Health Survey, as cited in the Methods. The analysis code that generates every number, table and figure is openly available at Zenodo (https://doi.org/{ZENODO}) and GitHub ({GITHUB}). The processed district-year analytic data are available from the author on reasonable request."

def read_draft():
    md = open(DRAFT, encoding="utf-8").read(); md = re.sub(r"<!--.*?-->", "", md, flags=re.S); S = {}; cur = None
    for line in md.split("\n"):
        m = re.match(r"^## (.+)$", line)
        if m: cur = m.group(1).strip(); S[cur] = []; continue
        if cur is not None: S[cur].append(line)
    return {k: [p.strip() for p in "\n".join(v).split("\n\n") if p.strip()] for k, v in S.items()}
def pandoc_cites(t): return re.sub(r"\s*\[(@[^\]]+)\]", lambda m: "{{" + ",".join(k.strip().lstrip("@") for k in m.group(1).split(";")) + "}}", t)   # 위첨자: 앞 공백 없음
def all_keys():
    src = open(os.path.join(HERE, "content_resp.py"), encoding="utf-8").read() + open(DRAFT, encoding="utf-8").read()
    src = re.sub(r"<!--.*?-->", "", src, flags=re.S); src = re.sub(r"(?m)^\s*#.*$", "", src)
    return sorted(k for k in {k.strip().lstrip("@") for g in re.findall(r"\[(@[^\]]+)\]", src) for k in g.split(";")} if re.fullmatch(r"(web:)?[a-z][a-z0-9]*", k))
KEYS = all_keys()

def trunc_pages(p):   # 2433-2443 → 2433–43
    m = re.fullmatch(r"(\d+)-(\d+)", p or "")
    if not m: return p
    a, b = m.groups()
    if len(a) == len(b):
        i = 0
        while i < len(a) - 1 and a[i] == b[i]: i += 1
        b = b[i:]
    return f"{a}\u2013{b}"
def ref(k):   # Elsevier ARBR: 저자 6명 + et al., 제목. 학술지 약어 연;<b>권</b>:쪽. https://doi.org/
    r = REFS[k]
    if r["type"] == "web": return f"{r['authors']}. {r['title']}. {r['url']}; {r['year']} [accessed {r['accessed']}]."
    au = r["authors"]; a = (", ".join(au) if len(au) <= 6 else ", ".join(au[:6]) + ", et al") + "."
    t = r["title"].rstrip("."); t = t + ("" if t.endswith(("?", "!")) else ".")
    s = f"{a} {t} {r['journal']} {r['year']}"
    if r.get("vol"): s += f";<b>{r['vol']}</b>"
    if r.get("pages"): s += f":{trunc_pages(r['pages'])}"
    return s + (f". https://doi.org/{r['doi']}" if r.get("doi") else (f". PMID: {r['pmid']}" if r.get("pmid") else "")) + ("" if r.get("doi") else ".")

class TX(JKMS):
    raw = False
    def _emit(self, p, text, sz=12, bold=False, italic=False):
        if not self.raw:
            text = brit(text); text = re.sub(r"(^|[\s(])-(?=\d)", "\\1\u2212", text)
        return super()._emit(p, text, sz, bold, italic)
    def head(self, text, level=1): return super().head(text.upper() if level == 1 else text, level)

LABEL = {"ill_defined_death_share": "Ill-defined cause share, % of deaths", "ltc_hospitals_per_100k_65": "Long-term care hospitals per 100,000 aged 65+", "im_specialists_per_100k": "Internal medicine specialists per 100,000",
         "current_smoking_rate": "Current smoking, %", "tb_suspected_screening": "Suspected tuberculosis on screening, %", "influenza_vaccination_rate": "Influenza vaccination, %",
         "chewing_discomfort_rate_65plus": "Chewing discomfort aged 65+, %", "basic_livelihood_rate": "Basic livelihood recipients, %", "walking_practice_rate": "Walking, %",
         "moderate_pa_rate": "Moderate-or-higher physical activity, %", "public_sports_facilities_per_100k": "Public sports facilities per 100,000",
         "urban_population_share": "Urban population share, %", "physicians_per_1000": "Physicians per 1,000", "sex_ratio": "Sex ratio, men per 100 women", "fiscal_independence": "Fiscal autonomy, %", "pop80_share": "Population aged 80+, %"}
GROUPS = [("Certification practice", HYP[:3]), ("Disease epidemiology", HYP[3:7]), ("Deprivation", HYP[7:8]), ("Physical activity", HYP[8:11])]
def table1():
    T = N["T1"]; cols = ["W1", "W2", "W3", "ALL"]
    rows = [["__H__", "Deaths"], ["  District-years, n"] + [f"{T[c]['n']:,}" for c in cols], ["  Pneumonia deaths, n"] + [f"{T[c]['pneu']:,}" for c in cols], ["  CLRD deaths, n"] + [f"{T[c]['clrd']:,}" for c in cols],
            ["  Pneumonia share, %"] + [f"{T[c]['share']:.1f}" for c in cols],
            ["  District pneumonia share, median (P10-P90), %"] + [f"{T[c]['sh_med']:.1f} ({T[c]['sh_p10']:.1f}-{T[c]['sh_p90']:.1f})" for c in cols]]
    for g, vs in GROUPS + [("Forced controls", FORCED)]:
        rows.append(["__H__", g + ", mean (SD)"])
        for v in vs:
            mx = max(abs(T[c]["cov"][v][0]) for c in cols); dp = 0 if mx >= 100 else (2 if mx < 1 else 1)
            rows.append([f"  {LABEL[v]}"] + [f"{T[c]['cov'][v][0]:,.{dp}f} ({T[c]['cov'][v][1]:,.{dp}f})" for c in cols])
    foot = ("Pneumonia share, pneumonia deaths as a percentage of pneumonia and CLRD deaths. Pneumonia, International Classification of Diseases, 10th revision, J12-J18; "
            "CLRD, chronic lower respiratory disease, J40-J47. Survey characteristics are district age-standardised estimates; filled cells for each characteristic are given in supplementary table S1. P10-P90, 10th-90th percentile; SD, standard deviation.")
    return (f"Table 1. Pneumonia and CLRD deaths, composition and district characteristics by calendar window, {N['n_rows']:,} district-years in {N['n_districts']} districts, South Korea, 2011-2024",
            ["Characteristic", "2011-2015", "2016-2019", "2020-2024", "2011-2024"], rows, foot)
SHORT = {"ill_defined_death_share": "Ill-defined cause share", "ltc_hospitals_per_100k_65": "Long-term care hospitals", "im_specialists_per_100k": "Internal medicine specialists",
         "current_smoking_rate": "Current smoking", "tb_suspected_screening": "Suspected tuberculosis", "influenza_vaccination_rate": "Influenza vaccination", "chewing_discomfort_rate_65plus": "Chewing discomfort",
         "basic_livelihood_rate": "Basic livelihood recipients", "walking_practice_rate": "Walking", "moderate_pa_rate": "Moderate-or-higher physical activity", "public_sports_facilities_per_100k": "Public sports facilities"}
DIRN = {"ill_defined_death_share": "+", "ltc_hospitals_per_100k_65": "+", "im_specialists_per_100k": "−", "current_smoking_rate": "−", "tb_suspected_screening": "−", "influenza_vaccination_rate": "−",
        "chewing_discomfort_rate_65plus": "+", "basic_livelihood_rate": "±", "walking_practice_rate": "−", "moderate_pa_rate": "−", "public_sports_facilities_per_100k": "−"}
def table2():
    rows = []; f = lambda t: f"{t[0]:.2f} ({C.b(t[1])}-{C.b(t[2])})"
    for g, vs in GROUPS:
        rows.append(["__H__", g])
        for v in vs:
            m = N["main"][v]; rows.append([f"  {SHORT[v]} ({DIRN[v]})", f((m["OR"], m["lo"], m["hi"])), f"{100*N['mv'][v]['cred']:.0f}", f(N["kh"]["IV"][v]), f(N["dec"]["wi_" + v]), f(N["dec"]["bw_" + v])])
    foot = (f"Odds ratios per 1 SD for a pneumonia death among pneumonia and CLRD deaths, relative to the expected composition (year-specific national cause-specific rates applied to district age structure); expected direction in parentheses. Principal model: beta-binomial with a Besag-York-Mollié 2 district effect and random-walk and independent year effects (the independent year effect was added after the design memo), "
            f"adjusted for all characteristics shown and five forced controls (n={N['n_rows']:,} district-years). *Share of the {N['n_mv']} random-subset fits containing the characteristic in which the CrI excluded 1; shares with the majority sign are in supplementary table S7a. Bounds that round to 1.00 are given to three decimals. "
            f"†Principal model plus a Knorr-Held type IV space-time interaction, the best-fitting interaction model. ‡District mean (between) and yearly deviation from it (within), fitted together. CLRD, chronic lower respiratory disease; CrI, credible interval; OR, odds ratio; SD, standard deviation.")
    return (f"Table 2. District characteristics and the odds of a pneumonia death among pneumonia and CLRD deaths, {N['n_rows']:,} district-years in {N['n_districts']} districts, South Korea, 2011-2024",
            ["Characteristic", "Principal OR (95% CrI)", "Subsets credible, %*", "Type IV OR (95% CrI)†", "Within OR (95% CrI)‡", "Between OR (95% CrI)‡"], rows, foot)

FIGCAP = {
 1: "National composition of pneumonia and chronic lower respiratory disease (CLRD) deaths, South Korea, 2011-2024. (A) Pneumonia deaths as a share of pneumonia and CLRD deaths, and deaths assigned to ill-defined causes (International Classification of Diseases, 10th revision, R00-R99) as a share of all deaths. (B) Ratio of the 2024 to the 2011 death rate for pneumonia and CLRD by sex and 5-year age group; circles, pneumonia; squares, CLRD; filled symbols, men; open symbols, women; vertical axis on a log scale.",
 2: f"Level and speed of the shift from chronic lower respiratory disease (CLRD) to pneumonia deaths, {N['n_districts']} districts, South Korea, 2011-2024. (A) Residual odds ratio of a pneumonia death among pneumonia and CLRD deaths, the exponentiated Besag-York-Mollié 2 district effect from the principal model, after the offset for the expected composition and district characteristics. (B) District departure from the national shift, the exponentiated district-specific slope per decade from the speed model; solid outlines, faster districts (posterior probability of a positive slope above 0.95); dashed outlines, slower districts (below 0.05). Thick lines, province boundaries; district boundaries as of 2014.",
 3: f"Substitution and certification, {N['sub_n']} districts, South Korea, 2011-2015 to 2020-2024. (A) Change in the log standardised mortality ratio (SMR) for pneumonia against that for chronic lower respiratory disease (CLRD). (B) Change in the share of deaths assigned to ill-defined causes against the change in the standardised log odds of pneumonia vs CLRD (the difference between the changes in log SMR), with the least-squares line. Each point is one district; dotted lines mark no change.",
 4: f"Odds ratios (OR) per 1 standard deviation with 95% credible intervals for district characteristics and the odds of a pneumonia death among pneumonia and chronic lower respiratory disease deaths, {N['n_rows']:,} district-years in {N['n_districts']} districts, South Korea, 2011-2024, from the principal model, the principal model with a Knorr-Held type IV space-time interaction, and the within-district and between-district components. The dotted vertical line marks an OR of 1; the horizontal axis is on a log scale.",
}
def foot_row(J, text, sz=9, ls=15):
    from docx.enum.text import WD_LINE_SPACING
    t = J.doc.tables[-1]; r = t.add_row(); m = r.cells[0].merge(r.cells[-1]); m.text = ""; p = m.paragraphs[0]
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.EXACTLY; p.paragraph_format.line_spacing = Pt(ls); p.paragraph_format.space_before = Pt(4)
    c = J.counting; J.counting = False; J._emit(p, text, sz); J.counting = c
def put_table(J, t, fs=9):
    c = J.counting; J.counting = False; J.table_fit(t[0], t[1], t[2], "", fs_max=fs, title_bold=True); foot_row(J, t[3], 8); J.counting = c

def build():
    D = read_draft(); J = TX(cite="sup")
    J.para(f"<b>{TITLE}</b>")
    J.head("Abstract", 1)
    for p in D["Abstract"]:
        m = re.match(r"^(Objectives|Methods|Results|Conclusions):\s*(.*)$", p, re.S); J.para(f"<b>{m.group(1)}:</b> {m.group(2)}", double=False, after=6)   # 제목 + 초록을 1쪽에
    J.para(f"<b>Keywords:</b> {C.KEYWORDS}", before=6, double=False)
    J.page_break(); J.counting = True
    J.head("Introduction", 1)
    for p in D["Introduction"]: J.para(pandoc_cites(p), indent=True)
    J.head("Methods", 1)
    for x in C.METHODS:
        J.head(x[0], 2)
        for p in x[1:]: J.para(pandoc_cites(p), indent=True)
    J.head("Results", 1)
    for x in C.RESULTS:
        J.head(x[0], 2)
        for p in x[1:]: J.para(pandoc_cites(p), indent=True)
    J.head("Discussion", 1)
    for p in D["Discussion"]:
        if p.startswith("### "): J.head(p[4:].strip(), 2); continue
        J.para(pandoc_cites(p), indent=True)
    J.counting = False
    J.head("Data availability", 1); J.para(data_statement())
    assert sorted(J.cites) == KEYS, (set(J.cites) ^ set(KEYS))
    J.page_break(); J.head("References", 1); J.raw = True; rl = []
    for i, k in enumerate(J.cites, 1): s = f"{i}. " + ref(k); rl.append(s); J.para(s)
    J.raw = False
    J.page_break(); put_table(J, table1(), fs=8)
    J.page_break(); put_table(J, table2())
    J.page_break(); J.head("Figure captions", 1)
    for k in sorted(FIGCAP): J.para(f"<b>Figure {k}.</b> {FIGCAP[k]}")
    return J, rl, D

def docx_bw(path):
    from docx import Document
    t = "\n".join(x.text for x in Document(path).paragraphs)
    return len(t[t.find("\nINTRODUCTION\n"):t.find("\nDATA AVAILABILITY\n")].split())
def fix_orphans(path, heads, max_iter=8):
    from docx import Document
    for _ in range(max_iter):
        pdf = path.replace(".docx", ".pdf")
        subprocess.run(["/opt/homebrew/bin/soffice", "--headless", "-env:UserInstallation=file:///tmp/lo_resp_arbr", "--convert-to", "pdf", "--outdir", os.path.dirname(path), path], check=True, capture_output=True)
        pages = subprocess.run(["pdftotext", "-layout", pdf, "-"], capture_output=True, text=True).stdout.split("\f"); orphan = None
        for pg in pages:
            ls = [re.sub(r"^\d+\s+", "", l.strip()) for l in pg.split("\n") if l.strip()]; ls = [l for l in ls if not re.fullmatch(r"\d+", l)]
            if ls and ls[-1] in heads: orphan = ls[-1]; break
        if orphan is None: return
        d = Document(path)
        for p in d.paragraphs:
            if p.text.strip() == orphan:
                r = OxmlElement("w:r"); br = OxmlElement("w:br"); br.set(qn("w:type"), "page"); r.append(br); p._p.insert(1 if p._p.pPr is not None else 0, r); break
        d.save(path); print("orphan fixed:", orphan)

if __name__ == "__main__":
    p = os.path.join(OUT, "Manuscript.docx"); D = read_draft()
    AB = [re.sub(r"^(Objectives|Methods|Results|Conclusions):\s*", "", x) for x in D["Abstract"]]; aw = sum(len(x.split()) for x in AB) + 4
    J, rl, D = build(); J.doc_title = "Manuscript"; J.save(p); bw = docx_bw(p)
    heads = {x.upper() for x in ("Abstract", "Introduction", "Methods", "Results", "Discussion", "Data availability", "References", "Figure captions")} | {x[0] for x in C.METHODS + C.RESULTS} | {x[4:].strip() for x in D["Discussion"] if x.startswith("### ")}
    fix_orphans(p, heads)
    open(os.path.join(OUT, "wordcount.txt"), "w").write(f"body_words={bw}\nabstract_words={aw}\nrefs={len(KEYS)}\ntables=2\nfigures=4\ntitle_words={len(TITLE.split())}\n")
    print(f"body {bw} | abstract {aw} | refs {len(KEYS)} | title words {len(TITLE.split())}")
