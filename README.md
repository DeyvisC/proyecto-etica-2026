# Quishing Demo — LimaSur Insights
### Experimento educativo · Curso Ética en Tecnología

## Estructura del proyecto

```
quishing-demo/
├── app.py                     # Backend Flask
├── Procfile                   # Para Render / Heroku
├── requirements.txt
├── data/
│   └── metrics.json           # Creado automáticamente (NO versionar)
└── templates/
    ├── index.html             # Página del quishing (encuesta ficticia)
    ├── leccion.html           # Página educativa post-clic
    └── admin.html             # Dashboard de métricas
```

---

## Variables de entorno (Render → Environment)

| Variable       | Descripción                             | Ejemplo               |
|----------------|-----------------------------------------|-----------------------|
| `SECRET_KEY`   | Clave secreta Flask (CSRF)              | cadena aleatoria 32+  |
| `ADMIN_TOKEN`  | Token para acceder al dashboard admin   | `mi-token-secreto`    |
| `FLASK_ENV`    | `production` activa cookies Secure      | `production`          |

> En Render, ve a **Environment → Add Environment Variable**.

---

## Ejecución local

```bash
pip install -r requirements.txt
export SECRET_KEY="dev-secret-local"
export ADMIN_TOKEN="vmt-admin"
python app.py
```

Visita: `http://localhost:5000`

---

## Despliegue en Render

1. Sube el proyecto a GitHub.
2. En Render → **New Web Service** → conecta el repo.
3. Build command: `pip install -r requirements.txt`
4. Start command: *(Render detecta el Procfile automáticamente)*
5. Añade las variables de entorno indicadas arriba.

---

## Rutas del sistema

| Ruta                           | Descripción                          |
|--------------------------------|--------------------------------------|
| `GET /`                        | Encuesta (incrementa `total_scans`)  |
| `POST /submit`                 | Botón trampa (requiere CSRF válido)  |
| `GET /leccion`                 | Página educativa                     |
| `GET /admin-metrics-vmt`       | Dashboard (requiere `?token=...`)    |
| `GET /admin-metrics-vmt/api`   | JSON de métricas (mismo token)       |

---

## Privacidad por Diseño

- El backend **nunca lee ni almacena** `nombre` ni `dni`.
- Solo incrementa contadores en `data/metrics.json`.
- No hay logs de IPs individuales.
- CSRF activo en todos los formularios POST.

---

## Nota ética

Este sistema fue creado exclusivamente con fines educativos para demostrar
vulnerabilidades cognitivas ante ataques de Quishing.
**Usar fuera del contexto académico autorizado puede constituir un delito** bajo
la Ley N.° 30096 (Ley de Delitos Informáticos del Perú).
