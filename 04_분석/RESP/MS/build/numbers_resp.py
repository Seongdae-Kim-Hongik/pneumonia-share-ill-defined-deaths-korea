# numbers_resp.py — RESP(호흡기 사망 사인 구성: 폐렴 ÷ 폐렴+CLRD) 원고의 모든 수치를 결과 CSV에서 읽는다. 손입력 금지, assert로 정합 확인.
#  사용: from numbers_resp import load; N = load()
import os, unicodedata, numpy as np, pandas as pd, geopandas as gpd
HERE = os.path.dirname(os.path.abspath(__file__)); B = os.path.dirname(os.path.dirname(HERE)); RS = os.path.join(B, "results_std3")
SHP = os.environ.get("ST_SHP", os.path.join(HERE, "..", "..", "..", "..", "data", "boundary", "final.shp"))
NFC = lambda s: unicodedata.normalize("NFC", str(s)).strip()
rd = lambda f, **k: pd.read_csv(os.path.join(RS, f), encoding="utf-8-sig", **k)
WIN = [("W1", 2011, 2015), ("W2", 2016, 2019), ("W3", 2020, 2024), ("ALL", 2011, 2024)]
HYP = ["ill_defined_death_share", "ltc_hospitals_per_100k_65", "im_specialists_per_100k", "current_smoking_rate", "tb_suspected_screening", "influenza_vaccination_rate",
       "chewing_discomfort_rate_65plus", "basic_livelihood_rate", "walking_practice_rate", "moderate_pa_rate", "public_sports_facilities_per_100k"]
FORCED = ["urban_population_share", "physicians_per_1000", "sex_ratio", "fiscal_independence", "pop80_share"]
PA = ["walking_practice_rate", "moderate_pa_rate", "public_sports_facilities_per_100k"]
# 시군구 영문 표기(원고에 이름이 나오는 곳만; 코드로 결합)
EN = {"32060": "Sokcho", "36460": "Wando", "36040": "Naju", "32390": "Inje", "32310": "Hongcheon", "32400": "Goseong (Gangwon)", "24020": "Seo-gu (Gwangju)",
      "21310": "Gijang", "21100": "Saha", "21030": "Dong-gu (Busan)", "21110": "Geumjeong", "31250": "Gwangju (Gyeonggi)", "21090": "Haeundae", "11240": "Songpa", "11040": "Seongdong", "11070": "Jungnang"}
# 경계 파일(2014 기준) 시도 코드 체계: 11 서울 21 부산 22 대구 23 인천 24 광주 25 대전 26 울산 29 세종 31 경기 32 강원 33 충북 34 충남 35 전북 36 전남 37 경북 38 경남 39 제주
SIDO_EN = {"11": "Seoul", "21": "Busan", "22": "Daegu", "23": "Incheon", "24": "Gwangju", "25": "Daejeon", "26": "Ulsan", "29": "Sejong", "31": "Gyeonggi", "32": "Gangwon",
           "33": "Chungbuk", "34": "Chungnam", "35": "Jeonbuk", "36": "Jeonnam", "37": "Gyeongbuk", "38": "Gyeongnam", "39": "Jeju"}

def codes():   # 모형의 지역 색인 = 경계 파일 region 순서(37R_fit_binom.R). 코드표는 같은 파일에서 1:1로 만든다(이름 결합 아님: 모형이 쓴 색인 그 자체).
    G = gpd.read_file(SHP); G["region"] = G.region.map(NFC); G["cd"] = G.sigungu_cd.astype(str)
    assert G.region.is_unique and G.cd.is_unique and len(G) == 229
    return G

def load():
    N = {}; G = codes(); R2C = dict(zip(G.region, G.cd))
    P = pd.read_csv(os.path.join(B, "panel_RESP_binom_std3.csv"), encoding="utf-8-sig"); P["fbd_region"] = P.fbd_region.map(NFC); P["cd"] = P.fbd_region.map(R2C)
    assert P.cd.notna().all() and len(P) == 3206 and P.cd.nunique() == 229; N["P"] = P
    N["n_rows"], N["n_districts"] = len(P), P.cd.nunique(); N["n_pneu"], N["n_clrd"] = int(P.pneu.sum()), int(P.clrd.sum()); N["n_pc"] = int(P.n_pc.sum())
    assert N["n_pc"] == N["n_pneu"] + N["n_clrd"]
    N["n_pc_zero"] = int((P.n_pc == 0).sum()); N["n_pc_lt5"] = int((P.n_pc < 5).sum())
    # 전국 원표(DT_1B34E01)
    T = rd("D1_national_trend.csv").set_index("year"); N["T"] = T
    N["share_2011"], N["share_2024"] = T.P_share_PC[2011], T.P_share_PC[2024]
    N["clrd_2011"], N["clrd_2024"], N["pneu_2011"], N["pneu_2024"] = (int(T.clrd[2011]), int(T.clrd[2024]), int(T.pneu[2011]), int(T.pneu[2024]))
    N["ill_2011"] = T.illdef_share_all[2011]; N["ill_2124_lo"], N["ill_2124_hi"] = T.illdef_share_all.loc[2021:2024].min(), T.illdef_share_all.loc[2021:2024].max()
    N["covid_2022"] = int(T.covid[2022])
    # 시군구 합과 전국 원표 비교(연령미상·주소미상 차이)
    y = P.groupby("year")[["pneu", "clrd"]].sum(); N["panel_share_2011"] = 100 * y.pneu[2011] / (y.pneu[2011] + y.clrd[2011]); N["panel_share_2024"] = 100 * y.pneu[2024] / (y.pneu[2024] + y.clrd[2024])
    assert abs(N["panel_share_2011"] - N["share_2011"]) < 1.0 and abs(N["panel_share_2024"] - N["share_2024"]) < 1.0
    A = rd("D1_national_age_sex.csv"); N["AS"] = A
    N["clrd_rr_lo"], N["clrd_rr_hi"] = A.clrd_rate_ratio.min(), A.clrd_rate_ratio.max(); N["pneu_rr_lo"], N["pneu_rr_hi"] = A.pneu_rate_ratio.min(), A.pneu_rate_ratio.max()
    assert (A.dP_share_pp > 0).all() and A.clrd_rate_ratio.max() < 1 and A.pneu_rate_ratio.min() > 1; N["n_agesex"] = len(A)
    # 기대 구성 p0의 연도 안 지역 차
    N["p0_within_year_range"] = float(P.groupby("year").p0.agg(lambda s: s.max() - s.min()).max())
    # 표 1 창별
    T1 = {}
    for w, a, b in WIN:
        q = P[(P.year >= a) & (P.year <= b)]; g = q.groupby("cd")[["pneu", "clrd", "E_P", "E_C"]].sum(); sh = 100 * g.pneu / (g.pneu + g.clrd)
        T1[w] = dict(n=len(q), pneu=int(q.pneu.sum()), clrd=int(q.clrd.sum()), share=100 * q.pneu.sum() / q.n_pc.sum(), exp_share=100 * q.E_P.sum() / (q.E_P.sum() + q.E_C.sum()),
                     sh_p10=sh.quantile(.1), sh_med=sh.median(), sh_p90=sh.quantile(.9),
                     cov={v: (q[f"{v}_raw"].mean(), q[f"{v}_raw"].std()) for v in HYP + FORCED})
    N["T1"] = T1
    # 우도·주모형
    L = rd("S1_likelihood.csv").set_index("family"); N["waic_binom"], N["waic_bb"] = L.WAIC["binomial"], L.WAIC["betabinomial"]; assert N["waic_bb"] < N["waic_binom"]
    F = rd("S3_main_fit.csv").iloc[0]; N["waic_m1"], N["phi_m1"], N["rho_m1"] = F.WAIC, F.phi_area, F.rho_bb
    M = rd("S3_main_OR.csv").set_index("cov"); N["main"] = {v: dict(OR=M.OR[v], lo=M.lo[v], hi=M.hi[v], P=M.P_gt1[v], cred=bool(M.cred[v])) for v in M.index}
    assert set(N["main"]) == set(HYP + FORCED)
    N["pa_all_null"] = all(not N["main"][v]["cred"] for v in PA); assert N["pa_all_null"]
    NC = rd("S3_negctrl_OR.csv").set_index("cov"); N["nc"] = {v: (NC.OR[v], NC.lo[v], NC.hi[v], bool(NC.cred[v])) for v in NC.index}; assert not any(t[3] for t in N["nc"].values())
    S2 = rd("S2_setcompare.csv").set_index("set").WAIC; N["set_waic"] = S2.to_dict(); N["waic_forced"] = L.WAIC["betabinomial"]
    # 다중우주
    MV = pd.concat([rd("S7_mv_001_100.csv"), rd("S7_mv_101_200.csv")]); assert MV.spec.nunique() == 200; N["n_mv"] = 200
    N["mv"] = {v: dict(n=int((MV["cov"] == v).sum()), cred=float(MV[MV["cov"] == v].cred.mean()), gt1=float((MV[MV["cov"] == v].OR > 1).mean()),
                       med=float(MV[MV["cov"] == v].OR.median())) for v in HYP}
    # KH
    N["kh"] = {}; N["kh_waic"] = {}
    for k in ("I", "II", "III", "IV"):
        o = rd(f"S43_KH_{k}_OR.csv").set_index("cov"); N["kh"][k] = {v: (o.OR[v], o.lo[v], o.hi[v], bool(o.cred[v])) for v in o.index}; N["kh_waic"][k] = rd(f"S43_KH_{k}_fit.csv").WAIC.iloc[0]
    N["kh_best"] = min(N["kh_waic"], key=N["kh_waic"].get); assert N["kh_best"] == "IV"
    # 분해·창·민감도·사후
    D = rd("S22_decomp_OR.csv").set_index("cov"); N["dec"] = {v: (D.OR[v], D.lo[v], D.hi[v], bool(D.cred[v])) for v in D.index}
    W = rd("S4_window_OR.csv"); N["win"] = {(r.model, r["cov"]): (r.OR, r.lo, r.hi, bool(r.cred)) for _, r in W.iterrows()}
    S = rd("S40_sens_OR.csv"); N["sens"] = {(r.model, r["cov"]): (r.OR, r.lo, r.hi, bool(r.cred)) for _, r in S.iterrows()}; N["sens_models"] = list(dict.fromkeys(S.model))
    H = pd.concat([rd("S46_posthoc_reverse.csv"), rd("S47_posthoc_chewing.csv")]); N["ph"] = {(r.spec, r["cov"]): (r.OR, r.lo, r.hi, bool(r.cred)) for _, r in H.iterrows()}
    SPp = rd("S41_spatialplus_OR.csv"); N["splus"] = {r["cov"]: (r.OR, r.lo, r.hi, bool(r.cred)) for _, r in SPp.iterrows()}   # 37R_spatialplus_posthoc2.R
    # 속도
    F2 = rd("S20_speed_M2a_fit.csv").iloc[0]; N["waic_m2a"], N["sd_slope"], N["phi_slope"] = F2.WAIC, F2.sd_slope, F2.phi_slope
    N["waic_m2b"] = rd("S20_speed_M2b_fit.csv").WAIC.iloc[0]; N["waic_m3"] = rd("S21_speed_determinants_fit.csv").WAIC.iloc[0]
    Sd = rd("S20_speed_M2a_area.csv"); Sd["cd"] = Sd.fbd_region.map(NFC).map(R2C); assert Sd.cd.notna().all() and len(Sd) == 229; N["speed"] = Sd
    N["delta_sd"] = Sd.delta.std(); fast = Sd[Sd.P_gt0 > 0.95]; slow = Sd[Sd.P_gt0 < 0.05]; N["n_fast"], N["n_slow"] = len(fast), len(slow)
    typ = lambda r: "ward" if NFC(r).endswith("구") else ("county" if NFC(r).endswith("군") else "city")
    Sd["type"] = Sd.fbd_region.map(typ); N["n_fast_county"] = int((fast.fbd_region.map(typ) == "county").sum()); N["n_slow_ward"] = int((slow.fbd_region.map(typ) == "ward").sum())
    N["delta_by_type"] = Sd.groupby("type").delta.mean().to_dict()
    Sd["sido"] = Sd.cd.str[:2].map(SIDO_EN); N["delta_by_sido"] = Sd.groupby("sido").delta.mean().sort_values(ascending=False).to_dict()
    fs_ = pd.concat([fast, slow]); N["n_fs_ci1"] = int(((fs_.lo < 0) & (fs_.hi > 0)).sum())
    N["fast_by_sido"] = fast.cd.str[:2].map(SIDO_EN).value_counts().to_dict(); N["slow_by_sido"] = slow.cd.str[:2].map(SIDO_EN).value_counts().to_dict()
    top = Sd.sort_values("delta", ascending=False); N["top3"] = [(EN[c], d) for c, d in zip(top.cd[:3], top.delta[:3])]; N["bottom3"] = [(EN[c], d) for c, d in zip(top.cd[::-1][:3], top.delta[::-1][:3])]
    Lv = rd("S3_area_M1.csv"); Lv["cd"] = Lv.fbd_region.map(NFC).map(R2C); N["level"] = Lv
    m = Sd.merge(Lv[["cd", "re_total"]], on="cd"); N["corr_level_speed"] = float(np.corrcoef(m.re_total, m.delta)[0, 1])
    m2b = pd.read_csv(os.path.join(RS, "S20_speed_M2b_area.csv"), encoding="utf-8-sig"); N["corr_m2a_m2b"] = float(np.corrcoef(Sd.set_index("fbd_region").delta.loc[m2b.fbd_region], m2b.delta)[0, 1])
    M3 = rd("S21_speed_determinants_OR.csv").set_index("cov"); N["m3"] = {v: (M3.OR[v], M3.lo[v], M3.hi[v], bool(M3.cred[v]), M3.P_gt1[v]) for v in M3.index}
    N["m3_any_cred"] = any(M3.cred[[i for i in M3.index if i.startswith("bx_")]])
    # 대체 검정
    D2 = rd("D2_substitution_summary.csv", index_col=0); N["sub"] = {k: (D2.estimate[k], D2.lo[k], D2.hi[k]) for k in D2.index}; N["sub_n"] = int(D2.n_regions.iloc[0])
    D2s = rd("D2_substitution_sens.csv"); N["sub_sens"] = {r.window: (r.signal_corr_PC, r.lo, r.hi) for _, r in D2s.iterrows()}   # 37R_discriminate_sens.py
    # 전국 성·연령 절대 사망률 변화(10만 명당, 2024 − 2011)
    A["dPr"] = A.pneu_rate_2024 - A.pneu_rate_2011; A["dCr"] = A.clrd_rate_2024 - A.clrd_rate_2011; A["dSum"] = A.dPr + A.dCr; N["AS"] = A
    old = A[A.age.isin(["85 - 89세", "90세이상"])]; young = A[~A.age.isin(["85 - 89세", "90세이상"])]
    N["n_young_sum_le0"] = int((young.dSum <= 0).sum()); N["n_young"] = len(young); N["n_old_sum_gt0"] = int((old.dSum > 0).sum()); N["n_old"] = len(old)
    mid = A[A.age.isin(["65 - 69세", "70 - 74세", "75 - 79세", "80 - 84세"])]; N["n_mid_fell"] = int((mid.dSum < 0).sum()); N["n_mid"] = len(mid); assert N["n_mid_fell"] == N["n_mid"] == 8 and N["n_old_sum_gt0"] == 4
    with np.errstate(all="ignore"):
        N["moran_speed"] = moran(Sd.set_index("cd").delta.to_dict()); N["moran_level"] = moran(Lv.set_index("cd").re_total.to_dict())
    assert N["moran_speed"][1] <= 0.001 and N["moran_level"][1] <= 0.001
    return N

def moran(vals_by_cd, nperm=999, seed=37):   # INLA 그래프(graph_593, 경계 파일 순서) 행표준화, 순열 999
    G = codes(); Lg = open(os.path.join(B, "graph_593.graph")).read().split("\n"); n = int(Lg[0]); W = np.zeros((n, n))
    for ln in Lg[1:]:
        q = ln.split()
        if len(q) >= 2:
            for j in q[2:]: W[int(q[0]) - 1, int(j) - 1] = 1
    W = W / W.sum(1, keepdims=True); x = G.cd.map(vals_by_cd).values.astype(float); assert not np.isnan(x).any()
    z = x - x.mean(); I = (z @ W @ z) / (z @ z); r = np.random.default_rng(seed); ps = [(lambda q: (q @ W @ q) / (q @ q))(r.permutation(z)) for _ in range(nperm)]
    return float(I), (1 + sum(p >= I for p in ps)) / (nperm + 1)

if __name__ == "__main__":
    N = load()
    for k in ("n_rows", "n_pneu", "n_clrd", "share_2011", "share_2024", "waic_m1", "waic_m2a", "delta_sd", "n_fast", "n_slow", "n_fast_county", "n_slow_ward", "corr_level_speed", "corr_m2a_m2b", "kh_best", "top3", "bottom3", "fast_by_sido", "slow_by_sido"):
        print(k, N[k])
    print(moran(N["speed"].set_index("cd").delta.to_dict()), moran(N["level"].set_index("cd").re_total.to_dict()))
