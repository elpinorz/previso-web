"""
genera_dati.py — crea ordini.csv di esempio per testare Previso.
Esegui UNA volta prima di avviare app.py
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

random.seed(42); np.random.seed(42)

PRODOTTI = [
    ("Scarpe running M42", 49.90), ("Zaino trekking 45L", 89.90),
    ("Giacca impermeabile L", 129.90), ("Calze tecniche", 9.90),
    ("Borraccia termica", 24.90), ("Guanti trail running", 19.90),
    ("Cappello tecnico", 14.90), ("Pantaloni trail M", 59.90),
]
CLIENTI = [
    "marco.rossi@email.it","giulia.verdi@email.it","luca.bianchi@email.it",
    "sara.ferrari@email.it","antonio.mele@email.it","chiara.russo@email.it",
    "davide.conti@email.it","elena.marino@email.it","francesco.greco@email.it",
    "valentina.ricci@email.it","matteo.colombo@email.it","federica.lombardi@email.it",
]
AFFINITA = {
    "Giacca impermeabile L":  ["Calze tecniche","Zaino trekking 45L"],
    "Zaino trekking 45L":     ["Borraccia termica","Cappello tecnico"],
    "Scarpe running M42":     ["Calze tecniche","Guanti trail running"],
    "Pantaloni trail M":      ["Guanti trail running","Cappello tecnico"],
}
ordini = []
data_inizio = datetime(2025, 1, 1)
data_fine   = datetime(2026, 3, 31)
for cliente in CLIENTI:
    if cliente in ["marco.rossi@email.it","giulia.verdi@email.it","luca.bianchi@email.it"]:
        ultima = data_fine - timedelta(days=random.randint(35,60))
    elif cliente in ["sara.ferrari@email.it","antonio.mele@email.it"]:
        ultima = data_fine - timedelta(days=random.randint(20,35))
    else:
        ultima = data_fine - timedelta(days=random.randint(1,15))
    for _ in range(random.randint(3,12)):
        data = ultima - timedelta(days=random.randint(0,365))
        if data < data_inizio: data = data_inizio + timedelta(days=random.randint(0,30))
        nome, prezzo = random.choice(PRODOTTI)
        qty = random.randint(1,3)
        ordini.append({"order_id":f"ORD{len(ordini)+1:05d}","date":data.strftime("%Y-%m-%d"),
                       "customer":cliente,"product":nome,"price":prezzo,"quantity":qty,"revenue":round(prezzo*qty,2)})
        if nome in AFFINITA and random.random()<0.4:
            nc = random.choice(AFFINITA[nome])
            pc = next(p for n,p in PRODOTTI if n==nc)
            ordini.append({"order_id":f"ORD{len(ordini)+1:05d}","date":data.strftime("%Y-%m-%d"),
                           "customer":cliente,"product":nc,"price":pc,"quantity":1,"revenue":pc})
df = pd.DataFrame(ordini).sort_values("date").reset_index(drop=True)
df.to_csv("ordini.csv", index=False)
print(f"✓ Generati {len(df)} ordini per {len(CLIENTI)} clienti → ordini.csv")
