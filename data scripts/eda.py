"""Create reproducible exploratory figures from the raw release and cleaned sample."""
import json
import os
from pathlib import Path
os.environ.setdefault("MPLCONFIGDIR", str(Path(__file__).resolve().parents[1] / "tmp/matplotlib"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from source_io import ROOT


def main():
    data = pd.read_csv(ROOT / "data/processed/development_sample.csv")
    audit = json.loads((ROOT / "reports/evidence/data_audit.json").read_text())
    out = ROOT / "reports/figures"
    out.mkdir(parents=True,exist_ok=True)
    plt.rcParams.update({"font.family":"DejaVu Sans", "font.size":10,
                         "axes.spines.top":False,"axes.spines.right":False,
                         "figure.facecolor":"white","axes.titleweight":"bold"})
    colors = ["#357782", "#de9053"]
    counts = [audit["raw_return_counts"]["0"],audit["raw_return_counts"]["1"]]
    fig,ax=plt.subplots(figsize=(7,3.6))
    bars=ax.bar(["Kept (0)","Returned (1)"],counts,color=colors,width=0.55)
    ax.bar_label(bars,labels=[f"{n:,} ({n/sum(counts):.1%})" for n in counts],padding=5)
    ax.set(ylim=(0,max(counts)*1.22),ylabel="Purchase events",title="Raw ASOS training release: return outcomes")
    ax.ticklabel_format(axis="y",style="plain")
    fig.tight_layout(); fig.savefig(out/"class_distribution.png",dpi=180); plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(9,3.4))
    for ax,column,title in zip(axes,["avgGbpPrice","avgDiscountValue"],["Average product price (GBP)","Average product discount (source units)"]):
        values=data[column].dropna(); limit=values.quantile(.99)
        ax.hist(values[values<=limit],bins=40,color=colors[0],edgecolor="white",linewidth=.3)
        ax.set(title=title,xlabel="Value (top 1% omitted from display)",ylabel="Sample events")
    fig.tight_layout();fig.savefig(out/"price_discount.png",dpi=180);plt.close(fig)
    fig,ax=plt.subplots(figsize=(7,3.8))
    rates=data.groupby("productType").isReturned.agg(["mean","size"]).sort_values("mean")
    ax.barh(rates.index,rates["mean"],color=colors[0])
    ax.set(xlim=(0,1),xlabel="Observed return fraction",title="Return frequency by anonymized product type")
    fig.tight_layout();fig.savefig(out/"product_return_rates.png",dpi=180);plt.close(fig)
    columns=["avgGbpPrice","avgDiscountValue","premier","isReturned"]
    corr=data[columns].corr()
    fig,ax=plt.subplots(figsize=(6,4))
    im=ax.imshow(corr,vmin=-1,vmax=1,cmap="BrBG")
    labels=["Avg. price","Avg. discount","Premier","Returned"]
    ax.set_xticks(range(4),labels,rotation=20,ha="right"); ax.set_yticks(range(4),labels)
    for i in range(4):
        for j in range(4): ax.text(j,i,f"{corr.iloc[i,j]:.2f}",ha="center",va="center",color="white" if abs(corr.iloc[i,j])>.65 else "black")
    ax.set_title("Pearson correlations in the development sample")
    fig.colorbar(im,ax=ax,shrink=.8);fig.tight_layout();fig.savefig(out/"correlations.png",dpi=180);plt.close(fig)
    country=data.groupby("shippingCountry").isReturned.agg(["mean","size"]).sort_index()
    fig,ax=plt.subplots(figsize=(7,3.5))
    ax.bar(country.index,country["mean"],color=colors[0])
    ax.set(ylim=(0,1),ylabel="Observed return fraction",title="Descriptive country audit (not model fairness)")
    ax.tick_params(axis="x",rotation=35)
    fig.tight_layout();fig.savefig(out/"country_audit.png",dpi=180);plt.close(fig)
    summary={"sample_rows":len(data),"product_type_rates":rates.reset_index().to_dict(orient="records"),
             "country_rates":country.reset_index().to_dict(orient="records"),
             "correlations":corr.to_dict(),"numerical_summary":data[["avgGbpPrice","avgDiscountValue"]].describe().to_dict()}
    (ROOT/"reports/evidence/eda_summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    print("Saved five figures and reports/evidence/eda_summary.json")


if __name__ == "__main__":
    main()
