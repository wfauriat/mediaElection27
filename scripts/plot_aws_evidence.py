"""Plot dev/aws-evidence/daily_metrics.csv as a static SVG for the evidence README.

/opt/venvs/pyDS/bin/python scripts/plot_aws_evidence.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "dev" / "aws-evidence" / "daily_metrics.csv"
OUT = ROOT / "dev" / "aws-evidence" / "aws-activity.svg"

INK, INK2, GRID, BLUE, RED = "#0b0b0b", "#52514e", "#e1e0d9", "#2a78d6", "#d03b3b"

PANELS = [
    ("events_triggeredrules", "EventBridge cron triggers per day (schedule: 4/day)", "bar"),
    ("lambda_loader_invocations", "Loader Lambda runs per day (one per feed file)", "bar"),
    ("s3_raw_numberofobjects", "Raw feed files stored in S3", "line"),
    ("cloudfront_requests", "Dashboard requests served by CloudFront per day", "bar"),
]


def main() -> None:
    df = pd.read_csv(SRC, parse_dates=["date"]).set_index("date").sort_index()
    df = df[df.index >= "2026-05-16"]
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.size": 9,
            "axes.edgecolor": GRID,
            "axes.labelcolor": INK2,
            "xtick.color": INK2,
            "ytick.color": INK2,
        }
    )
    fig, axes = plt.subplots(len(PANELS), 1, figsize=(9, 8.2), sharex=True)
    for ax, (col, title, kind) in zip(axes, PANELS, strict=True):
        s = df[col].fillna(0)
        if kind == "bar":
            ax.bar(s.index, s.values, width=0.8, color=BLUE, linewidth=0)
        else:
            ax.plot(s.index, s.values, color=BLUE, linewidth=2)
        if col == "lambda_loader_invocations" and "lambda_loader_errors" in df:
            err = df["lambda_loader_errors"].fillna(0)
            err = err[err > 0]
            ax.scatter(
                err.index,
                [s.max() * 0.92] * len(err),
                color=RED,
                s=18,
                zorder=3,
                label=f"days with loader errors ({int(err.sum())} errors, deploy day)",
            )
            ax.legend(loc="upper right", frameon=False, fontsize=8, labelcolor=INK2)
        ax.set_title(title, loc="left", fontsize=10, color=INK, pad=4)
        ax.grid(axis="y", color=GRID, linewidth=0.8)
        ax.set_axisbelow(True)
        for side in ("top", "right", "left"):
            ax.spines[side].set_visible(False)
        ax.tick_params(length=0)
    axes[-1].xaxis.set_major_locator(mdates.MonthLocator())
    axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    fig.suptitle(
        "mediaElection27 on AWS (eu-west-3), from CloudWatch metrics",
        x=0.01,
        ha="left",
        fontsize=12,
        color=INK,
        fontweight="bold",
    )
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    fig.savefig(OUT, format="svg", metadata={"Date": None})
    if len(sys.argv) > 2 and sys.argv[1] == "--preview":
        fig.savefig(sys.argv[2], dpi=110)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
