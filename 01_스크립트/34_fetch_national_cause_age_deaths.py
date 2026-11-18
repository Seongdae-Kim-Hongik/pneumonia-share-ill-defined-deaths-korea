#!/usr/bin/env python3
# 34 — 전국 사인(104항목)×성×연령(5세)별 사망자수·사망률(KOSIS DT_1B34E01, orgId 101)을 연도별로 받는다(2026-11-06, 사망 2차 묶음 선별용).
#  시군구 사망원인(DT_1B34E13)은 사인별 연령 분포가 없어 간접 연령표준화 기대 수를 만들 수 없으므로, 전국 사인×연령 사망률을 따로 받는다.
#  키: ~/.kosis_key(내용 출력 금지). 산출: 00_원천/D_사망_인구_암/DT_1B34E01_national/<연도>.json, DT_1B34E01_national_long.csv
#  사용: python3 34_fetch_national_cause_age_deaths.py [시작연도] [끝연도]   (기본 2011 2024)
import os, sys, json, time, urllib.request, urllib.parse
import pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "00_원천", "D_사망_인구_암", "DT_1B34E01_national"); os.makedirs(OUT, exist_ok=True)
Y0, Y1 = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) > 2 else (2011, 2024)
KEY = open(os.path.expanduser("~/.kosis_key")).read().strip()
URL = "https://kosis.kr/openapi/Param/statisticsParameterData.do?"
rows = []
for y in range(Y0, Y1 + 1):
    f = os.path.join(OUT, f"{y}.json")
    if not os.path.exists(f):
        q = dict(method="getList", apiKey=KEY, itmId="ALL", objL1="ALL", objL2="ALL", objL3="ALL", format="json", jsonVD="Y",
                 prdSe="Y", startPrdDe=str(y), endPrdDe=str(y), orgId="101", tblId="DT_1B34E01")
        d = json.loads(urllib.request.urlopen(URL + urllib.parse.urlencode(q), timeout=300).read().decode("utf-8"))
        if isinstance(d, dict): raise SystemExit(f"[34] {y} 오류 응답: {d}")
        json.dump(d, open(f, "w", encoding="utf-8"), ensure_ascii=False); time.sleep(1)
    d = json.load(open(f, encoding="utf-8"))
    for r in d:
        rows.append(dict(year=int(r["PRD_DE"]), cause_code=r["C1"], cause=r["C1_NM"], sex=r["C2_NM"], age_code=r["C3"], age=r["C3_NM"], item=r["ITM_NM"],
                         value=pd.to_numeric(r["DT"], errors="coerce")))
    print(f"[34] {y}: {len(d):,}행")
L = pd.DataFrame(rows); L.to_csv(os.path.join(ROOT, "00_원천", "D_사망_인구_암", "DT_1B34E01_national_long.csv"), index=False, encoding="utf-8-sig")
chk = L[(L.cause == "계") & (L.sex == "계") & (L.age == "계") & (L.item == "사망자수")].set_index("year").value
print("[34] 전국 총사망(검산용):", chk.astype(int).to_dict())
