#!/bin/bash
# word_pdf.sh <docx> <out.pdf> — Microsoft Word로 PDF 저장(Word 샌드박스 컨테이너 경로 경유). 투고 포털 변환과 같은 Word 배치 기준.
set -e; W="$HOME/Library/Containers/com.microsoft.Word/Data/Documents/arbr"; mkdir -p "$W"; rm -f "$W/W.pdf"; cp "$1" "$W/W.docx"
osascript <<E >/dev/null 2>&1 || true
with timeout of 240 seconds
tell application "Microsoft Word"
  open POSIX file "$W/W.docx"
  delay 4
  save as document "W.docx" file name "$W/W.pdf" file format format PDF
  close every document saving no
end tell
end timeout
E
test -s "$W/W.pdf"; cp "$W/W.pdf" "$2"; echo "word pdf → $2"
