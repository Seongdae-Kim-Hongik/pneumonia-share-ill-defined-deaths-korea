#!/bin/bash
# run_all_arbr.sh — RESP ARBR 전체 빌드(2026-11-18). 그림은 figs_resp.py(이미 생성, 필요 시 따로), 참고문헌 캐시 refs_resp.json 그대로(네트워크 없음).
# Zenodo DOI는 <논문폴더>/06_GitHub_Zenodo/zenodo_doi_arbr.txt 한 줄을 읽는다(없으면 PENDING).
set -e; cd "$(dirname "$0")"; O=../out_arbr
python3 -W ignore build_arbr.py
python3 -W ignore esm_resp.py
python3 -W ignore authorship_arbr.py
python3 -W ignore cover_arbr.py
python3 pb_to_br.py $O/Manuscript.docx $O/Supplementary_Material.docx $O/Authorship_File.docx
python3 sanitize_docx.py --no-anon $O/Manuscript.docx $O/Supplementary_Material.docx $O/Authorship_File.docx $O/Cover_Letter.docx
for f in Supplementary_Material Authorship_File Cover_Letter; do /opt/homebrew/bin/soffice --headless -env:UserInstallation=file:///tmp/lo_resp_fin_arbr --convert-to pdf --outdir $O $O/$f.docx >/dev/null 2>&1; done
./word_pdf.sh $O/Manuscript.docx $O/Manuscript.pdf
python3 -W ignore strobe_arbr.py $O/Manuscript.pdf
python3 pb_to_br.py $O/STROBE_Checklist.docx; python3 sanitize_docx.py --no-anon $O/STROBE_Checklist.docx
/opt/homebrew/bin/soffice --headless -env:UserInstallation=file:///tmp/lo_resp_fin_arbr --convert-to pdf --outdir $O $O/STROBE_Checklist.docx >/dev/null 2>&1
python3 -W ignore check_arbr.py
