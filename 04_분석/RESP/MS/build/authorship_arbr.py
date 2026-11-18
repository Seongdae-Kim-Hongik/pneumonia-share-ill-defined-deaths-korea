# authorship_arbr.py — ARBR authorship file(2쪽): 1쪽 = 유형·제목·저자·소속·교신 연락처, 2쪽 = 필수 선언(Funding·Conflicts of interest·AI) + 선택(기여·감사) + 윤리·자료.
import os, subprocess
from build_arbr import TX, TITLE, ORCID, AFFIL, ADDRESS, AI_STATEMENT, IRB, FUNDING, COI, CONTRIB, data_statement, OUT
J = TX(cite="sup")
J.para("<b>Article type</b>"); J.para("Original article")
J.para("<b>Title</b>", before=6); J.para(TITLE)
J.para("<b>Author</b>", before=6); J.para(f"Seongdae Kim, PhD (ORCID {ORCID})"); J.para(AFFIL)
J.para("<b>Corresponding author</b>", before=6); J.para(f"Seongdae Kim, PhD, {ADDRESS}. Email: kimsd@hongik.ac.kr")
J.page_break(); J.para("<b>Final declarations</b>")
for h, t in (("Funding of the research", FUNDING), ("Conflicts of interest", COI), ("Use of artificial intelligence tools", AI_STATEMENT),
             ("Contribution of each author", CONTRIB), ("Acknowledgements", "None. Translation and English-language editing assistance is declared under the use of artificial intelligence tools."),
             ("Ethics approval", IRB), ("Data availability", data_statement())):
    J.para(f"<b>{h}.</b> {t}", before=8, double=False)
p = os.path.join(OUT, "Authorship_File.docx"); J.doc_title = "Authorship file"; J.save(p)
subprocess.run(["/opt/homebrew/bin/soffice", "--headless", "-env:UserInstallation=file:///tmp/lo_resp_au_arbr", "--convert-to", "pdf", "--outdir", OUT, p], check=True, capture_output=True)
pg = subprocess.run(["pdfinfo", p.replace(".docx", ".pdf")], capture_output=True, text=True).stdout.split("Pages:")[1].split()[0]
print("authorship pages", pg); assert pg == "2", pg
