#!/usr/bin/env python3
# 37R — RESP 판별 분석(사전지정, 설계 메모 5절; 2026-11-12, 새 파일)
#  D1 전국 원표(DT_1B34E01) 성×연령 폐렴 비중·사인별 사망률 2011 대 2024, 불명확(R00-R99)·코로나 추이
#  D2 대체 검정: 시군구 W1(2011-15)→W3(2020-24) ΔlogSIR_P, ΔlogSIR_C, 합; 포아송 표본 분산을 뺀 신호 분산·공분산, 지역 부트스트랩 2,000회
#  D4 Δ불명확 사인 비율 대 Δ구성(초과 로짓) 상관
#  산출: 04_분석/RESP/results_std3/D1_national_age_sex.csv, D1_national_trend.csv, D2_substitution_regions.csv, D2_substitution_summary.csv, D4_illdefined_comovement.csv
import os, unicodedata
import numpy as np, pandas as pd
NFC = lambda s: unicodedata.normalize("NFC", str(s))
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.normpath(os.path.join(HERE, ".."))
OUT = os.path.join(ROOT, "04_분석", "RESP"); RES = os.path.join(OUT, "results_std3"); os.makedirs(RES, exist_ok=True)
N = pd.read_csv(os.path.join(ROOT, "00_원천/D_사망_인구_암/DT_1B34E01_national_long.csv"), encoding="utf-8-sig", dtype={"cause_code": str})
N["value"] = pd.to_numeric(N.value, errors="coerce")
CC = {"A02": "pneu", "A04": "clrd", "A": "resp", "0": "all", "I": "illdef", "125": "covid", "A01": "flu", "A05": "resp_rest", "A03": "lri"}
n = N[N.cause_code.isin(CC) & (N.item == "사망자수")].copy(); n["c"] = n.cause_code.map(CC)
# D1a 전국 추이(계·계)
t = n[(n.sex == "계") & (n.age == "계")].pivot_table(index="year", columns="c", values="value", aggfunc="sum").fillna(0)
t["P_share_PC"] = t.pneu / (t.pneu + t.clrd) * 100; t["illdef_share_all"] = t.illdef / t["all"] * 100; t["covid_share_all"] = t.covid / t["all"] * 100
t["resp_plus_illdef_share_all"] = (t.resp + t.illdef) / t["all"] * 100
t.round(2).to_csv(os.path.join(RES, "D1_national_trend.csv"), encoding="utf-8-sig"); print("[D1] 전국 추이\n", t[["pneu", "clrd", "illdef", "covid", "P_share_PC", "illdef_share_all"]].round(1).to_string())
# D1b 성×연령: 2011 대 2024 사망자수·사망률
AG = ["50 - 54세", "55 - 59세", "60 - 64세", "65 - 69세", "70 - 74세", "75 - 79세", "80 - 84세", "85 - 89세", "90세이상"]
r = N[N.cause_code.isin(["A02", "A04"]) & N.age.isin(AG) & N.sex.isin(["남자", "여자"]) & N.year.isin([2011, 2024])].copy(); r["c"] = r.cause_code.map(CC)
w = r.pivot_table(index=["sex", "age", "year"], columns=["c", "item"], values="value", aggfunc="sum")
w.columns = [f"{a}_{'n' if b == '사망자수' else 'rate'}" for a, b in w.columns]; w = w.reset_index()
w["P_share"] = w.pneu_n / (w.pneu_n + w.clrd_n) * 100
x = w.pivot_table(index=["sex", "age"], columns="year", values=["P_share", "pneu_rate", "clrd_rate"])
x.columns = [f"{a}_{b}" for a, b in x.columns]; x = x.reset_index()
x["dP_share_pp"] = x.P_share_2024 - x.P_share_2011; x["pneu_rate_ratio"] = x.pneu_rate_2024 / x.pneu_rate_2011; x["clrd_rate_ratio"] = x.clrd_rate_2024 / x.clrd_rate_2011
x["age"] = pd.Categorical(x.age, AG, ordered=True); x = x.sort_values(["sex", "age"])
x.round(3).to_csv(os.path.join(RES, "D1_national_age_sex.csv"), index=False, encoding="utf-8-sig"); print("[D1] 성×연령\n", x[["sex", "age", "P_share_2011", "P_share_2024", "dP_share_pp", "pneu_rate_ratio", "clrd_rate_ratio"]].round(2).to_string())

# D2 대체 검정
D = pd.read_csv(os.path.join(OUT, "panel_RESP_binom_std3.csv"), encoding="utf-8-sig"); D["fbd_region"] = D.fbd_region.map(NFC)
D["W"] = np.where(D.year <= 2015, "W1", np.where(D.year >= 2020, "W3", "W2"))
A = D[D.W != "W2"].groupby(["fbd_region", "W"]).agg(P=("pneu", "sum"), C=("clrd", "sum"), EP=("E_P", "sum"), EC=("E_C", "sum"), ill=("ill_defined_death_share_raw", "mean")).unstack("W")
A.columns = [f"{a}_{b}" for a, b in A.columns]; A = A.reset_index()
ok = (A[["P_W1", "C_W1", "P_W3", "C_W3"]] > 0).all(axis=1); print("[D2] 0칸 때문에 제외 지역", int((~ok).sum())); A = A[ok].copy()
A["dP"] = np.log(A.P_W3 / A.EP_W3) - np.log(A.P_W1 / A.EP_W1); A["dC"] = np.log(A.C_W3 / A.EC_W3) - np.log(A.C_W1 / A.EC_W1)
A["dT"] = np.log((A.P_W3 + A.C_W3) / (A.EP_W3 + A.EC_W3)) - np.log((A.P_W1 + A.C_W1) / (A.EP_W1 + A.EC_W1)); A["dComp"] = A.dP - A.dC
A["vP"] = 1 / A.P_W3 + 1 / A.P_W1; A["vC"] = 1 / A.C_W3 + 1 / A.C_W1   # 포아송 표본 분산(로그 SIR)
A["dIll"] = A.ill_W3 - A.ill_W1
A.to_csv(os.path.join(RES, "D2_substitution_regions.csv"), index=False, encoding="utf-8-sig")
def stats(B):
    sP = B.dP.var() - B.vP.mean(); sC = B.dC.var() - B.vC.mean(); cov = np.cov(B.dP, B.dC)[0, 1]   # 표본 잡음은 P·C 사이 독립 → 공분산 비편향
    corr = cov / np.sqrt(max(sP, 1e-12) * max(sC, 1e-12)); vComp = sP + sC - 2 * cov
    return dict(sig_var_P=sP, sig_var_C=sC, cov_PC=cov, signal_corr_PC=corr, raw_corr_PC=np.corrcoef(B.dP, B.dC)[0, 1],
                share_comp_var_from_P=sP / vComp, share_comp_var_from_C=sC / vComp, share_comp_var_from_neg_cov=-2 * cov / vComp,
                mean_dP=B.dP.mean(), mean_dC=B.dC.mean(), mean_dT=B.dT.mean(), corr_dIll_dComp=np.corrcoef(B.dIll, B.dComp)[0, 1], corr_dIll_dP=np.corrcoef(B.dIll, B.dP)[0, 1], corr_dIll_dC=np.corrcoef(B.dIll, B.dC)[0, 1])
est = stats(A); rng = np.random.default_rng(37); bs = pd.DataFrame([stats(A.iloc[rng.integers(0, len(A), len(A))]) for _ in range(2000)])
summ = pd.DataFrame({"estimate": pd.Series(est), "lo": bs.quantile(0.025), "hi": bs.quantile(0.975)}); summ["n_regions"] = len(A)
summ.round(4).to_csv(os.path.join(RES, "D2_substitution_summary.csv"), encoding="utf-8-sig"); print("[D2] 대체 검정\n", summ.round(3).to_string())
summ.loc[["corr_dIll_dComp", "corr_dIll_dP", "corr_dIll_dC"]].round(4).to_csv(os.path.join(RES, "D4_illdefined_comovement.csv"), encoding="utf-8-sig")
