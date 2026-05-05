#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# Portfolio Tracker — Installatie (Mac / Linux)
# Gebruik: bash install.sh
# ─────────────────────────────────────────────────────────────────────────────

set -e

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_DIR="$ROOT_DIR/app"
VENV_DIR="$APP_DIR/.venv"
PYTHON=""

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║       Portfolio Tracker Installatie      ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# ── Zoek Python 3.9+ ──────────────────────────────────────────────────────────
for cmd in python3 python3.13 python3.12 python3.11 python3.10 python3.9; do
    if command -v "$cmd" &>/dev/null; then
        if "$cmd" -c "import sys; sys.exit(0 if sys.version_info >= (3,9) else 1)" 2>/dev/null; then
            PYTHON="$cmd"
            break
        fi
    fi
done

# ── Python installeren indien niet aanwezig ────────────────────────────────────
if [ -z "$PYTHON" ]; then
    echo "⚠️   Python 3.9+ niet gevonden. Proberen te installeren..."

    OS="$(uname -s)"

    if [ "$OS" = "Darwin" ]; then
        if command -v brew &>/dev/null; then
            echo "🍺  Python installeren via Homebrew..."
            brew install python3
        else
            echo "🍺  Homebrew installeren..."
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            if [ -f /opt/homebrew/bin/brew ]; then
                eval "$(/opt/homebrew/bin/brew shellenv)"
            fi
            echo "🍺  Python installeren via Homebrew..."
            brew install python3
        fi
    elif [ "$OS" = "Linux" ]; then
        if command -v apt-get &>/dev/null; then
            sudo apt-get update -qq && sudo apt-get install -y python3 python3-venv python3-pip
        elif command -v dnf &>/dev/null; then
            sudo dnf install -y python3
        else
            echo "❌  Kan Python niet automatisch installeren."
            echo "    Installeer handmatig via: https://www.python.org/downloads/"
            exit 1
        fi
    else
        echo "❌  Onbekend OS. Installeer Python handmatig: https://www.python.org/downloads/"
        exit 1
    fi

    for cmd in python3 python3.13 python3.12 python3.11 python3.10 python3.9; do
        if command -v "$cmd" &>/dev/null; then
            if "$cmd" -c "import sys; sys.exit(0 if sys.version_info >= (3,9) else 1)" 2>/dev/null; then
                PYTHON="$cmd"
                break
            fi
        fi
    done

    if [ -z "$PYTHON" ]; then
        echo "❌  Python installatie mislukt. Installeer handmatig: https://www.python.org/downloads/"
        exit 1
    fi
fi

echo "✅  Python gevonden: $($PYTHON --version)"

# ── Virtualenv aanmaken ────────────────────────────────────────────────────────
if [ -d "$VENV_DIR" ]; then
    echo "ℹ️   Bestaande omgeving gevonden, wordt hergebruikt."
else
    echo "⚙️   Virtuele omgeving aanmaken..."
    $PYTHON -m venv "$VENV_DIR"
    echo "✅  Virtuele omgeving aangemaakt."
fi

# ── Dependencies installeren ───────────────────────────────────────────────────
echo "📦  Dependencies installeren (kan even duren)..."
"$VENV_DIR/bin/pip" install --quiet --upgrade pip
"$VENV_DIR/bin/pip" install --quiet -r "$APP_DIR/requirements.txt"
echo "✅  Alle packages geïnstalleerd."

# ── Mappen aanmaken ───────────────────────────────────────────────────────────
mkdir -p "$APP_DIR/cache" "$APP_DIR/data"

# ── Launch-script aanmaken ────────────────────────────────────────────────────
cat > "$ROOT_DIR/Portfolio Tracker starten.command" << EOF
#!/bin/bash
cd "\$(dirname "\$0")/app"
echo "🚀  Portfolio Tracker starten..."
echo "    Open je browser op: http://localhost:8501"
echo "    Stoppen: druk Ctrl+C"
echo ""
.venv/bin/streamlit run app.py --server.headless true
EOF
chmod +x "$ROOT_DIR/Portfolio Tracker starten.command"

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║       ✅  Installatie geslaagd!          ║"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "  Dubbelklik op 'Portfolio Tracker starten.command' in Finder"
echo ""
