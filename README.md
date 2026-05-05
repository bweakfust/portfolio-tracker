# Portfolio Tracker

Lokale portfolio tracker voor DEGIRO. Upload je transactie-CSV en bekijk rendement, CAGR en vergelijking met de S&P 500.

---

## Installatie

### Stap 1 — Installeer de app

**Mac / Linux** — open Terminal in deze map en run:
```bash
bash install.sh
```

**Windows** — dubbelklik op `install.bat`

> Python wordt automatisch geïnstalleerd als het nog niet aanwezig is.

---

### Stap 2 — Exporteer je DEGIRO-transacties

1. Log in op [degiro.nl](https://www.degiro.nl)
2. Ga naar **Activiteiten → Transacties**
3. Selecteer een zo breed mogelijke periode (vanaf je eerste transactie)
4. Klik **Exporteer** → kies **CSV**

---

### Stap 3 — Start de app

**Mac / Linux:** dubbelklik op `start.sh`
**Windows:** dubbelklik op `start.bat`

De app opent op [http://localhost:8501](http://localhost:8501)

---

### Stap 4 — Upload je CSV

Klik op **"Blader door bestanden"** en selecteer het geëxporteerde DEGIRO-bestand.
De app onthoudt je laatste upload — bij de volgende opstart hoef je niet opnieuw te uploaden.

---

## Tips

- **Koersen verversen:** sidebar → "Prijzen verversen"
- **Opnieuw starten:** altijd via `start.sh` of `start.bat`, geen herinstallatie nodig
