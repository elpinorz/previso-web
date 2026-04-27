"""
app.py — Previso Web Server
Avvia con: python app.py
Poi apri: http://localhost:8000
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from datetime import datetime, timedelta
import shutil, os, io, json

app = FastAPI(title="Previso API")
app.mount("/static", StaticFiles(directory="static"), name="static")

CSV_PATH = "ordini.csv"

# ── Utility ──────────────────────────────────────────────

def carica_df(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["date"])
    df["quantity"] = df["quantity"].astype(int)
    df["revenue"]  = df["revenue"].astype(float)
    df["month"]    = df["date"].dt.to_period("M")
    return df

# ── Analytics ────────────────────────────────────────────

def prevedi_domanda(df):
    risultati = {}
    for prodotto in df["product"].unique():
        sub = (df[df["product"] == prodotto]
               .groupby("month")["quantity"].sum().reset_index())
        sub["t"] = np.arange(len(sub))
        if len(sub) < 3:
            continue
        model = LinearRegression().fit(sub[["t"]], sub["quantity"])
        ultimo_t = sub["t"].max()
        previsioni = []
        for i in range(1, 4):
            mese_futuro = (sub["month"].max() + i).strftime("%Y-%m")
            qty = max(0, int(round(model.predict([[ultimo_t + i]])[0])))
            previsioni.append({"mese": mese_futuro, "quantita_prevista": qty})
        storico = [{"mese": str(r["month"]), "quantita": int(r["quantity"])}
                   for _, r in sub.iterrows()]
        coef = float(model.coef_[0])
        risultati[prodotto] = {
            "storico":    storico[-6:],
            "previsioni": previsioni,
            "trend":      "crescita" if coef > 0.5 else "calo" if coef < -0.5 else "stabile",
            "coef":       round(coef, 2),
        }
    return risultati

def analizza_scorte(previsioni, scorte):
    out = []
    for prodotto, dati in previsioni.items():
        if prodotto not in scorte:
            continue
        unita = scorte[prodotto]
        prossimo = dati["previsioni"][0]["quantita_prevista"] if dati["previsioni"] else 0
        vg = prossimo / 30 if prossimo > 0 else 0.1
        giorni = min(999, int(unita / vg))
        stato = "CRITICO" if giorni < 14 else "ATTENZIONE" if giorni < 30 else "OK"
        out.append({"prodotto": prodotto, "unita": unita, "giorni": giorni, "stato": stato})
    return sorted(out, key=lambda x: x["giorni"])

def prevedi_churn(df):
    ref = df["date"].max() + timedelta(days=1)
    rfm = (df.groupby("customer").agg(
        recency   = ("date",     lambda x: (ref - x.max()).days),
        frequency = ("order_id", "nunique"),
        monetary  = ("revenue",  "sum"),
    ).reset_index())
    for col in ["recency", "frequency", "monetary"]:
        mn, mx = rfm[col].min(), rfm[col].max()
        rfm[f"{col}_n"] = (rfm[col] - mn) / (mx - mn + 1e-9)
    rfm["score"] = (rfm["recency_n"] * 0.5 +
                    (1 - rfm["frequency_n"]) * 0.3 +
                    (1 - rfm["monetary_n"])  * 0.2)
    rfm["pct"] = (rfm["score"] * 100).round(0).astype(int)
    return (rfm[["customer","recency","frequency","monetary","pct"]]
            .sort_values("pct", ascending=False)
            .head(10)
            .rename(columns={"monetary":"ltv"})
            .round({"ltv": 2})
            .to_dict("records"))

def genera_raccomandazioni(df):
    basket = (df.groupby(["customer", df["date"].dt.to_period("M")])["product"]
              .apply(list).reset_index())
    coppie, conteggio_p = {}, {}
    for _, row in basket.iterrows():
        prodotti = list(set(row["product"]))
        for p in prodotti:
            conteggio_p[p] = conteggio_p.get(p, 0) + 1
        for i in range(len(prodotti)):
            for j in range(i+1, len(prodotti)):
                k = tuple(sorted([prodotti[i], prodotti[j]]))
                coppie[k] = coppie.get(k, 0) + 1
    n = len(basket)
    rec = []
    for (p1, p2), cnt in coppie.items():
        if cnt < 2:
            continue
        lift = (cnt/n) / ((conteggio_p.get(p1,1)/n) * (conteggio_p.get(p2,1)/n))
        rec.append({"prodotto_a": p1, "prodotto_b": p2,
                    "co_acquisti": cnt, "lift": round(lift, 2)})
    return sorted(rec, key=lambda x: x["lift"], reverse=True)[:5]

def metriche_generali(df):
    return {
        "ricavi_mese":   round(df[df["date"] >= df["date"].max() - timedelta(days=30)]["revenue"].sum(), 2),
        "clienti_totali": df["customer"].nunique(),
        "ordini_totali":  df["order_id"].nunique(),
        "aov":            round(df.groupby("order_id")["revenue"].sum().mean(), 2),
    }

# ── Scorte default (in produzione: dal gestionale) ───────

SCORTE_DEFAULT = {
    "Scarpe running M42":     12,
    "Zaino trekking 45L":      7,
    "Giacca impermeabile L":  31,
    "Calze tecniche":        214,
    "Borraccia termica":      89,
    "Guanti trail running":   55,
    "Cappello tecnico":       42,
    "Pantaloni trail M":      28,
}

# ── Routes ───────────────────────────────────────────────

@app.get("/")
def root():
    return FileResponse("static/index.html")

@app.get("/api/analisi")
def analisi():
    if not os.path.exists(CSV_PATH):
        raise HTTPException(404, "ordini.csv non trovato. Carica un file prima.")
    df          = carica_df(CSV_PATH)
    previsioni  = prevedi_domanda(df)
    return {
        "metriche":       metriche_generali(df),
        "previsioni":     previsioni,
        "scorte":         analizza_scorte(previsioni, SCORTE_DEFAULT),
        "churn":          prevedi_churn(df),
        "raccomandazioni":genera_raccomandazioni(df),
        "aggiornato":     datetime.now().strftime("%d/%m/%Y %H:%M"),
    }

@app.post("/api/upload")
async def upload(file: UploadFile = File(...)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(400, "Carica un file .csv")
    content = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(content), parse_dates=["date"])
        required = {"order_id","date","customer","product","price","quantity","revenue"}
        if not required.issubset(df.columns):
            raise HTTPException(400, f"Colonne mancanti: {required - set(df.columns)}")
    except Exception as e:
        raise HTTPException(400, f"Errore nel file: {str(e)}")
    with open(CSV_PATH, "wb") as f:
        f.write(content)
    return {"ok": True, "righe": len(df)}

# ── Avvio ────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    print("\n🚀 Previso avviato → http://localhost:8000\n")
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
