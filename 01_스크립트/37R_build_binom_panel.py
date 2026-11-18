#!/usr/bin/env python3
# 37R — RESP 이항 패널(2026-11-12). 80이 만든 panel_RESP_std3.csv(분자 = 폐렴, E = E_P)에 이항 분모·offset을 붙인다.
#  n_pc = 폐렴 + 만성하기도질환 사망, p0 = E_P/(E_P+E_C) (PNEU_Estd2·CLRD_Estd2, 연도별 ΣE = Σ관측으로 재척도 — 80과 같은 규칙), off_pc = logit(p0)
#  민감도: n_r = 호흡계통 전체(J00-J98), p0r = E_P/E_R(RESP_Estd.csv E_std 재척도), off_r = logit(p0r); CLRD 결과판 y = clrd, off_cr = logit(E_C/E_R)
#  민감도 전용 공변량: senility_share(R54 ÷ 전체 사망 %) z
#  분자는 기준 SQLite region_year(읽기 전용)에서 읽고 패널 cases(폐렴)와 3,206칸 assert
#  산출: 04_분석/RESP/panel_RESP_binom_std3.csv
import os, sqlite3, unicodedata
import numpy as np, pandas as pd
NFC = lambda s: unicodedata.normalize("NFC", str(s))
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.normpath(os.path.join(HERE, ".."))
SQ = os.path.join(os.path.expandvars("$ST_DATASET_ROOT"), "연구데이터셋_5종_GPT버전/02_체육건강_시공간_GPT버전/02_체육건강_시공간_GPT버전.sqlite")
PAN = os.path.join(ROOT, "02_패널"); OUT = os.path.join(ROOT, "04_분석", "RESP")
D = pd.read_csv(os.path.join(OUT, "panel_RESP_std3.csv"), encoding="utf-8-sig"); D["fbd_region"] = D.fbd_region.map(NFC)
con = sqlite3.connect(f"file:{SQ}?mode=ro", uri=True)
S = pd.read_sql('select year, fbd_region, "mort__폐렴_deaths" as pneu, "mort__만성하기도질환_deaths" as clrd, "mort__호흡기질환_deaths" as resp from region_year where year between 2011 and 2024', con); con.close()
S["fbd_region"] = S.fbd_region.map(NFC)
D = D.merge(S, on=["year", "fbd_region"], how="left", validate="one_to_one"); assert len(D) == 3206 and (D.cases == D.pneu).all() and D[["clrd", "resp"]].notna().all().all()
def ext_E(fn, col, obs):
    X = pd.read_csv(os.path.join(PAN, fn), encoding="utf-8-sig"); X["fbd_region"] = X.fbd_region.map(NFC)
    e = D[["year", "fbd_region"]].merge(X[["year", "fbd_region", col]], on=["year", "fbd_region"], how="left", validate="one_to_one")[col]
    assert e.notna().all() and (e > 0).all(), fn
    return e * D.groupby("year")[obs].transform("sum") / e.groupby(D.year).transform("sum")
D["E_P"] = D.E; D["E_C"] = ext_E("CLRD_Estd2.csv", "E_std2", "clrd"); D["E_R"] = ext_E("RESP_Estd.csv", "E_std", "resp")
assert abs(D.E_P.sum() - D.pneu.sum()) < 1e-6 * D.pneu.sum()
lg = lambda p: np.log(p / (1 - p))
D["n_pc"] = D.pneu + D.clrd; D["p0"] = D.E_P / (D.E_P + D.E_C); D["off_pc"] = lg(D.p0)
D["p0r"] = (D.E_P / D.E_R).clip(upper=0.999); D["off_r"] = lg(D.p0r)
D["p0cr"] = (D.E_C / D.E_R).clip(upper=0.999); D["off_cr"] = lg(D.p0cr)
X = pd.read_csv(os.path.join(PAN, "PNEU_mort_extra_261108.csv"), encoding="utf-8-sig"); X["fbd_region"] = X.fbd_region.map(NFC)
X["senility_share_raw"] = X["노쇠_deaths"] / X["전체_deaths"] * 100
D = D.merge(X[["year", "fbd_region", "senility_share_raw"]], on=["year", "fbd_region"], how="left", validate="one_to_one")
D["senility_share"] = (D.senility_share_raw - D.senility_share_raw.mean()) / D.senility_share_raw.std(ddof=0)
D["share_obs"] = np.where(D.n_pc > 0, D.pneu / D.n_pc.where(D.n_pc > 0), np.nan)
print("[37R] n_pc = 0 칸", int((D.n_pc == 0).sum()), "· n_pc < 5 칸", int((D.n_pc < 5).sum()), "· p0 범위", D.p0.round(3).min(), D.p0.round(3).max(), "· p0r>0.99 칸", int((D.E_P / D.E_R > 0.99).sum()))
print("[37R] 연도별 관측 구성·연령 기대 구성(전국 합)")
g = D.groupby("year").agg(P=("pneu", "sum"), C=("clrd", "sum"), EP=("E_P", "sum"), EC=("E_C", "sum"))
g["obs"] = g.P / (g.P + g.C); g["exp_age"] = g.EP / (g.EP + g.EC); print(g.round(3).to_string())
D.to_csv(os.path.join(OUT, "panel_RESP_binom_std3.csv"), index=False, encoding="utf-8-sig")
print("[37R] 저장 panel_RESP_binom_std3.csv", D.shape)
