# Portfolio Tracker — CLAUDE.md

## Opstarten

```bash
python3 -m streamlit run app.py
# → http://localhost:8501
```

**Dependencies installeren (eenmalig):**
```bash
python3 -m pip install -r requirements.txt
```

---

## Wat de app doet

Lokale portfolio tracker voor DEGIRO. Upload een CSV-export van je transacties en krijg:

- **5 scorecards**: portfoliowaarde, rendement (tijdsframe), CAGR, vs S&P 500, winst in €
- **Tab 1 – Portfoliowaarde**: lijngrafieken waarde vs geïnvesteerd kapitaal
- **Tab 2 – vs S&P 500**: beide genormaliseerd naar 100 op dag 1 van het tijdsframe
- **Tab 3 – Verdeling**: donut chart per positie

Tijdsframes: 1M / 3M / 6M / YTD / 1Y / 3Y / 5Y / Alles (via sidebar).

---

## DEGIRO import-formaat

Exporteer via: **Activiteiten → Transacties → Exporteer (CSV)**

Het nieuwe DEGIRO-formaat (2024+) heeft deze kolommen:

| Kolom | Inhoud |
|---|---|
| Datum | DD-MM-YYYY |
| Tijd | HH:MM |
| Product | Naam aandeel |
| ISIN | ISIN-code |
| Beurs | Exchange code (NDQ, NSY, EAM, XET, …) |
| Uitvoeringsplaats | Venue |
| Aantal | Positief = koop, negatief = verkoop |
| Koers | Aandeelprijs |
| *(unnamed)* | Valuta (USD/EUR/…) |
| Lokale waarde | Waarde in lokale valuta |
| *(unnamed)* | EUR-kolom |
| Waarde EUR | Bedrag in EUR (negatief=koop, positief=verkoop) |
| Wisselkoers | FX-rate |
| … | Kosten |
| Order ID | Unieke order-ID |

**Koop/verkoop** wordt bepaald door het teken van `Aantal`, niet een tekst-label.
**EUR-bedrag** komt uit `Waarde EUR` (exclusief kosten). Het oude formaat met `Omschrijving: "Koop 10 @ 185,92 USD"` wordt ook herkend — de parser detecteert automatisch welk formaat het is.

---

## Berekeningen

### Netto geïnvesteerd kapitaal
```
netto_geïnvesteerd = som(alle aankopen EUR) − som(alle verkopen EUR)
```
Gebaseerd op alle transacties, ook die zonder oplosbare ticker.

### Portfoliowaarde (dagelijks)
Per dag: voor elke positie `aandelen × koers_in_EUR`, gesommeerd.
Koersen worden via yfinance opgehaald en omgezet naar EUR (FX via `USDEUR=X` etc.).
GBp (pence) wordt automatisch gedeeld door 100 voor de EUR-conversie.

### All-time rendement
```
rendement = (portfoliowaarde / netto_geïnvesteerd) − 1
```
Gebruikt geïnvesteerd kapitaal als basis — dag-1 portfoliowaarde is niet bruikbaar omdat het portfolio dan nog maar 2-3 posities bevat.

### Tijdsframe-rendement — Modified Dietz
Voor periodes met nieuwe stortingen (1M t/m 5Y) wordt **Modified Dietz** gebruikt:

```
rendement = (V_eind − V_begin − Netto_CF) / (V_begin + Gewogen_CF)
```

Waarbij elke storting gewogen wordt op basis van hoe vroeg in de periode hij viel:
```
gewicht = (dagen_tot_einde_periode / totale_periode_dagen)
```

Een storting op dag 1 telt volledig mee als "startkapitaal" (gewicht=1).
Een storting halverwege telt voor de helft (gewicht=0.5).
Zo worden rendementen niet opgeblazen door nieuwe stortingen.

**Verschil naïef vs Modified Dietz (1Y in onze data):**
- Naïef: +150% (inclusief €9.6k netto storting in dat jaar)
- Modified Dietz: +80% (correct, gecorrigeerd voor stortingen)

### CAGR
```
CAGR = (1 + rendement) ^ (1 / jaren) − 1
```
Voor "Alles": `jaren = (vandaag − eerste_transactiedatum) / 365.25`

### S&P 500 vergelijking
- Simpele procentuele verandering `^GSPC` over hetzelfde tijdsframe
- Beide lijnen genormaliseerd naar 100 op de eerste gemeenschappelijke handelsdag
- Groen vlak = portfolio boven S&P 500

### Ongerealiseerde P&L
```
ongerealiseerd = Σ (aandelen × huidige_prijs_EUR − kostprijs_EUR)
```
Alleen voor posities met bekende huidige prijs. Posities zonder oplosbare ticker worden overgeslagen (anders trekken ze de P&L kunstmatig omlaag met hun kostprijs).

---

## Bestandsstructuur

```
portfolio-tracker/
├── install.sh / install.bat  # installatie (eenmalig uitvoeren)
├── start.sh / start.bat      # app starten (aangemaakt na installatie)
├── README.md
├── CLAUDE.md                 # dit bestand
└── app/                      # interne bestanden
    ├── app.py                # Streamlit entry point
    ├── requirements.txt
    ├── src/
    │   ├── parser.py         # DEGIRO CSV parser (nieuw + oud formaat)
    │   ├── ticker_resolver.py# ISIN + Beurs → yfinance ticker via OpenFIGI
    │   ├── prices.py         # koersen ophalen, EUR-conversie, parquet cache
    │   ├── portfolio.py      # posities (FIFO), history, Modified Dietz, metrics
    │   └── charts.py         # Plotly charts (dark theme)
    ├── cache/
    │   ├── ticker_map_auto.json      # automatisch opgeloste ISIN→ticker mappings
    │   ├── ticker_map_override.json  # handmatige correcties (prioriteit boven auto)
    │   └── px_*.parquet              # gecachede koersdata per ticker
    └── data/
        ├── last_upload.csv       # laatste geüploade CSV (automatisch opgeslagen)
        └── last_upload_meta.json # bestandsnaam + datum van upload
```

---

## Ticker-resolutie

DEGIRO-exports bevatten geen ticker-symbolen, alleen ISIN + Beurs-code.

**Stap 1 – OpenFIGI API** (gratis, geen key):
- ISIN + Beurs-code → OpenFIGI `exchCode` mapping
- Beurs NDQ → OpenFIGI `UW` (NASDAQ), NSY → `UN` (NYSE), EAM → `NA` (Amsterdam), enz.
- Resultaat geprobed met yfinance: als `history(period="5d")` niet leeg → correct

**Stap 2 – Handmatige override**:
- In de app invullen in het gele waarschuwingsvak
- Opgeslagen in `cache/ticker_map_override.json`
- Override wint altijd van de automatische resolutie

**Bekende valkuilen OpenFIGI:**
- `NTFX` i.p.v. `NFLX` (Netflix) → handmatig gecorrigeerd via override
- `REIT` i.p.v. `NNN` (NNN REIT) → handmatig gecorrigeerd
- `Z` i.p.v. `ZS` (Zscaler) → handmatig gecorrigeerd
- `TE` i.p.v. `TTE` (TotalEnergies) → handmatig gecorrigeerd
- `None`-entries worden bij elke opstart opgeruimd zodat ze opnieuw geprobeerd worden

---

## Data persistentie

- Geüploade CSV wordt automatisch opgeslagen in `data/last_upload.csv`
- Bij herstart laadt de app automatisch de laatste upload — geen re-upload nodig
- Koersdata gecacht als parquet in `cache/px_*.parquet` (verloopt na 20 uur)
- Knop "Prijzen verversen" in de sidebar wist de parquet-cache

---

## Bekende beperkingen

- **GBp vs GBP**: Londense aandelen worden door yfinance soms in pence (GBp) gerapporteerd. De `prices.py` laag deelt deze automatisch door 100.
- Koersen zijn vertraagd (yfinance free tier).
