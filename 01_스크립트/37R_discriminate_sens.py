#!/usr/bin/env python3
# 37R — RESP 대체 검정 민감도(2026-11-12 새 파일, review 1회차 지적): 37R_discriminate.py의 D2와 같은 계산을 다른 창 쌍으로.
#  S1: W1(2011-15) → W2(2016-19)(코로나 이전), S2: W1 → 2023-24(2020-22 제외). 산출: results_std3/D2_substitution_sens.csv
import os, unicodedata, numpy as np, pandas as pd
NFC = lambda s: unicodedata.normalize("NFC", str(s))
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.normpath(os.path.join(HERE, "..")); OUT = os.path.join(ROOT, "04_분석", "RESP"); RES = os.path.join(OUT, "results_std3")
D = pd.read_csv(os.path.join(OUT, "panel_RESP_binom_std3.csv"), encoding="utf-8-sig"); D["fbd_region"] = D.fbd_region.map(NFC)
def run(a0, a1, b0, b1, lab):
    q = D[((D.year >= a0) & (D.year <= a1)) | ((D.year >= b0) & (D.year <= b1))].copy(); q["W"] = np.where(q.year <= a1, "A", "B")
    A = q.groupby(["fbd_region", "W"]).agg(P=("pneu", "sum"), C=("clrd", "sum"), EP=("E_P", "sum"), EC=("E_C", "sum")).unstack("W"); A.columns = [f"{x}_{y}" for x, y in A.columns]
    A = A[(A[["P_A", "C_A", "P_B", "C_B"]] > 0).all(axis=1)]
    A["dP"] = np.log(A.P_B / A.EP_B) - np.log(A.P_A / A.EP_A); A["dC"] = np.log(A.C_B / A.EC_B) - np.log(A.C_A / A.EC_A)
    A["vP"] = 1 / A.P_B + 1 / A.P_A; A["vC"] = 1 / A.C_B + 1 / A.C_A
    def st(B):
        sP = B.dP.var() - B.vP.mean(); sC = B.dC.var() - B.vC.mean(); cov = np.cov(B.dP, B.dC)[0, 1]
        return cov / np.sqrt(max(sP, 1e-12) * max(sC, 1e-12))
    e = st(A); rng = np.random.default_rng(37); bs = [st(A.iloc[rng.integers(0, len(A), len(A))]) for _ in range(2000)]
    return dict(window=lab, n_regions=len(A), signal_corr_PC=e, lo=np.quantile(bs, .025), hi=np.quantile(bs, .975))
R = pd.DataFrame([run(2011, 2015, 2016, 2019, "2011-2015 to 2016-2019"), run(2011, 2015, 2023, 2024, "2011-2015 to 2023-2024")])
R.round(4).to_csv(os.path.join(RES, "D2_substitution_sens.csv"), index=False, encoding="utf-8-sig"); print(R.round(3).to_string())
