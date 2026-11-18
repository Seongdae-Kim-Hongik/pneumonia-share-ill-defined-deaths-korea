# cover_arbr.py — RESP 커버레터(ARBR, 2026-11-18). 1쪽, 단독 저자 비인칭, 김성대 서명. ARBR 요구: 편집장 앞, 제목·섹션, 새로움·의의·근거,
import os, re, subprocess
from docx import Document
from docx.shared import Pt, Cm
import content_resp as C
from build_arbr import TITLE as DTITLE, ZENODO, GITHUB, ADDRESS, OUT
from british import brit
HERE = os.path.dirname(os.path.abspath(__file__)); SIG = os.path.join(HERE, "signature_kim.png")
N = C.N; W = dict(l.split("=") for l in open(os.path.join(OUT, "wordcount.txt")).read().split()); M = N["main"]; sub = N["sub"]
assert M["ill_defined_death_share"]["cred"] and N["mv"]["ill_defined_death_share"]["cred"] == 1.0 and sub["signal_corr_PC"][1] < 0 < sub["signal_corr_PC"][2] and N["pa_all_null"] and N["n_mid_fell"] == 8
DATE = "18 November 2026"
cl = [DATE, "Dr José Luis López-Campos Bodineau", "Editor-in-Chief, Archivos de Bronconeumología", "",
      "Dear Dr López-Campos,",
      f"Please find enclosed the manuscript entitled \"{DTITLE}\" by Seongdae Kim, submitted for publication in Archivos de Bronconeumología in the Original articles section.",
      f"Between 2011 and 2024, the share of pneumonia among deaths from pneumonia and chronic lower respiratory disease (CLRD) in South Korea rose from {N['share_2011']:.0f}% to {N['share_2024']:.0f}%. Using national death registration for all {N['n_districts']} districts and Bayesian spatio-temporal models of cause composition, this study asks whether pneumonia took over deaths that would earlier have been certified as CLRD, mainly chronic obstructive pulmonary disease (COPD). The shift appeared in every age group from 50 years, but in absolute terms falls in CLRD death rates exceeded rises in pneumonia death rates from 65 to 84 years. The speed of the shift was spatially clustered and not explained by measured district characteristics. No district-level exchange between the two causes was detected, and the pneumonia share was consistently associated with the share of deaths certified to ill-defined causes, whose rises accompanied falls in recorded CLRD.",
      "The novelty lies in analysing the composition of respiratory deaths, rather than each cause separately, across every district of a country over 14 years. The relevance for respiratory medicine is that falling registered COPD mortality, a common indicator of progress, should be read with attention to how the underlying cause is selected for older people with chronic lung disease who die with pneumonia; these data cannot separate disease change from certification.",
      "The content of the manuscript is completely original, and the work has not been totally or partially published and is not under consideration for publication in another journal. The author, as sole author, is aware of the manuscript and approves its submission to the journal. The author used Claude (Anthropic) and ChatGPT (OpenAI) only for translation and English-language editing of the manuscript and takes full responsibility for its content. Open Access processing is not requested; the author transfers the copyright of the article to the Spanish Society of Pulmonology and Thoracic Surgery (SEPAR). The study used only published aggregate statistics and was approved by the Institutional Review Board of Hongik University (7002340-202511-HR-012; continuing review 7002340-202611-HR-040).",
      f"The main text contains {int(W['body_words']):,} words, with a structured abstract of {int(W['abstract_words'])} words, two tables, four figures and {W['refs']} references. The authorship file, supplementary material and STROBE checklist are provided as separate files. The analysis code is openly available at Zenodo (https://doi.org/{ZENODO}) and GitHub ({GITHUB}).",
      "Thank you for considering this manuscript.", "", "Yours sincerely,", "[[SIG]]",
      "Seongdae Kim, PhD (corresponding author)", ADDRESS, "Email: kimsd@hongik.ac.kr"]
d = Document(); st = d.styles["Normal"]; st.font.name = "Times New Roman"; st.font.size = Pt(11); st.paragraph_format.space_after = Pt(4); st.paragraph_format.line_spacing = 1.0
for s in d.sections: s.page_width, s.page_height = Cm(21), Cm(29.7); s.left_margin = s.right_margin = s.top_margin = s.bottom_margin = Cm(2.3)
gap = False
for t in cl:
    if t == "": gap = True; continue
    if t == "[[SIG]]": p = d.add_paragraph(); p.add_run().add_picture(SIG, width=Cm(3.2)); continue
    p = d.add_paragraph(brit(t))
    if gap: p.paragraph_format.space_before = Pt(10); gap = False
d.core_properties.author = "Seongdae Kim"; d.core_properties.last_modified_by = "Seongdae Kim"; d.core_properties.title = "Cover Letter"; d.core_properties.comments = ""
fp = os.path.join(OUT, "Cover_Letter.docx"); d.save(fp)
subprocess.run(["/opt/homebrew/bin/soffice", "--headless", "-env:UserInstallation=file:///tmp/lo_resp_cl_arbr", "--convert-to", "pdf", "--outdir", OUT, fp], capture_output=True)
txt = subprocess.run(["pdftotext", fp.replace(".docx", ".pdf"), "-"], capture_output=True, text=True).stdout
assert not re.search(r"\b(we|our|us|I)\b", txt) and "—" not in txt and re.search(r"7002340-202611-?\s*HR-040", txt) and not re.search(r"(?i)funding|competing|overlap|previously submitted|same data", txt), "문체·IRB·금지 항목"
pages = subprocess.run(["pdfinfo", fp.replace(".docx", ".pdf")], capture_output=True, text=True).stdout.split("Pages:")[1].split()[0]
assert pages == "1", pages; print("cover pages", pages)
