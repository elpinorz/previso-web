# Previso — Web App

Dashboard analytics predittivo per PMI e-commerce italiane.

## Avvio rapido

```bash
# 1. Installa dipendenze (una volta sola)
pip install -r requirements.txt

# 2. Genera dati di test (una volta sola)
python genera_dati.py

# 3. Avvia il server
python app.py

# 4. Apri il browser su:
#    http://localhost:8000
```

## Usare i tuoi dati reali

Carica il tuo CSV direttamente dal dashboard (pulsante in basso a sinistra).

Il CSV deve avere queste colonne:

| Colonna  | Esempio              |
|----------|----------------------|
| order_id | ORD00001             |
| date     | 2025-03-15           |
| customer | mario.rossi@email.it |
| product  | Scarpe running M42   |
| price    | 49.90                |
| quantity | 2                    |
| revenue  | 99.80                |

## Struttura progetto

```
previso_web/
├── app.py           ← Server FastAPI (backend)
├── genera_dati.py   ← Genera CSV di test
├── requirements.txt
├── ordini.csv       ← Creato da genera_dati.py
└── static/
    └── index.html   ← Dashboard (frontend)
```
