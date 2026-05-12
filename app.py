import os
import json
import logging
from pathlib import Path
from functools import wraps

from flask import Flask, render_template, redirect, url_for, request, jsonify, abort
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from wtforms import HiddenField
from flask_talisman import Talisman

# ── Configuración de logging ──────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ── Inicialización de la app ──────────────────────────────────────────────────
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", os.urandom(32))
app.config["WTF_CSRF_TIME_LIMIT"] = 3600          # CSRF token válido 1 hora
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = os.environ.get("FLASK_ENV") == "production"

# ── CSRF Protection ───────────────────────────────────────────────────────────
csrf = CSRFProtect(app)

# ── Content Security Policy ───────────────────────────────────────────────────
csp = {
    "default-src": "'self'",
    "style-src":   ["'self'", "https://cdn.tailwindcss.com", "'unsafe-inline'"],
    "script-src":  ["'self'", "https://cdn.tailwindcss.com", "'unsafe-inline'"],
    "font-src":    ["'self'", "https://fonts.gstatic.com", "https://fonts.googleapis.com"],
    "img-src":     ["'self'", "data:"],
    "connect-src": "'self'",
    "frame-ancestors": "'none'",
}

Talisman(
    app,
    content_security_policy=csp,
    frame_options="DENY",             # Solo cambia x_frame_options por frame_options
    strict_transport_security=True,
    strict_transport_security_max_age=31536000,
    referrer_policy="no-referrer",
    force_https=False,               # Render maneja HTTPS externamente
)

# ── Ruta y helpers de métricas ────────────────────────────────────────────────
METRICS_PATH = Path("data/metrics.json")

def _load_metrics() -> dict:
    METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)
    if METRICS_PATH.exists():
        try:
            return json.loads(METRICS_PATH.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {"total_scans": 0, "vulnerable_clicks": 0}

def _save_metrics(metrics: dict) -> None:
    METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)
    METRICS_PATH.write_text(json.dumps(metrics, indent=2))

def _increment(key: str) -> dict:
    metrics = _load_metrics()
    metrics[key] = metrics.get(key, 0) + 1
    _save_metrics(metrics)
    return metrics

# ── Formulario WTForms (solo lleva el token CSRF) ────────────────────────────
class SurveyForm(FlaskForm):
    """
    Formulario minimalista: WTForms gestiona el token CSRF automáticamente.
    NO almacenamos nombre ni DNI — Privacidad por Diseño.
    """
    pass

# ── Protección del dashboard admin ───────────────────────────────────────────
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "vmt-secret-2026")

def require_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.args.get("token") or request.headers.get("X-Admin-Token", "")
        if token != ADMIN_TOKEN:
            abort(403)
        return f(*args, **kwargs)
    return decorated

# ── Rutas ─────────────────────────────────────────────────────────────────────

@app.route("/ping")
def ping():
    """Ruta para Cron-job / UptimeRobot. 
    Mantiene la app despierta sin afectar las métricas de visitas reales."""
    return "OK", 200

@app.route("/")
def index():
    """
    Página principal del quishing. Registra un escaneo/visita.
    PRIVACIDAD: solo incrementa contador, nunca guarda IP ni datos personales.
    """
    _increment("total_scans")
    form = SurveyForm()
    return render_template("index.html", form=form)


@app.route('/submit', methods=['POST'])
@csrf.exempt # Esto quita la protección para que el clic entre sí o sí
def submit():
    """
    Registra el clic vulnerable sin pedir tokens.
    """
    # Quitamos la validación del form porque el @csrf.exempt ya hace el trabajo
    _increment("vulnerable_clicks")
    logger.info("¡Clic vulnerable registrado con éxito!")
    return redirect(url_for("leccion"))


@app.route("/leccion")
def leccion():
    return render_template("leccion.html")


@app.route("/admin-metrics-vmt")
@require_admin
def admin_metrics():
    metrics = _load_metrics()
    scans   = metrics.get("total_scans", 0)
    clicks  = metrics.get("vulnerable_clicks", 0)
    pct     = round((clicks / scans * 100), 1) if scans > 0 else 0.0
    return render_template(
        "admin.html",
        total_scans=scans,
        vulnerable_clicks=clicks,
        vulnerability_pct=pct,
    )


@app.route("/admin-metrics-vmt/api")
@require_admin
def admin_metrics_api():
    """Endpoint JSON para el dashboard en tiempo real."""
    metrics = _load_metrics()
    scans   = metrics.get("total_scans", 0)
    clicks  = metrics.get("vulnerable_clicks", 0)
    pct     = round((clicks / scans * 100), 1) if scans > 0 else 0.0
    return jsonify(total_scans=scans, vulnerable_clicks=clicks, vulnerability_pct=pct)


# ── Punto de entrada (dev) ────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)
