#!/usr/bin/env bash
# Instalador de la Bolsa de Empleo Tizayuca (macOS y Linux).
#
# Uso:
#   ./instalar.sh             instala y deja el servicio web activo
#   ./instalar.sh --detener   detiene el servicio web
#
# Si se ejecuta dentro del repositorio ya descargado, usa esos archivos; si se ejecuta solo
# (por ejemplo copiado a un servidor vacío), descarga el código fuente desde GitHub.
#
# Variables opcionales: PUERTO (8000), DESTINO (./BolsaEmpleoTizayuca), REPO_URL,
# DJANGO_ALLOWED_HOSTS (por defecto localhost, 127.0.0.1 y los nombres/IP de esta máquina).
set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/UTVAM-Software/2026-III-Bolsa-de-Empleo-Tizayuca.git}"
PUERTO="${PUERTO:-8000}"
AQUI="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"

if [ -f "$AQUI/manage.py" ]; then
    RAIZ="$AQUI"; SRC="$AQUI"; MODO="repositorio"
else
    RAIZ="${DESTINO:-$PWD/BolsaEmpleoTizayuca}"; SRC="$RAIZ/codigo"; MODO="descarga"
fi
PIDFILE="$RAIZ/.servidor.pid"
LOG="$RAIZ/servidor.log"

paso() { printf '\n\033[1m[%s/5] %s\033[0m\n' "$1" "$2"; }
fallo() { printf '\n\033[31mERROR: %s\033[0m\n' "$1" >&2; exit 1; }

detener_servidor() {
    if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
        kill "$(cat "$PIDFILE")" 2>/dev/null || true
        echo "Servicio web detenido (PID $(cat "$PIDFILE"))."
    fi
    rm -f "$PIDFILE"
}

if [ "${1:-}" = "--detener" ]; then
    detener_servidor
    exit 0
fi

# Python 3.12 o superior (lo pide Django 6)
PYTHON=""
for candidato in python3.14 python3.13 python3.12 python3; do
    if command -v "$candidato" >/dev/null 2>&1 \
       && "$candidato" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 12) else 1)' 2>/dev/null; then
        PYTHON="$candidato"; break
    fi
done
[ -n "$PYTHON" ] || fallo "Se necesita Python 3.12 o superior (python3 --version)."

# ---------------------------------------------------------------------------
paso 1 "Crear el ambiente virtual"
mkdir -p "$RAIZ"
detener_servidor                      # por si hay una instalación anterior corriendo
if [ ! -x "$RAIZ/.venv/bin/python" ]; then
    "$PYTHON" -m venv "$RAIZ/.venv" \
        || fallo "No se pudo crear el ambiente virtual (en Debian/Ubuntu: sudo apt install python3-venv)."
fi
VPY="$RAIZ/.venv/bin/python"
echo "Ambiente virtual en $RAIZ/.venv"

# ---------------------------------------------------------------------------
paso 2 "Descargar los archivos de código fuente"
if [ "$MODO" = "repositorio" ]; then
    echo "Se usan los archivos del repositorio en $SRC"
    if [ -d "$SRC/.git" ] && command -v git >/dev/null 2>&1; then
        git -C "$SRC" pull --ff-only >/dev/null 2>&1 || echo "(sin cambios nuevos que descargar)"
    fi
else
    command -v git >/dev/null 2>&1 || fallo "Se necesita git para descargar el código fuente."
    if [ -d "$SRC/.git" ]; then
        git -C "$SRC" pull --ff-only || fallo "No se pudo actualizar el código fuente."
    else
        git clone --depth 1 "$REPO_URL" "$SRC" || fallo "No se pudo descargar $REPO_URL"
    fi
fi
cd "$SRC"
[ -f manage.py ] || fallo "No se encontró manage.py en $SRC"

# ---------------------------------------------------------------------------
paso 3 "Configurar la base de datos y los usuarios"
"$VPY" -m pip install --quiet --disable-pip-version-check -r requirements.txt \
    || fallo "No se pudieron instalar las dependencias (requirements.txt)."
"$VPY" manage.py migrate --noinput >/dev/null || fallo "Falló la creación de la base de datos."
"$VPY" manage.py preparar_entorno || fallo "Falló la creación de roles y usuarios."
if "$VPY" manage.py shell -c "import sys; from vacantes.models import Vacante; sys.exit(0 if Vacante.objects.exists() else 1)" >/dev/null 2>&1; then
    echo "Ya hay vacantes en la base de datos; no se agregan datos de ejemplo."
else
    "$VPY" manage.py poblar_vacantes --cantidad 100 >/dev/null && echo "Se cargaron 100 vacantes de ejemplo."
fi

# ---------------------------------------------------------------------------
paso 4 "Instalar las herramientas propias de Django"
"$VPY" manage.py check || fallo "La revisión de Django encontró problemas."
"$VPY" manage.py makemigrations --check --dry-run >/dev/null || fallo "Hay migraciones pendientes de generar."
echo "Django $("$VPY" -m django --version): configuración y migraciones correctas."

# ---------------------------------------------------------------------------
paso 5 "Activar el servicio web"
puerto_libre() {
    "$VPY" -c "import socket,sys
s = socket.socket(); s.settimeout(1)
sys.exit(1 if s.connect_ex(('127.0.0.1', int(sys.argv[1]))) == 0 else 0)" "$1"
}
while ! puerto_libre "$PUERTO"; do
    echo "El puerto $PUERTO está ocupado, se prueba el siguiente."
    PUERTO=$((PUERTO + 1))
done
if [ -z "${DJANGO_ALLOWED_HOSTS:-}" ]; then
    DJANGO_ALLOWED_HOSTS="$("$VPY" - <<'PY'
import socket
hosts = {'localhost', '127.0.0.1'}
try:
    nombre = socket.gethostname()
    hosts.add(nombre)
    hosts.update(i[4][0] for i in socket.getaddrinfo(nombre, None, socket.AF_INET))
except OSError:
    pass
print(','.join(sorted(hosts)))
PY
)"
fi
export DJANGO_ALLOWED_HOSTS
nohup "$VPY" manage.py runserver "0.0.0.0:$PUERTO" --noreload >"$LOG" 2>&1 &
echo $! >"$PIDFILE"

LISTO=0
for _ in $(seq 1 30); do
    if "$VPY" -c "import sys,urllib.request
sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:$PUERTO/', timeout=2).status == 200 else 1)" 2>/dev/null; then
        LISTO=1; break
    fi
    kill -0 "$(cat "$PIDFILE")" 2>/dev/null || break
    sleep 1
done
if [ "$LISTO" -ne 1 ]; then
    tail -n 20 "$LOG" >&2 || true
    detener_servidor
    fallo "El servicio web no respondió. Revisa $LOG"
fi

if [ "$MODO" = "repositorio" ]; then DETENER="./instalar.sh --detener"; else DETENER="DESTINO=$RAIZ $AQUI/instalar.sh --detener"; fi

cat <<FIN

Instalación terminada. El servicio web está activo (PID $(cat "$PIDFILE")).

  Sitio:          http://127.0.0.1:$PUERTO
  Iniciar sesión: http://127.0.0.1:$PUERTO/cuentas/login/
  Administrador:  admin@example.com   /  Tizayuca.2026
  Solo lectura:   profesor@example.com / Tizayuca.2026
  Detener:        $DETENER
  Registro:       $LOG
FIN
