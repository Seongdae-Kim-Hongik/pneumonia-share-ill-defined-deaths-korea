#!/usr/bin/env python3
# 39m — 사망 종속변수용 세분 간접 연령표준화 E (39_build_Estd_fine.py 의 사망판, 2026-11-06 CLRD부터). 39 원본은 건보 진료(298 매핑) 전용이라 건드리지 않는다.
#  사용: ST_FBDZIP=<창원 교정 인구 폴더> [ST_E2_PANEL_SUF=_std3] python3 39m_build_Estd_mort.py <TAG>
#  사인: 99m_screen_mortality_prep.CAUSES 와 같은 표(STRK·IHD·FALL·SUIC·ALZ·CLRD) — 전국 KOSIS DT_1B34E01 사인×5세 사망자수(연령미상 제외)
#  ① 주 E(E_std2): 5세 18구간 0-4 … 80-84, 85+ (전국 사망 원자료가 85세 이상까지 5세라 진료 자료 75+보다 세분)
#  ② 거친 E(E_std_c10): 진료 시리즈와 같은 10구간(0-9 … 60-64·65-69·70-74·75+) — 민감도 s8(구간 수 축소) 대응
#  ③ 시군구 5세 인구 = FBD_DATA_ZIP(39·99m 매칭 규칙 그대로), 분모 = 패널 offset × FBD 연령 비율(총인구 비 |비−1| ≤ 1% assert)
#  ④ rate[y,a] = 전국 사망자수 / Σ_d 분모 ; E = Σ_a 분모 × rate ; 연도별 ΣE = Σcases 재척도
#  산출: 02_패널/<TAG>_Estd2.csv (year, fbd_region, E_std2, E_std_c10, SIR_*, pop65/80/85_share_raw)
#        02_패널/<TAG>_national_agerates_mort.csv, 04_분석/<TAG>/results_std2/S00_Estd2_validation.csv
import os, sys, importlib.util, unicodedata
import numpy as np, pandas as pd
from scipy.stats import spearmanr
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
def _load(nm, f):
    s = importlib.util.spec_from_file_location(nm, os.path.join(HERE, f)); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
m38 = _load("m38", "38_build_Estd_all.py"); cw = _load("cw", "40_region_crosswalk.py")
NFC = lambda s: unicodedata.normalize("NFC", str(s))
CAUSES = {"STRK": "뇌혈관 질환 (I60-I69)", "IHD": "허혈성 심장 질환 (I20-I25)", "FALL": "낙상(추락) (W00-W19)",
          "SUIC": "고의적 자해(자살) (X60-X84)", "ALZ": "알츠하이머병 (G30)", "CLRD": "만성 하기도 질환 (J40-J47)"}   # 99m 과 같은 표
TAG = sys.argv[1]; assert TAG in CAUSES, TAG; NC = CAUSES[TAG]
assert os.environ.get("ST_FBDZIP"), "ST_FBDZIP(창원 2023 교정 인구 폴더)를 지정"
B18 = [f"{lo}-{lo+4}" for lo in range(0, 85, 5)] + ["85+"]
C10 = ["0-9", "10-19", "20-29", "30-39", "40-49", "50-59", "60-64", "65-69", "70-74", "75+"]
def to10(b):
    if b == "85+": return "75+"
    lo = int(b.split("-")[0])
    return C10[lo // 10] if lo < 60 else ("60-64" if lo < 65 else "65-69" if lo < 70 else "70-74" if lo < 75 else "75+")

# ── 전국 사인×5세 사망자수(99m 규칙) ──
N = pd.read_csv(os.path.join(ROOT, "00_원천", "D_사망_인구_암", "DT_1B34E01_national_long.csv"), encoding="utf-8-sig")
N = N[(N.sex == "계") & (N.item == "사망자수") & N.year.between(2011, 2024) & (N.cause == NC)]
def nat_band(a):
    a = a.replace(" ", "")
    if a in ("0세", "1-4세"): return "0-4"
    if a in ("85-89세", "90세이상"): return "85+"
    if a.endswith("세") and "-" in a:
        lo, hi = a[:-1].split("-")
        if int(hi) - int(lo) == 4 and int(lo) <= 80: return f"{lo}-{hi}"
    return None
N["band"] = N.age.map(nat_band)
NB = N[N.band.notna()].groupby(["year", "band"]).value.sum().unstack()[B18]
tot = N[N.age == "계"].set_index("year").value; unk = N[N.age == "연령미상"].set_index("year").value.reindex(tot.index).fillna(0)
assert ((NB.sum(axis=1) + unk - tot).abs() <= 1).all(), "전국 연령 합 ≠ 계"
print(f"[39m] {TAG} {NC}: 전국 14년 사망 {int(tot.sum()):,} (연령미상 {int(unk.sum())})")

# ── 시군구 5세 인구(FBD_DATA_ZIP) ──
PAN = os.path.join(ROOT, "04_분석", TAG, f"panel_{TAG}{os.environ.get('ST_E2_PANEL_SUF', '')}.csv")
P = pd.read_csv(PAN, encoding="utf-8-sig"); P["key"] = P.key.map(NFC); P["fbd_region"] = P.fbd_region.map(NFC); PKEYS = set(P.key)
SIDO_HDR = {k for k in cw.SIDO_STD if len(k) >= 3 and (k.endswith("시") or k.endswith("도"))}
FIVE = [f"{lo}-{lo+4}세" for lo in range(0, 85, 5)]; OLD85 = ["85-89세", "90-94세", "95-99세", "100세 이상"]
EXTRA = {("충청북도", "청원군"): "충청북도|청주시"}; rows = []
for y in range(2011, 2025):
    d = pd.read_csv(os.path.join(m38.FBDZIP, f"{y}.csv"), encoding="cp949", dtype=str)
    d["행정구역별"] = d["행정구역별"].map(NFC).str.strip(); d["연령별"] = d["연령별"].map(NFC).str.strip(); d["v"] = pd.to_numeric(d["전체"].str.replace(",", ""), errors="coerce")
    sido = None; city = None; blocks = (d["행정구역별"] != d["행정구역별"].shift()).cumsum()
    for _, g in d.groupby(blocks, sort=False):
        nm = g["행정구역별"].iat[0]
        if nm == "전국": continue
        if nm in SIDO_HDR:
            sido = nm; city = None
            if nm != "세종특별자치시": continue
            g = g.drop_duplicates("연령별")
        sg = nm.split("-")[-1]
        if sg.endswith("시"): city = sg
        elif sg.endswith("구") and city is not None and cw.sido_std(sido) not in ("서울시", "부산시", "대구시", "인천시", "광주시", "대전시", "울산시"): continue
        else: city = None
        a = g.set_index("연령별")["v"]; t = a.get("계", np.nan)
        if pd.isna(t): continue
        f = a.reindex(FIVE); o = a.reindex(OLD85); assert f.notna().all() and o.notna().all(), (y, nm)
        r = {"year": y, "tot": t, **{b: f[b + "세"] for b in B18[:-1]}, "85+": t - f.sum()}
        assert abs(r["85+"] - o.sum()) < 0.5, (y, nm)
        r["p65"] = sum(r[b] for b in B18[13:]); r["p80"] = r["80-84"] + r["85+"]; r["p85"] = r["85+"]
        key = EXTRA.get((cw.sido_std(sido), sg), cw.make_key(sido, sg))
        if key not in PKEYS and key.endswith("군") and key[:-1] + "시" in PKEYS: key = key[:-1] + "시"
        r["key"] = NFC(key); rows.append(r)
G = pd.DataFrame(rows).groupby(["year", "key"], as_index=False)[["tot"] + B18 + ["p65", "p80", "p85"]].sum()
X = P[["year", "key", "fbd_region", "offset", "population", "cases"]].merge(G, on=["year", "key"], how="left", validate="one_to_one")
assert X.tot.notna().all(), X[X.tot.isna()][["year", "key"]]
X["pop_ratio"] = X.tot / X.population
print("[39m] 총인구 비(FBD 계 / 패널 population):", X.pop_ratio.describe()[["min", "50%", "max"]].round(4).to_dict())
assert ((X.pop_ratio - 1).abs() <= 0.01).all(), X[(X.pop_ratio - 1).abs() > 0.01][["year", "key", "population", "tot"]]
for c in ("p65", "p80", "p85"): X[c.replace("p", "pop") + "_share_raw"] = 100 * X[c] / X.tot

# ── rate·E ──
DEN = pd.DataFrame({b: X.offset * X[b] / X.tot for b in B18}); DEN["year"] = X.year.values
OUT = X[["year", "fbd_region", "cases", "pop65_share_raw", "pop80_share_raw", "pop85_share_raw"]].copy()
rs = lambda e: e * OUT.groupby("year").cases.transform("sum") / pd.Series(e, index=OUT.index).groupby(OUT.year).transform("sum")
R18 = NB / DEN.groupby("year")[B18].sum()
OUT["E_std2"] = rs((DEN[B18].values * R18.loc[X.year.values].values).sum(axis=1))
D10 = DEN[B18].T.groupby(to10).sum().T[C10]; D10["year"] = DEN.year
N10 = NB.T.groupby(to10).sum().T[C10]; R10 = N10 / D10.groupby("year")[C10].sum()
OUT["E_std_c10"] = rs((D10[C10].values * R10.loc[X.year.values].values).sum(axis=1))
nat = OUT.groupby("year").cases.sum() / X.groupby("year").offset.sum(); OUT["E_crude"] = X.offset * X.year.map(nat)
for c in ("E_std2", "E_std_c10", "E_crude"): assert (OUT.groupby("year")[c].sum() - OUT.groupby("year").cases.sum()).abs().max() < 1e-6 * OUT.cases.sum()
OUT["SIR_crude"] = OUT.cases / OUT.E_crude; OUT["SIR_std2"] = OUT.cases / OUT.E_std2; OUT["SIR_c10"] = OUT.cases / OUT.E_std_c10
save = OUT[["year", "fbd_region", "E_std2", "E_std_c10", "SIR_crude", "SIR_std2", "SIR_c10", "pop65_share_raw", "pop80_share_raw", "pop85_share_raw"]].sort_values(["year", "fbd_region"])
save.to_csv(os.path.join(ROOT, "02_패널", f"{TAG}_Estd2.csv"), index=False, encoding="utf-8-sig")
RT = R18.stack().rename("rate").reset_index().rename(columns={"band": "age"}); RT["deaths"] = NB.stack().values; RT["denom_nat"] = DEN.groupby("year")[B18].sum().stack().values   # 2026-11-06 원고 직접표준화용 분모 추가
RT.to_csv(os.path.join(ROOT, "02_패널", f"{TAG}_national_agerates_mort.csv"), index=False, encoding="utf-8-sig")

# ── 검증(선별 단계 99m E_std 와 대조 + 고령 비율과의 상관) ──
old = pd.read_csv(os.path.join(ROOT, "02_패널", f"{TAG}_Estd.csv"), encoding="utf-8-sig"); old["fbd_region"] = old.fbd_region.map(NFC)
cmp_ = OUT.merge(old[["year", "fbd_region", "E_std"]], on=["year", "fbd_region"], how="left", validate="one_to_one")
print("[39m] E_std2 / 선별 E_std(99m):", (cmp_.E_std2 / cmp_.E_std).describe()[["min", "50%", "max"]].round(4).to_dict())
Gs = OUT.groupby("fbd_region").agg(cases=("cases", "sum"), E=("E_crude", "sum"), E2=("E_std2", "sum"), E10=("E_std_c10", "sum"), o65=("pop65_share_raw", "mean"), o80=("pop80_share_raw", "mean"), o85=("pop85_share_raw", "mean"))
V = pd.DataFrame([dict(version=nm, rho_65=spearmanr(Gs.cases / Gs[c], Gs.o65)[0], rho_80=spearmanr(Gs.cases / Gs[c], Gs.o80)[0], rho_85=spearmanr(Gs.cases / Gs[c], Gs.o85)[0],
                       SIR_P90_P10=(Gs.cases / Gs[c]).quantile(.9) / (Gs.cases / Gs[c]).quantile(.1)) for nm, c in (("crude", "E"), ("c10_75plus", "E10"), ("std2_85plus", "E2"))]).round(3)
os.makedirs(os.path.join(ROOT, "04_분석", TAG, "results_std2"), exist_ok=True)
V.to_csv(os.path.join(ROOT, "04_분석", TAG, "results_std2", "S00_Estd2_validation.csv"), index=False, encoding="utf-8-sig")
print("[39m] 14년 통합 시군구 SIR – 고령 비율 Spearman:\n" + V.to_string(index=False))
print(f"[39m] 저장: 02_패널/{TAG}_Estd2.csv ({len(save)}행) · 02_패널/{TAG}_national_agerates_mort.csv")
