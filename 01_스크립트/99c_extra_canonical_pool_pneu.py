#!/usr/bin/env python3
# 99c — 폐렴 사망(PNEU, J12-J18) 가설 풀용 추가 열(2026-11-08). 99c_alz를 복제해 결합 규칙(코드표, 이름 결합 금지, 군위군 37310 별칭)은 그대로 쓴다.
#  ① 정본 통합자료: basic_livelihood_rate(국민기초생활보장 수급자 비율 %, 창원 2021-23 입력 오류 3칸 보간) — 박탈
#                   em_specialists_per100k(응급의학 전문의 ÷ 정본 인구 × 10만) — 중증 폐렴 급성기 진료 접근(STRK와 같은 정의)
#                   factory_land_share(공장용지 면적 비율 %) — 대기오염(산업 배출) 대리(CLRD와 같은 정의; 시군구 PM2.5 연도 자료 없음)
#  ② 요양병원 수(마스터 chk__요양기관_요양병원) ÷ 65세 이상 인구(39m PNEU_Estd2 pop65_share_raw × 패널 인구) × 10만 — 요양시설 거주·흡인·의료관련 폐렴, 사망 장소·진단 축
#  ③ 사망원인 추가 사인(성=계): 폐렴 J12-J18(검산: 패널 cases와 3,206칸 일치 assert), R00-R99 불명확 사인, R54 노쇠, 전체 사망
#       → ill_defined_share = R00-R99 ÷ 전체 사망 × 100 (사망진단 품질 대리, 민감도 전용)
#  산출: 02_패널/EXT_canonical_pool_PNEU_261108.csv, 02_패널/PNEU_mort_extra_261108.csv
import os, sys, unicodedata, importlib.util
import numpy as np, pandas as pd
NFC = lambda s: unicodedata.normalize("NFC", str(s))
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.normpath(os.path.join(HERE, ".."))
ZD = os.environ.get("ST_CANON", os.path.join(os.path.expandvars("$ST_DATA_ROOT"), "기타/R_Studio/FBD_DATA_ZIP/통합자료_261030"))
PAN = os.path.join(ROOT, "02_패널")

# ① 정본
C = pd.read_csv(os.path.join(ZD, "01_공변량_229x2011_2024.csv"), encoding="utf-8-sig", dtype={"sigungu_cd": str})
K = pd.read_csv(os.path.join(ZD, "00_시군구_229_대응표.csv"), encoding="utf-8-sig", dtype={"sigungu_cd": str}); assert K.sigungu_cd.is_unique and len(K) == 229
K.loc[K.sigungu_cd == "37310", "region"] = "대구시군위군"
C = C.drop(columns=["region"]).merge(K[["sigungu_cd", "region"]], on="sigungu_cd", how="left", validate="many_to_one"); assert C.region.notna().all()
out = pd.DataFrame({"year": C.year, "fbd_region": C.region.map(NFC),
                    "em_specialists_per100k": C.emergency_medicine_specialists.astype(float) / C["pop"].astype(float) * 1e5,
                    "factory_land_share": C.factory_land_area.astype(float),
                    "basic_livelihood_rate": C.basic_livelihood_recipient_rate.astype(float)})
out = out[(out.year >= 2011) & (out.year <= 2024)].copy()
out = out.sort_values(["fbd_region", "year"])
ref = out[out.year.isin([2020, 2024])].groupby("fbd_region").basic_livelihood_rate.mean()
bad = out.year.isin([2021, 2022, 2023]) & ((out.basic_livelihood_rate < 0.2 * out.fbd_region.map(ref)) | (out.basic_livelihood_rate > 5 * out.fbd_region.map(ref)))
print("[99c-pneu] 수급률 결함 칸", int(bad.sum()), sorted(out.loc[bad, "fbd_region"].unique()))
assert bad.sum() == 33 and (out.loc[bad, "fbd_region"] == NFC("경상남도창원시")).sum() == 3
out.loc[bad, "basic_livelihood_rate"] = np.nan
out = out.sort_values(["fbd_region", "year"])
out["basic_livelihood_rate"] = out.groupby("fbd_region").basic_livelihood_rate.transform(lambda s: s.interpolate(method="linear", limit_area="inside"))
assert out.groupby("fbd_region").year.nunique().eq(14).all() and out.fbd_region.nunique() == 229 and not out.duplicated(["year", "fbd_region"]).any()

# ② 요양병원 ÷ 65세 이상
MA = pd.read_parquet(os.path.join(PAN, "MASTER_시군구_연도_wide.parquet"), columns=["year", "fbd_region", "population", "chk__요양기관_요양병원", "mort__폐렴_deaths", "mort__전체사망_deaths"])
MA["fbd_region"] = MA.fbd_region.map(NFC); MA = MA[MA.year.between(2011, 2024)]
E2 = pd.read_csv(os.path.join(PAN, "PNEU_Estd2.csv"), encoding="utf-8-sig"); E2["fbd_region"] = E2.fbd_region.map(NFC)
P = pd.read_csv(os.path.join(ROOT, "04_분석", "PNEU", "panel_PNEU.csv"), encoding="utf-8-sig", usecols=["year", "fbd_region", "population", "cases"]); P["fbd_region"] = P.fbd_region.map(NFC)
X = P.merge(E2[["year", "fbd_region", "pop65_share_raw"]], on=["year", "fbd_region"], validate="one_to_one").merge(MA[["year", "fbd_region", "chk__요양기관_요양병원", "mort__폐렴_deaths"]], on=["year", "fbd_region"], how="left", validate="one_to_one")
assert len(X) == 3206 and (X.cases == X["mort__폐렴_deaths"]).all()
X["ltc_hospitals_per100k_65"] = X["chk__요양기관_요양병원"].astype(float) / (X.population * X.pop65_share_raw / 100) * 1e5
print("[99c-pneu] 요양병원/65+ 10만 연도 중앙값", X.groupby("year").ltc_hospitals_per100k_65.median().round(1).to_dict(), "결측", int(X.ltc_hospitals_per100k_65.isna().sum()))
out = out.merge(X[["year", "fbd_region", "ltc_hospitals_per100k_65"]], on=["year", "fbd_region"], how="left", validate="one_to_one")

# ③ 사망원인 추가 사인 → 50.load_source 집계
spec = importlib.util.spec_from_file_location("m50", os.path.join(HERE, "50_build_master_panel.py")); m50 = importlib.util.module_from_spec(spec); spec.loader.exec_module(m50)
L = pd.read_parquet(os.path.join(PAN, "사망원인_시군구_연도_사인_성_long.parquet"), columns=["year", "sido", "sigungu", "sgg_code", "sgg_code_std", "level", "parent_code", "code_note", "cause_code", "sex", "deaths"],
                    filters=[("sex", "==", "계"), ("year", ">=", 2011), ("year", "<=", 2024), ("cause_code", "in", ["0", "A1", "I", "I1"])])
L = L[(L.sex == "계") & L.year.between(2011, 2024) & L.cause_code.isin(["0", "A1", "I", "I1"])]
L["v"] = L.cause_code.map({"0": "전체_deaths", "A1": "PNEU_deaths", "I": "불명확_deaths", "I1": "노쇠_deaths"})
IDX = ["year", "sido", "sigungu", "sgg_code", "sgg_code_std", "level", "parent_code", "code_note"]
for c in IDX[1:]: L[c] = L[c].fillna("").astype(str)
W = L.pivot_table(index=IDX, columns="v", values="deaths", aggfunc="sum").reset_index().replace({"": np.nan})
W = W[W.level.notna()]
tmpf = "_tmp_PNEU_mort_extra_wide.csv"; W.to_csv(os.path.join(PAN, tmpf), index=False, encoding="utf-8-sig")
mk = pd.read_csv(os.path.join(PAN, "시군구_마스터키.csv"), dtype=str); mk = mk[mk.fbd_sido.notna()].drop_duplicates("key")
log = dict(missing_files=[], level_filter={}, unmatched=[], special=[], overlap=[], sources={})
src = dict(name="mortx", prefix="", files=[tmpf], sido="sido", sgg="sigungu", merge_counts=True, level="시군구", ratio=lambda c: False, label="사망원인통계")
agg, meta = m50.load_source(src, set(mk.key), log)
os.remove(os.path.join(PAN, tmpf))
agg = agg.merge(mk[["key", "fbd_region"]], on="key", how="left"); agg["fbd_region"] = agg.fbd_region.map(NFC); agg["year"] = agg.year.astype(int)
M = P[["year", "fbd_region", "cases"]].merge(agg[["year", "fbd_region", "전체_deaths", "PNEU_deaths", "불명확_deaths", "노쇠_deaths"]], on=["year", "fbd_region"], how="left", validate="one_to_one")
assert M[["전체_deaths", "PNEU_deaths"]].notna().all().all(), M[M.PNEU_deaths.isna()].head()
mm = (M.PNEU_deaths != M.cases).sum(); print(f"[99c-pneu] J12-J18 검산: 마스터·패널 cases와 불일치 {mm}칸 / {len(M)}"); assert mm == 0
tot_chk = M.merge(MA[["year", "fbd_region", "mort__전체사망_deaths"]], on=["year", "fbd_region"]); assert (tot_chk["전체_deaths"] == tot_chk["mort__전체사망_deaths"]).all()
for c in ["불명확_deaths", "노쇠_deaths"]: print(f"[99c-pneu] {c} 결측 {int(M[c].isna().sum())}, 14년 합 {int(M[c].sum()):,}"); M[c] = M[c].fillna(0)
M["ill_defined_share"] = M["불명확_deaths"] / M["전체_deaths"] * 100
print("[99c-pneu] 불명확 사인 비율(%) 연도 중앙값", M.groupby("year").ill_defined_share.median().round(2).to_dict())
out = out.merge(M[["year", "fbd_region", "ill_defined_share"]], on=["year", "fbd_region"], how="left", validate="one_to_one")
na = out[out.ltc_hospitals_per100k_65.isna()][["year", "fbd_region"]]; print("[99c-pneu] 요양병원 결측 칸(80과 같은 규칙: 시군구 내 보간 → 시군구 평균)", na.values.tolist())
out = out.sort_values(["fbd_region", "year"]); g = out.groupby("fbd_region").ltc_hospitals_per100k_65
out["ltc_hospitals_per100k_65"] = g.transform(lambda s: s.interpolate(method="linear", limit_area="inside")); out["ltc_hospitals_per100k_65"] = out.ltc_hospitals_per100k_65.fillna(out.groupby("fbd_region").ltc_hospitals_per100k_65.transform("mean"))
assert out.notna().all().all(), out.isna().sum()
fp = os.path.join(PAN, "EXT_canonical_pool_PNEU_261108.csv"); out.to_csv(fp, index=False, encoding="utf-8-sig")
M.to_csv(os.path.join(PAN, "PNEU_mort_extra_261108.csv"), index=False, encoding="utf-8-sig")
print(f"[99c-pneu] 저장 {fp} {out.shape}; 02_패널/PNEU_mort_extra_261108.csv {M.shape}")
