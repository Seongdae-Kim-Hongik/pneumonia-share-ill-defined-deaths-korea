# 99b — 정본 통합자료(FBD_DATA_ZIP/통합자료_261030, 229×2011-2024, 180열)의 신규 지표를 체육 시리즈 패널 형식(year, fbd_region)으로 뽑는다(2026-11-06, 대장암부터).
#  결합: 정본 sigungu_cd → 00_시군구_229_대응표.csv(코드표) → region(= 체육 패널 fbd_region). 이름 결합 금지 규칙에 따라 코드표로만 잇고, 229곳 전부 대응·연도 14개를 assert.
#  산출: 02_패널/EXT_canonical_pool_261106.csv
#   alcohol_venues_per10k = 유흥주점 + 단란주점 영업(연말, 인허가) / 1만 명 (정본 lic_*_per10k 합; 분모 = 정본 pop, 창원 2023 교정 1,009,038 반영됨)
#   restaurants_per10k    = 일반음식점 영업 / 1만 명 (2011-2015 공식 연보 대비 0.98-1.05)
#   delivery_per10k       = 배달 위주 업태(넓은 정의) / 1만 명
#   outside_care_share    = 관외 외래 / (관내 + 관외 외래) × 100 (진료 접근성·관외 유출, 민감도용)
import os, sys, unicodedata
import pandas as pd
NFC = lambda s: unicodedata.normalize("NFC", str(s))
ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
ZD = os.environ.get("ST_CANON", os.path.join(os.path.expandvars("$ST_DATA_ROOT"), "기타/R_Studio/FBD_DATA_ZIP/통합자료_261030"))
C = pd.read_csv(os.path.join(ZD, "01_공변량_229x2011_2024.csv"), encoding="utf-8-sig", dtype={"sigungu_cd": str})
K = pd.read_csv(os.path.join(ZD, "00_시군구_229_대응표.csv"), encoding="utf-8-sig", dtype={"sigungu_cd": str})
assert K.sigungu_cd.is_unique and len(K) == 229
ALIAS = {"37310": "대구시군위군"}   # 코드 별칭표: 군위군 2023 대구 편입, 대응표 "경상북도군위군" ↔ 체육 패널 "대구시군위군"(같은 코드 37310)
for _c, _r in ALIAS.items(): K.loc[K.sigungu_cd == _c, "region"] = _r
C = C.drop(columns=["region"]).merge(K[["sigungu_cd", "region"]], on="sigungu_cd", how="left", validate="many_to_one"); assert C.region.notna().all()
out = pd.DataFrame({"year": C.year, "fbd_region": C.region.map(NFC),
    "alcohol_venues_per10k": C.lic_entertainment_bars_per10k + C.lic_singing_bars_per10k,
    "restaurants_per10k": C.lic_general_restaurant_per10k,
    "delivery_per10k": C.delivery_broad_per10k,
    "outside_care_share": 100 * C.out_of_district_outpatient_volume / (C.in_district_outpatient_volume + C.out_of_district_outpatient_volume)})
out = out[(out.year >= 2011) & (out.year <= 2024)]
assert out.groupby("fbd_region").year.nunique().eq(14).all() and out.fbd_region.nunique() == 229 and not out.duplicated(["year", "fbd_region"]).any()
REF = sys.argv[1] if len(sys.argv) > 1 else "HCC"   # 지역 집합 대조용 기준 패널 TAG(이미 만든 std3 패널)
P = pd.read_csv(os.path.join(ROOT, "04_분석", REF, f"panel_{REF}_std3.csv"), encoding="utf-8-sig", usecols=["year", "fbd_region"]); P["fbd_region"] = P.fbd_region.map(NFC)
assert set(P.fbd_region) == set(out.fbd_region), "체육 패널 지역과 불일치"
fp = os.path.join(ROOT, "02_패널", "EXT_canonical_pool_261106.csv"); out.to_csv(fp, index=False, encoding="utf-8-sig")
print(f"[99b] 저장 {fp} {out.shape}"); print(out.describe().T.round(2).to_string()); print("결측", out.isna().sum().to_dict())
