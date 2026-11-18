#!/usr/bin/env python3
# 99c — 호흡기 사망 사인 구성(RESP: 폐렴 ÷ (폐렴 + 만성하기도질환)) 가설 풀 추가 열(2026-11-12). 99c_lipt(수급률 양쪽 규칙)·99c_pneu(사망 추가 사인)를 복제, 출력 파일만 분리.
#  정본 통합자료(통합자료_261030): basic_livelihood_rate(양쪽 규칙 33칸 → 시군구 안 보간), im_specialists_per100k(내과 전문의 ÷ 정본 인구 × 10만)
#  산출 재사용(같은 정의, 읽기만): ltc_hospitals_per100k_65 ← EXT_canonical_pool_PNEU_261108.csv
#                                       ill_defined_share(R00-R99 ÷ 전체 사망 %), senility_share(R54 ÷ 전체 사망 %) ← PNEU_mort_extra_261108.csv
#  분자 검산: 기준 SQLite region_year의 mort__폐렴·만성하기도질환·호흡기질환·전체사망 = master table(3,206칸) assert
#  산출: 02_패널/EXT_canonical_pool_RESP_261112.csv
import os, sqlite3, unicodedata
import numpy as np, pandas as pd
NFC = lambda s: unicodedata.normalize("NFC", str(s))
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.normpath(os.path.join(HERE, ".."))
ZD = os.environ.get("ST_CANON", os.path.join(os.path.expandvars("$ST_DATA_ROOT"), "기타/R_Studio/FBD_DATA_ZIP/통합자료_261030"))
SQ = os.path.join(os.path.expandvars("$ST_DATASET_ROOT"), "연구데이터셋_5종_GPT버전/02_체육건강_시공간_GPT버전/02_체육건강_시공간_GPT버전.sqlite")
PAN = os.path.join(ROOT, "02_패널")
C = pd.read_csv(os.path.join(ZD, "01_공변량_229x2011_2024.csv"), encoding="utf-8-sig", dtype={"sigungu_cd": str})
K = pd.read_csv(os.path.join(ZD, "00_시군구_229_대응표.csv"), encoding="utf-8-sig", dtype={"sigungu_cd": str}); assert K.sigungu_cd.is_unique and len(K) == 229
K.loc[K.sigungu_cd == "37310", "region"] = "대구시군위군"
C = C.drop(columns=["region"]).merge(K[["sigungu_cd", "region"]], on="sigungu_cd", how="left", validate="many_to_one"); assert C.region.notna().all()
out = pd.DataFrame({"year": C.year, "fbd_region": C.region.map(NFC),
                    "im_specialists_per100k": C.internal_medicine_specialists.astype(float) / C["pop"].astype(float) * 1e5,
                    "basic_livelihood_rate": C.basic_livelihood_recipient_rate.astype(float)})
out = out[(out.year >= 2011) & (out.year <= 2024)].sort_values(["fbd_region", "year"]).copy()
ref = out[out.year.isin([2020, 2024])].groupby("fbd_region").basic_livelihood_rate.mean()
yy = out.year.isin([2021, 2022, 2023]); r_ = out.basic_livelihood_rate / out.fbd_region.map(ref)
bad = yy & ((r_ < 0.2) | (r_ > 5))
print("[99c-resp] 수급률 결함 칸", int(bad.sum()), sorted(out.loc[bad, "fbd_region"].unique()))
assert bad.sum() == 33 and out.loc[bad, "fbd_region"].nunique() == 11
out.loc[bad, "basic_livelihood_rate"] = np.nan
for c in ["im_specialists_per100k", "basic_livelihood_rate"]:
    out[c] = out.groupby("fbd_region")[c].transform(lambda s: s.interpolate(method="linear", limit_area="inside"))
    out[c] = out[c].fillna(out.groupby("fbd_region")[c].transform("mean"))
chk = out[yy].basic_livelihood_rate / out[yy].fbd_region.map(out[out.year.isin([2020, 2024])].groupby("fbd_region").basic_livelihood_rate.mean())
print(f"[99c-resp] 정정 뒤 2021-23/(2020·2024 평균) {chk.min():.2f}~{chk.max():.2f}"); assert chk.min() >= 0.2 and chk.max() <= 5

P = pd.read_csv(os.path.join(PAN, "EXT_canonical_pool_PNEU_261108.csv"), encoding="utf-8-sig"); P["fbd_region"] = P.fbd_region.map(NFC)
X = pd.read_csv(os.path.join(PAN, "PNEU_mort_extra_261108.csv"), encoding="utf-8-sig"); X["fbd_region"] = X.fbd_region.map(NFC)
X["senility_share"] = X["노쇠_deaths"] / X["전체_deaths"] * 100
out = out.merge(P[["year", "fbd_region", "ltc_hospitals_per100k_65"]], on=["year", "fbd_region"], how="left", validate="one_to_one")
out = out.merge(X[["year", "fbd_region", "ill_defined_share", "senility_share", "전체_deaths"]], on=["year", "fbd_region"], how="left", validate="one_to_one")

# 기준 SQLite 분자 대조(읽기 전용)
con = sqlite3.connect(f"file:{SQ}?mode=ro", uri=True)
cols = {"mort__폐렴_deaths": "pneu", "mort__만성하기도질환_deaths": "clrd", "mort__호흡기질환_deaths": "resp", "mort__전체사망_deaths": "alld"}
ry = pd.read_sql(f"select * from region_year where year between 2011 and 2024 limit 1", con)
keyc = [c for c in ry.columns if c in ("fbd_region", "region", "key", "sigungu_cd", "sgg_code")]
print("[99c-resp] SQLite 키 열", keyc)
S = pd.read_sql("select year, " + ", ".join(keyc + [f'"{c}"' for c in cols]) + " from region_year where year between 2011 and 2024", con); con.close()
S = S.rename(columns=cols)
kk = "fbd_region" if "fbd_region" in S.columns else keyc[0]
S["fbd_region"] = S[kk].map(NFC)
MA = pd.read_parquet(os.path.join(PAN, "MASTER_시군구_연도_wide.parquet"), columns=["year", "fbd_region"] + list(cols)).rename(columns=cols)
MA["fbd_region"] = MA.fbd_region.map(NFC); MA = MA[MA.year.between(2011, 2024)]
J = S.merge(MA, on=["year", "fbd_region"], suffixes=("_sq", "_ma"), validate="one_to_one")
print("[99c-resp] SQLite·마스터 결합 행", len(J))
for v in cols.values():
    d = (J[v + "_sq"].fillna(-1) != J[v + "_ma"].fillna(-1)).sum(); print(f"[99c-resp] {v}: 불일치 {int(d)}칸, 합(SQLite) {J[v + '_sq'].sum():,.0f}"); assert d == 0
J2 = J.merge(out[["year", "fbd_region", "전체_deaths"]], on=["year", "fbd_region"], how="inner"); assert (J2["alld_sq"] == J2["전체_deaths"]).all()
out = out.drop(columns=["전체_deaths"])
nat = J.groupby("year")[["pneu_sq", "clrd_sq", "resp_sq"]].sum()
nat["share_P_of_PC"] = nat.pneu_sq / (nat.pneu_sq + nat.clrd_sq) * 100; nat["P_of_R"] = nat.pneu_sq / nat.resp_sq * 100; nat["C_of_R"] = nat.clrd_sq / nat.resp_sq * 100
print("[99c-resp] 전국 구성(%)\n", nat.round(1).to_string())
assert out.groupby("fbd_region").year.nunique().eq(14).all() and out.fbd_region.nunique() == 229 and not out.duplicated(["year", "fbd_region"]).any()
miss = out.isna().sum(); print("[99c-resp] 결측", miss[miss > 0].to_dict())
fp = os.path.join(PAN, "EXT_canonical_pool_RESP_261112.csv"); out.to_csv(fp, index=False, encoding="utf-8-sig")
print(f"[99c-resp] 저장 {fp} {out.shape}"); print(out.describe().T[["min", "50%", "max"]].round(2))
