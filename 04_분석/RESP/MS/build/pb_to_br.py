# pb_to_br.py — pageBreakBefore(문단 속성)를 문단 첫머리의 명시적 쪽 나눔(w:br type=page)으로 바꾼다. sanitize_docx.py가 pageBreakBefore를 지우기 때문(Word 검은 네모 방지)에 그 전에 돌린다.
import sys, re, zipfile, shutil
for path in sys.argv[1:]:
    z = zipfile.ZipFile(path); tmp = path + ".tmp"; o = zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED); n = 0
    for it in z.infolist():
        b = z.read(it.filename)
        if it.filename == "word/document.xml":
            s = b.decode("utf-8")
            def fix(m):
                global n; p = m.group(0)
                if not re.search(r"<w:pageBreakBefore(?:\s+w:val=\"(?:1|true|on)\")?\s*/>", p): return p
                n += 1; p = re.sub(r"<w:pageBreakBefore[^>]*/>", "", p)
                return re.sub(r"(</w:pPr>)", r'\1<w:r><w:br w:type="page"/></w:r>', p, count=1) if "</w:pPr>" in p else re.sub(r"(<w:p\b[^>]*>)", r'\1<w:r><w:br w:type="page"/></w:r>', p, count=1)
            s = re.sub(r"<w:p\b[^>]*>.*?</w:p>", fix, s, flags=re.S); b = s.encode("utf-8")
        o.writestr(it, b)
    o.close(); z.close(); shutil.move(tmp, path); print(path.split("/")[-1], "page breaks →", n)
