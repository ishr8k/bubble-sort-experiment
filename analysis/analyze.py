"""
Analysis of the bubble sort experiment (Assignment 1).

Only techniques from the lectures are used:
  * five-number summary (min, Q1, median, Q3, max), mean, standard deviation   (Lecture 05)
  * 95% confidence interval of the mean: m -/+ z * S / sqrt(N), z = 1.96       (Lecture 07)
  * box plots / line plots with labelled axes and units, reduced precision     (Lecture 01, 05)

Run from the project root:  python3 analysis/analyze.py
Input : data/raw_measurements.csv
Output: data/summary_statistics.csv, figures/*.png and a text report on stdout.
"""
import math
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import seaborn as sns

Z_95 = 1.96  # z value for the 95% confidence level (z-table)
ALGOS = ["PassPerItem", "UntilNoChange", "WhileNeeded"]
ORDERS = ["sorted", "nearly_sorted", "random", "reversed"]
ORDER_LABEL = {"sorted": "sorted", "nearly_sorted": "nearly sorted", "random": "random", "reversed": "reversed"}
SIZES = [100, 1000, 10000]
PALETTE = dict(zip(ALGOS, ["#d95f02", "#7570b3", "#1b9e77"]))


def sig3(x):
    """Format with 3 significant digits (precision reduced to what is meaningful)."""
    if x == 0:
        return "0"
    decimals = max(0, 2 - int(math.floor(math.log10(abs(x)))))
    return f"{x:,.{decimals}f}"


def load():
    d = pd.read_csv("data/raw_measurements.csv")
    d["ms"] = d["time_ns"] / 1e6  # nanoseconds -> milliseconds
    return d


def summarise(d):
    rows = []
    for (size, order, algo), g in d.groupby(["size", "order", "algorithm"]):
        x = g["ms"].to_numpy()
        n = len(x)
        m = x.mean()
        s = x.std(ddof=0)  # standard deviation as defined in the lecture (divide by N)
        half = Z_95 * s / math.sqrt(n)
        q1, med, q3 = np.percentile(x, [25, 50, 75])
        rows.append(dict(size=size, order=order, algorithm=algo, N=n, min=x.min(), q1=q1, median=med,
                         q3=q3, max=x.max(), mean=m, sd=s, ci_low=m - half, ci_high=m + half))
    return pd.DataFrame(rows)


def overlap(a, b):
    return not (a.ci_high < b.ci_low or b.ci_high < a.ci_low)


# ------------------------------------------------------------------ figures

def fig_boxplots(d):
    """Box plots per input size. Sorted input (differences of several orders of magnitude) is drawn on a
    log scale in the left column; the other three input orders are drawn on a linear scale on the right."""
    sns.set_theme(style="whitegrid", font_scale=0.9)
    fig, axes = plt.subplots(3, 2, figsize=(7.2, 8.8), gridspec_kw={"width_ratios": [1, 2.3]})
    dd = d.copy()
    dd["input order"] = dd["order"].map(ORDER_LABEL)
    for row, size in enumerate(SIZES):
        for col, (orders, log) in enumerate([(["sorted"], True), (["nearly_sorted", "random", "reversed"], False)]):
            ax = axes[row, col]
            sub = dd[(dd["size"] == size) & (dd["order"].isin(orders))]
            sns.boxplot(data=sub, x="input order", y="ms", hue="algorithm", hue_order=ALGOS,
                        order=[ORDER_LABEL[o] for o in orders], palette=PALETTE, ax=ax, linewidth=0.8,
                        fliersize=2)
            if log:
                ax.set_yscale("log")
                ax.set_ylabel("Execution time (ms, log scale)")
            else:
                ax.set_ylim(bottom=0)
                ax.set_ylabel("Execution time (ms)")
            ax.set_title(f"n = {size:,}", loc="left", fontsize=10)
            ax.set_xlabel("Initial order of the input")
            ax.get_legend().remove()
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=3, frameon=False, title="Algorithm")
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig("figures/fig2_boxplots.png", dpi=200)
    plt.close(fig)


def fig_lines(summary):
    sns.set_theme(style="whitegrid", font_scale=0.9)
    fig, axes = plt.subplots(2, 2, figsize=(7.2, 6.0))
    for ax, order in zip(axes.ravel(), ORDERS):
        for algo in ALGOS:
            s = summary[(summary["order"] == order) & (summary["algorithm"] == algo)].sort_values("size")
            yerr = [s["mean"] - s["ci_low"], s["ci_high"] - s["mean"]]
            ax.errorbar(s["size"], s["mean"], yerr=yerr, marker="o", capsize=3, color=PALETTE[algo],
                        label=algo, linewidth=1.3)
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xticks(SIZES)
        ax.set_xticklabels([f"{s:,}" for s in SIZES])
        ax.set_title(f"{ORDER_LABEL[order]} input", loc="left", fontsize=10)
        ax.set_xlabel("Input size n (log scale)")
        ax.set_ylabel("Mean time (ms, log scale)")
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=3, frameon=False, title="Algorithm")
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    fig.savefig("figures/fig3_scaling.png", dpi=200)
    plt.close(fig)


def fig_design():
    fig, ax = plt.subplots(figsize=(7.2, 4.3))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 60)
    ax.axis("off")

    def box(x, y, w, h, text, fc="#f2f2f2", ec="#444444", fs=8, bold=False):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.3,rounding_size=1.2", fc=fc, ec=ec, lw=1))
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs,
                fontweight="bold" if bold else "normal", linespacing=1.35)

    def arrow(x1, y1, x2, y2):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle="-|>", color="#444444", lw=1.2))

    # column titles
    ax.text(15, 58, "Independent variables", ha="center", fontsize=9, fontweight="bold")
    ax.text(50, 58, "One trial (360 in total)", ha="center", fontsize=9, fontweight="bold")
    ax.text(85, 58, "Dependent variable", ha="center", fontsize=9, fontweight="bold")

    # factors
    box(1, 40, 28, 14, "Input size\n100 | 1,000 | 10,000", fc="#e8f0fa")
    box(1, 22, 28, 14, "Initial order\nrandom | sorted |\nreversed | nearly sorted", fc="#e8f0fa")
    box(1, 4, 28, 14, "Algorithm\nUntilNoChange | WhileNeeded |\nPassPerItem", fc="#fdebd9")
    ax.text(15, 0.3, "full factorial: 3 x 3 x 4 = 36 conditions", ha="center", fontsize=7.5, style="italic")

    # trial
    box(37, 38, 26, 16, "1) generate ONE input array\n(size x order, seeded,\nrepetition 1..30)", fc="#e8f0fa")
    box(37, 8, 26, 26, "2) every algorithm sorts its own\ncopy of that same array,\nin Latin-square order:\n\nrow 1:  U  W  P\nrow 2:  W  P  U\nrow 3:  P  U  W\n(each row used 10 x per condition)",
        fc="#fdebd9", fs=7.3)
    arrow(50, 38, 50, 35)
    ax.text(50, 4.5, "U = UntilNoChange, W = WhileNeeded,\nP = PassPerItem. Trials run in random order.",
            ha="center", fontsize=6.8, style="italic")

    # DV
    box(72, 24, 27, 16, "3) time of sort() only\nSystem.nanoTime()\nratio scale, reported in ms", fc="#e6f4ea")
    ax.text(85.5, 18, "within-subjects design:\nsame input for all\nthree algorithms", ha="center", fontsize=7.2, style="italic")

    arrow(29.5, 47, 36.5, 46)
    arrow(29.5, 29, 36.5, 40)
    arrow(29.5, 11, 36.5, 20)
    arrow(63.5, 21, 71.5, 30)

    fig.tight_layout()
    fig.savefig("figures/fig1_design.png", dpi=200)
    plt.close(fig)


# ------------------------------------------------------------------ main

def main():
    d = load()
    summary = summarise(d)
    summary.to_csv("data/summary_statistics.csv", index=False)

    # integrity checks
    assert (summary["N"] == 30).all() and len(summary) == 36
    assert d.groupby(["size", "order", "algorithm", "position"]).size().min() > 0

    fig_design()
    fig_boxplots(d)
    fig_lines(summary)

    S = {(r.size, r.order, r.algorithm): r for r in summary.itertuples()}

    print("=== Descriptive statistics (ms) ===")
    pd.set_option("display.width", 220)
    pd.set_option("display.max_rows", 200)
    tmp = summary.copy()
    for c in ["min", "q1", "median", "q3", "max", "mean", "ci_low", "ci_high"]:
        tmp[c] = tmp[c].map(sig3)
    print(tmp[["size", "order", "algorithm", "min", "q1", "median", "q3", "max", "mean", "ci_low", "ci_high"]]
          .to_string(index=False))

    print("\n=== H1: sorted input -- UntilNoChange / WhileNeeded vs PassPerItem ===")
    for size in SIZES:
        p = S[(size, "sorted", "PassPerItem")]
        for a in ["UntilNoChange", "WhileNeeded"]:
            x = S[(size, "sorted", a)]
            print(f"n={size:>6} {a:14s} median {sig3(x.median):>8} vs PassPerItem {sig3(p.median):>8}  "
                  f"ratio {p.median / x.median:8.1f}x  CIs overlap: {overlap(x, p)}")
        u, w = S[(size, "sorted", "UntilNoChange")], S[(size, "sorted", "WhileNeeded")]
        print(f"          Until vs While on sorted: CIs overlap: {overlap(u, w)} "
              f"(means {sig3(u.mean)} vs {sig3(w.mean)})")

    print("\n=== H2: WhileNeeded vs UntilNoChange (random, reversed), and PassPerItem vs UntilNoChange (reversed) ===")
    for order in ["random", "reversed", "nearly_sorted"]:
        for size in SIZES:
            u, w, p = (S[(size, order, a)] for a in ["UntilNoChange", "WhileNeeded", "PassPerItem"])
            print(f"{order:13s} n={size:>6}: While<Until? {w.ci_high < u.ci_low} (median ratio U/W {u.median / w.median:4.2f}) | "
                  f"Pass vs Until overlap: {overlap(p, u)} (median ratio U/P {u.median / p.median:4.2f}) | "
                  f"While vs Pass overlap: {overlap(w, p)} (ratio P/W {p.median / w.median:4.2f})")

    print("\n=== H3: is WhileNeeded ever significantly slower than another algorithm? ===")
    slower = 0
    for size in SIZES:
        for order in ORDERS:
            w = S[(size, order, "WhileNeeded")]
            for a in ["UntilNoChange", "PassPerItem"]:
                o = S[(size, order, a)]
                if w.ci_low > o.ci_high:
                    slower += 1
                    print("WhileNeeded slower:", size, order, a)
    print("number of conditions where WhileNeeded's CI lies entirely above another algorithm's CI:", slower)
    print("fastest (lowest median) per condition:")
    for size in SIZES:
        for order in ORDERS:
            best = min(ALGOS, key=lambda a: S[(size, order, a)].median)
            tie = [a for a in ALGOS if a != best and overlap(S[(size, order, a)], S[(size, order, best)])]
            print(f"  n={size:>6} {order:13s} -> {best}" + (f"  (CI overlaps with {tie})" if tie else ""))

    print("\n=== H4: growth of the median when size grows 10x ===")
    for order in ORDERS:
        for a in ALGOS:
            r1 = S[(1000, order, a)].median / S[(100, order, a)].median
            r2 = S[(10000, order, a)].median / S[(1000, order, a)].median
            print(f"{order:13s} {a:14s}  100->1,000: x{r1:7.1f}   1,000->10,000: x{r2:7.1f}")

    print("\n=== Validity checks ===")
    d["rel"] = d["ms"] / d.groupby(["size", "order", "algorithm"])["ms"].transform("median")
    print("median relative time (time / median of its condition) by Latin-square position:")
    print(d.groupby("position")["rel"].median().round(3).to_string())
    print(d.groupby(["size", "position"])["rel"].median().unstack().round(3).to_string())
    d["half"] = np.where(d["trial"] <= 180, "first half", "second half")
    print("by experiment half:")
    print(d.groupby(["size", "half"])["rel"].median().unstack().round(3).to_string())
    print("max relative time (largest outlier / median):", round(d["rel"].max(), 2))
    # share of boxplot outliers (beyond 1.5 IQR)
    cnt = 0
    for (size, order, algo), g in d.groupby(["size", "order", "algorithm"]):
        q1, q3 = np.percentile(g["ms"], [25, 75])
        iqr = q3 - q1
        cnt += ((g["ms"] > q3 + 1.5 * iqr) | (g["ms"] < q1 - 1.5 * iqr)).sum()
    print(f"observations flagged as box-plot outliers: {cnt} of {len(d)} ({100 * cnt / len(d):.1f}%)")
    # mean vs median
    summary["mean_over_median"] = summary["mean"] / summary["median"]
    print("mean/median ratio: min %.2f max %.2f" % (summary["mean_over_median"].min(), summary["mean_over_median"].max()))
    print("CI half-width / mean (max): %.3f" % (((summary["ci_high"] - summary["ci_low"]) / 2 / summary["mean"]).max()))


if __name__ == "__main__":
    main()
