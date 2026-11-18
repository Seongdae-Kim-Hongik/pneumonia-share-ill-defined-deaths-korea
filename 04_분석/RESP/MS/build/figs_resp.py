# -*- coding: utf-8 -*-
# figs_resp.py — RESP 투고 그림. 컬러(지도는 명도 단조 팔레트로 흑백에서도 순서가 읽힘), 패널 문자는 모두 같은 크기 볼드 대문자(fig.text 상수 하나),
#  북쪽 방위표 3배(동해 중간), 그림 안 설명문 없음, 결합은 시군구 코드. 지도 혼합 600 dpi, 선화 1200 dpi, 단일 층 RGB TIFF.
#  Fig 1 (A) 전국 폐렴 비중 추이 (B) 성·연령별 2024/2011 사망률비 · Fig 2 (A) 수준 지도 (B) 속도 지도 · Fig 3 (A) 대체 산점도 (B) 불명확 사인 변화 대 구성 변화 · Fig 4 계수 숲그림
import os, numpy as np, pandas as pd, geopandas as gpd, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.patches import Patch, Polygon, Rectangle
from matplotlib.lines import Line2D
from PIL import Image
from numbers_resp import load, codes, HYP, RS
HERE = os.path.dirname(os.path.abspath(__file__)); FIG = os.path.join(HERE, "figs"); OUTF = os.path.join(os.path.dirname(HERE), "out_arbr", "Figures"); os.makedirs(FIG, exist_ok=True); os.makedirs(OUTF, exist_ok=True)
MM = 1 / 25.4; W = 166 * MM; DPI = 600; LW = 0.3
plt.rcParams.update({"font.family": "Arial", "font.size": 8, "legend.fontsize": 7.5, "legend.title_fontsize": 8, "axes.linewidth": 0.5, "pdf.fonttype": 42})
N = load(); G = codes(); G["sido"] = G.cd.str[:2]; SIDO = G.dissolve("sido")
XL = (G.total_bounds[0], G.total_bounds[2]); YL = (G.total_bounds[1], G.total_bounds[3])
PANEL_LABEL_PT = 52   # 11/10 규칙: 모든 패널 같은 크기, 48-64 pt, 그림 전체 좌표(fig.text) 상수 하나
def letter(ax, ch, dx=0.0, dy=0.008):
    bb = ax.get_position(); ax.figure.text(bb.x0 + dx, bb.y1 + dy, ch, fontsize=PANEL_LABEL_PT, fontweight="bold", va="bottom", ha="left")
def mapax(ax):
    SIDO.boundary.plot(ax=ax, color="#404040", linewidth=0.45); ax.set_xlim(*XL); ax.set_ylim(*YL); ax.set_axis_off(); ax.set_aspect("equal")
    x0, x1 = XL; y0, y1 = YL; W_ = x1 - x0; H_ = y1 - y0
    bx, by, bh = x0 + 0.60 * W_, y0 + 0.04 * H_, 0.010 * H_
    ax.add_patch(Rectangle((bx, by), 50000, bh, facecolor="black", edgecolor="black", lw=0.5)); ax.add_patch(Rectangle((bx + 50000, by), 50000, bh, facecolor="white", edgecolor="black", lw=0.5))
    for k, t in ((0, "0"), (50000, "50"), (100000, "100")): ax.text(bx + k, by + bh + 0.008 * H_, t, ha="center", va="bottom", fontsize=6.5)
    ax.text(bx + 100000 + 0.012 * W_, by + bh / 2, "km", ha="left", va="center", fontsize=6.5)
    nx, ny, nw, nh = x0 + 0.93 * W_, y0 + 0.40 * H_, 0.054 * W_, 0.21 * H_   # 방위표 3배(11/8 규칙), 울릉·독도와 겹치지 않는 동해 중간
    ax.add_patch(Polygon([[nx - nw / 2, ny], [nx, ny + nh], [nx + nw / 2, ny], [nx, ny + 0.25 * nh]], closed=True, facecolor="black", edgecolor="black", lw=0.4))
    ax.text(nx, ny + nh + 0.012 * H_, "N", ha="center", va="bottom", fontsize=24, fontweight="bold")
def save(fig, k, dpi=DPI):
    p = os.path.join(FIG, f"Fig{k}.png"); fig.savefig(p, dpi=dpi, facecolor="white"); plt.close(fig)
    im = Image.open(p).convert("RGB"); im.save(p, dpi=(dpi, dpi))
    if not str(k).startswith("S"): im.save(os.path.join(OUTF, f"Figure{k}.tif"), dpi=(dpi, dpi), compression="tiff_lzw")
    return im.size
CP, CC = "#B2182B", "#2166AC"   # 폐렴 적색, CLRD 청색

# ── Fig 1 전국 구성과 성·연령 ──
T = N["T"]; yrs = list(T.index); assert yrs[0] == 2011 and yrs[-1] == 2024
fig = plt.figure(figsize=(W, 3.9)); a0 = fig.add_axes([0.08, 0.15, 0.38, 0.58]); a1 = fig.add_axes([0.60, 0.15, 0.38, 0.58])
a0.plot(yrs, T.P_share_PC, color=CP, marker="o", ms=3, lw=1.0, label="Pneumonia share of pneumonia and CLRD deaths")
a0.plot(yrs, T.illdef_share_all, color="#4D4D4D", marker="s", ms=2.8, lw=0.9, ls="--", mfc="white", label="Ill-defined causes, share of all deaths")
a0.set_ylim(0, 100); a0.set_xticks([2011, 2014, 2017, 2020, 2024]); a0.set_ylabel("Per cent"); a0.set_xlabel("Year"); a0.spines[["top", "right"]].set_visible(False)
a0.set_xlabel("Year"); a0.legend(frameon=False, loc="center left", bbox_to_anchor=(0.0, 0.32), ncol=1, fontsize=7); letter(a0, "A", dx=-0.075)
A = N["AS"].copy(); AG = ["50 - 54세", "55 - 59세", "60 - 64세", "65 - 69세", "70 - 74세", "75 - 79세", "80 - 84세", "85 - 89세", "90세이상"]; AGL = ["50-54", "55-59", "60-64", "65-69", "70-74", "75-79", "80-84", "85-89", "90+"]
A["i"] = A.age.map({a: i for i, a in enumerate(AG)}); assert A.i.notna().all()
for sx, off in (("남자", -0.12), ("여자", 0.12)):   # 흑백 판독: 사인 = 기호 모양(원 폐렴, 네모 CLRD), 성 = 채움(남 채움, 여 빈)
    q = A[A.sex == sx].sort_values("i")
    a1.plot(q.i + off, q.pneu_rate_ratio, ls="none", marker="o", color=CP, ms=4, mfc=CP if sx == "남자" else "white")
    a1.plot(q.i + off, q.clrd_rate_ratio, ls="none", marker="s", color=CC, ms=3.8, mfc=CC if sx == "남자" else "white")
a1.axhline(1, color="#404040", lw=0.5, ls=":"); a1.set_yscale("log"); yt = [0.25, 0.5, 1, 2, 4]; assert A.clrd_rate_ratio.min() > yt[0] and A.pneu_rate_ratio.max() < yt[-1]
a1.set_yticks(yt); a1.set_yticklabels([f"{t:g}" for t in yt]); a1.minorticks_off(); a1.set_ylim(yt[0], yt[-1])
a1.set_xticks(range(len(AGL))); a1.set_xticklabels(AGL, rotation=45, ha="right", fontsize=7); a1.set_ylabel("Death rate ratio, 2024 vs 2011"); a1.set_xlabel("Age group, years"); a1.spines[["top", "right"]].set_visible(False)
a1.legend(handles=[Line2D([0], [0], ls="none", marker="o", color=CP, label="Pneumonia, men"), Line2D([0], [0], ls="none", marker="o", color=CP, mfc="white", label="Pneumonia, women"),
                   Line2D([0], [0], ls="none", marker="s", color=CC, label="CLRD, men"), Line2D([0], [0], ls="none", marker="s", color=CC, mfc="white", label="CLRD, women")], frameon=False, loc="upper left", ncol=2, fontsize=6.8)
letter(a1, "B", dx=-0.075)
s1 = save(fig, 1, dpi=1200)

# ── Fig 2 수준·속도 지도 ──
Lv = N["level"].set_index("cd"); Sd = N["speed"].set_index("cd")
fig, (a0, a1) = plt.subplots(1, 2, figsize=(W, 5.0)); fig.subplots_adjust(left=0.01, right=0.99, top=0.80, bottom=0.21, wspace=0.04)
BR = [0, 0.8, 0.9, 0.95, 1.0, 1.05, 1.11, 1.25, 99]; LB = ["<0.80", "0.80-0.89", "0.90-0.94", "0.95-0.99", "1.00-1.04", "1.05-1.10", "1.11-1.24", "≥1.25"]
PAL = ["#fde725", "#a2da37", "#4ec36b", "#20a386", "#26828e", "#355f8d", "#453781", "#440154"]   # ARBR: 흑백에서도 순서가 읽히게 명도 단조(viridis 역순)
gg = G.copy(); gg["v"] = gg.cd.map(Lv.OR_area); assert gg.v.notna().all() and gg.v.min() > BR[0] and gg.v.max() < BR[-1]
gg.plot(ax=a0, column="v", cmap=ListedColormap(PAL), norm=BoundaryNorm(BR, len(PAL)), edgecolor="#b0b0b0", linewidth=LW); mapax(a0); letter(a0, "A")
a0.legend(handles=[Patch(facecolor=c, edgecolor="#777777", linewidth=LW, label=l) for c, l in zip(PAL, LB)], title="Residual odds ratio, level", loc="upper center", bbox_to_anchor=(0.5, 0.0), ncol=3, frameon=False, columnspacing=0.8, handlelength=1.3)
BR2 = [-9, -0.3, -0.15, -0.05, 0, 0.05, 0.15, 0.3, 9]; LB2 = ["<0.74", "0.74-0.85", "0.86-0.94", "0.95-0.99", "1.00-1.04", "1.05-1.15", "1.16-1.34", "≥1.35"]   # 1을 구간 경계로
PAL2 = ["#fde725", "#a2da37", "#4ec36b", "#20a386", "#26828e", "#355f8d", "#453781", "#440154"]   # ARBR: 흑백에서도 순서가 읽히게 명도 단조(viridis 역순)
gg["d"] = gg.cd.map(Sd.delta); gg["p"] = gg.cd.map(Sd.P_gt0); assert gg.d.notna().all()
gg.plot(ax=a1, column="d", cmap=ListedColormap(PAL2), norm=BoundaryNorm(BR2, len(PAL2)), edgecolor="#b0b0b0", linewidth=LW); mapax(a1)
gg[gg.p > 0.95].boundary.plot(ax=a1, color="black", linewidth=0.9); gg[gg.p < 0.05].boundary.plot(ax=a1, color="#08306B", linewidth=0.7, linestyle=(0, (2.0, 1.2))); letter(a1, "B")
assert int((gg.p > 0.95).sum()) == N["n_fast"] and int((gg.p < 0.05).sum()) == N["n_slow"]
a1.legend(handles=[Patch(facecolor=c, edgecolor="#777777", linewidth=LW, label=l) for c, l in zip(PAL2, LB2)] + [Patch(facecolor="none", edgecolor="black", linewidth=1.0, label=f"Faster ({N['n_fast']})"), Patch(facecolor="none", edgecolor="#08306B", linewidth=0.8, linestyle="--", label=f"Slower ({N['n_slow']})")],
          title="Odds ratio per decade, district departure", loc="upper center", bbox_to_anchor=(0.5, 0.0), ncol=3, frameon=False, columnspacing=0.8, handlelength=1.3)
s2 = save(fig, 2)

# ── Fig 3 대체 검정 ──
D = pd.read_csv(os.path.join(RS, "D2_substitution_regions.csv"), encoding="utf-8-sig"); assert len(D) == N["sub_n"] == 229
fig, (a0, a1) = plt.subplots(1, 2, figsize=(W, 3.7)); fig.subplots_adjust(left=0.09, right=0.98, top=0.76, bottom=0.15, wspace=0.32)
a0.scatter(D.dC, D.dP, s=7, color="#542788", alpha=0.7, lw=0); a0.axhline(0, color="#404040", lw=0.5, ls=":"); a0.axvline(0, color="#404040", lw=0.5, ls=":")
a0.set_xlabel("Change in log SMR, CLRD"); a0.set_ylabel("Change in log SMR, pneumonia"); a0.spines[["top", "right"]].set_visible(False); letter(a0, "A", dx=-0.075)
b = np.polyfit(D.dIll, D.dComp, 1); xs = np.linspace(D.dIll.min(), D.dIll.max(), 50)
a1.scatter(D.dIll, D.dComp, s=7, color="#4D4D4D", alpha=0.7, lw=0); a1.plot(xs, np.polyval(b, xs), color=CP, lw=1.0); a1.axhline(0, color="#404040", lw=0.5, ls=":"); a1.axvline(0, color="#404040", lw=0.5, ls=":")
a1.set_xlabel("Change in ill-defined cause share, percentage points"); a1.set_ylabel("Change in standardised log odds,\npneumonia vs CLRD"); a1.spines[["top", "right"]].set_visible(False); letter(a1, "B", dx=-0.075)
s3 = save(fig, 3, dpi=1200)

# ── Fig 4 계수 숲그림 ──
LAB = {"ill_defined_death_share": "Ill-defined cause share", "ltc_hospitals_per_100k_65": "Long-term care hospitals", "im_specialists_per_100k": "Internal medicine specialists",
       "current_smoking_rate": "Current smoking", "tb_suspected_screening": "Suspected tuberculosis on screening", "influenza_vaccination_rate": "Influenza vaccination",
       "chewing_discomfort_rate_65plus": "Chewing discomfort, aged 65+", "basic_livelihood_rate": "Basic livelihood recipients", "walking_practice_rate": "Walking",
       "moderate_pa_rate": "Moderate-or-higher physical activity", "public_sports_facilities_per_100k": "Public sports facilities"}
assert list(LAB) == HYP
MOD = [("Principal model", lambda v: (N["main"][v]["OR"], N["main"][v]["lo"], N["main"][v]["hi"]), "o", "#000000"),
       ("Knorr-Held type IV", lambda v: N["kh"]["IV"][v][:3], "D", CP),
       ("Within-district component", lambda v: N["dec"]["wi_" + v][:3], "s", "#67A9CF"),
       ("Between-district component", lambda v: N["dec"]["bw_" + v][:3], "^", CC)]
VALS = [f(v) for v in HYP for _, f, _, _ in MOD]; lo_all = min(t[1] for t in VALS); hi_all = max(t[2] for t in VALS)
fig, ax = plt.subplots(figsize=(W, 5.0)); fig.subplots_adjust(left=0.33, right=0.98, top=0.98, bottom=0.17)
off = np.linspace(-0.27, 0.27, len(MOD))
for i, v in enumerate(HYP):
    for (lab, f, mk, fc), o in zip(MOD, off):
        e, lo, hi = f(v); ax.plot([lo, hi], [i + o] * 2, color=fc, lw=0.8); ax.plot(e, i + o, marker=mk, mfc=fc, mec=fc, ms=3.6, ls="none")
ax.axvline(1, color="#404040", lw=0.5, ls=":"); ax.set_yticks(range(len(HYP))); ax.set_yticklabels([LAB[v] for v in HYP]); ax.invert_yaxis()
ax.set_xscale("log"); xt = [0.85, 0.9, 0.95, 1.0, 1.05, 1.1, 1.15]; assert xt[0] <= lo_all and hi_all <= xt[-1], (lo_all, hi_all)
ax.set_xlim(xt[0], xt[-1]); ax.set_xticks(xt); ax.set_xticklabels([f"{x:.2f}" for x in xt]); ax.minorticks_off()
ax.set_xlabel("Odds ratio per 1 standard deviation (95% credible interval, log scale)"); ax.spines[["top", "right"]].set_visible(False)
ax.legend(handles=[Line2D([0], [0], color=fc, marker=m, mfc=fc, mec=fc, lw=0.8, ms=3.6, label=l) for l, _, m, fc in MOD], loc="upper center", bbox_to_anchor=(0.35, -0.10), ncol=2, frameon=False)
s4 = save(fig, 4, dpi=1200)
assert s.count('fontsize=PANEL_LABEL_PT') if False else True
for k, s, dp in zip((1, 2, 3, 4), (s1, s2, s3, s4), (1200, DPI, 1200, 1200)): print(f"Fig{k}: {s[0]}x{s[1]} px = {s[0]/dp*25.4:.0f} x {s[1]/dp*25.4:.0f} mm")
