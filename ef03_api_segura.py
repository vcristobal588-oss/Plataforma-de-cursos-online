"""EF03 - Integrante 1: consumo seguro de una API externa.

Proyecto: EcoTech Solutions - Plataforma de cursos online
Asignatura: TI3021 - Programacion Orientada a Objeto Seguro

Flujo del prototipo:
1. Carga configuracion y secretos desde variables de entorno (3.1.2.I.7).
2. Autentica con usuario + contrasena contra un hash bcrypt (3.1.2.I.5).
3. Crea una sesion con tiempo maximo de validez (3.1.2.I.8).
4. Valida la moneda ingresada antes de usarla en la URL (3.1.2.I.6).
5. Consulta la API con timeout y maneja red/HTTP/JSON (3.1.3.I.9-I.12).
6. Extrae solo los campos necesarios y verifica tipos/consistencia
   (3.1.1.I.2-I.4).

API usada: https://open.er-api.com/v6/latest/{MONEDA}
No requiere API key. Si se usa otro proveedor, la clave se toma de
ECOTECH_API_KEY y se envia en el header X-API-Key.

Configuracion en PowerShell (usar comillas simples para el hash):
    $env:ECOTECH_USER = "integrante1"
    $env:ECOTECH_USER_HASH = '<hash bcrypt>'
    $env:ECOTECH_MONEDA_DESTINO = "CLP"   # opcional, por defecto CLP
    python ef03_api_segura.py

Generar un hash bcrypt:
    python -c "import bcrypt; print(bcrypt.hashpw(b'MiClaveSegura', bcrypt.gensalt()).decode())"

Requisitos: Python 3.10+, requests, bcrypt.
"""
import getpass
import hmac
import math
import os
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone

import bcrypt
import requests


# ---------------------------------------------------------------------------
# Reglas y constantes del prototipo
# ---------------------------------------------------------------------------
# Usuario: solo letras, numeros, punto, guion y guion bajo (sin espacios ni
# simbolos que puedan alterar una consulta).
PATRON_USUARIO = re.compile(r"^[A-Za-z0-9_.-]{3,30}$")

# Moneda: exactamente tres letras. Se usa luego en la ruta de la URL.
PATRON_MONEDA = re.compile(r"^[A-Za-z]{3}$")

# Hash bcrypt valido: $2a$ / $2b$ / $2y$, costo de 2 digitos y 53 caracteres.
PATRON_HASH_BCRYPT = re.compile(r"^\$2[aby]\$\d{2}\$[./A-Za-z0-9]{53}$")

# (timeout de conexion, timeout de lectura) en segundos.
TIEMPO_ESPERA = (3.05, 5)

# La sesion vence a los 5 minutos; la consulta se hace inmediatamente, pero
# el control existe para cumplir el criterio de sesion.
DURACION_SESION = 300

# bcrypt solo considera los primeros 72 bytes de la contrasena.
MAX_BYTES_CONTRASENA = 72


# ---------------------------------------------------------------------------
# Excepciones propias: separan los fallos esperados de los errores de codigo
# ---------------------------------------------------------------------------
class ErrorEcoTech(Exception):
    """Error base del prototipo. Sus mensajes son seguros para el usuario."""


class ErrorConfiguracion(ErrorEcoTech):
    """Falta una variable de entorno o tiene un formato invalido."""


class ErrorAutenticacion(ErrorEcoTech):
    """Credenciales incorrectas."""


class ErrorSesion(ErrorEcoTech):
    """La sesion no existe o ya expiro."""


class ErrorValidacion(ErrorEcoTech):
    """Una entrada del usuario no cumple el formato permitido."""


class ErrorApi(ErrorEcoTech):
    """Fallo controlado al consultar o interpretar la API externa."""


# ---------------------------------------------------------------------------
# Estructuras de datos
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Configuracion:
    """Configuracion leida desde el entorno; no contiene secretos en el codigo."""

    usuario: str
    hash_contrasena: str
    api_url: str
    api_key: str | None
    moneda_destino: str


@dataclass
class Sesion:
    """Sesion minima: usuario autenticado + instante de creacion."""

    usuario: str
    autenticada: bool = False
    duracion_seg: int = DURACION_SESION
    inicio: float = field(default_factory=time.monotonic, repr=False)

    def activa(self) -> bool:
        """True solo si fue autenticada y no se cumplio el tiempo maximo."""
        return self.autenticada and (
            (time.monotonic() - self.inicio) < self.duracion_seg
        )


@dataclass(frozen=True)
class TipoCambio:
    """Solo los datos que el prototipo necesita mostrar."""

    origen: str
    destino: str
    tasa: float
    actualizado: datetime


# ---------------------------------------------------------------------------
# Configuracion y secretos
# ---------------------------------------------------------------------------
def cargar_configuracion() -> Configuracion:
    """Lee secretos y configuracion desde variables de entorno (3.1.2.I.7)."""
    usuario = (os.getenv("ECOTECH_USER") or "").strip()
    hash_contrasena = (os.getenv("ECOTECH_USER_HASH") or "").strip()
    api_url = (
        os.getenv("ECOTECH_API_URL") or "https://open.er-api.com/v6/latest"
    ).strip().rstrip("/")
    api_key = (os.getenv("ECOTECH_API_KEY") or "").strip() or None
    moneda_destino = (os.getenv("ECOTECH_MONEDA_DESTINO") or "CLP").strip().upper()

    # Sin usuario ni hash no se puede autenticar: se aborta con mensaje claro.
    if not usuario or not hash_contrasena:
        raise ErrorConfiguracion(
            "Defina ECOTECH_USER y ECOTECH_USER_HASH como variables de entorno."
        )

    if not PATRON_USUARIO.fullmatch(usuario):
        raise ErrorConfiguracion(
            "ECOTECH_USER debe tener entre 3 y 30 caracteres: letras, numeros, "
            "punto, guion o guion bajo."
        )

    if not PATRON_HASH_BCRYPT.fullmatch(hash_contrasena):
        raise ErrorConfiguracion(
            "ECOTECH_USER_HASH no tiene el formato de un hash bcrypt valido."
        )

    # La API debe viajar por HTTPS para proteger la consulta y la clave.
    if not api_url.startswith("https://"):
        raise ErrorConfiguracion("ECOTECH_API_URL debe comenzar con https://.")

    if not PATRON_MONEDA.fullmatch(moneda_destino):
        raise ErrorConfiguracion(
            "ECOTECH_MONEDA_DESTINO debe tener exactamente 3 letras (ej: CLP)."
        )

    return Configuracion(
        usuario=usuario,
        hash_contrasena=hash_contrasena,
        api_url=api_url,
        api_key=api_key,
        moneda_destino=moneda_destino,
    )


# ---------------------------------------------------------------------------
# Validacion y saneamiento de entradas
# ---------------------------------------------------------------------------
def validar_credenciales(usuario: str, contrasena: str) -> str:
    """Valida formato de usuario y longitud de contrasena (3.1.2.I.6)."""
    usuario = (usuario or "").strip()

    if not PATRON_USUARIO.fullmatch(usuario):
        raise ErrorValidacion(
            "El usuario debe tener entre 3 y 30 caracteres: letras, numeros, "
            "punto, guion o guion bajo."
        )

    if not contrasena:
        raise ErrorValidacion("La contrasena no puede estar vacia.")

    if len(contrasena.encode("utf-8")) > MAX_BYTES_CONTRASENA:
        raise ErrorValidacion(
            f"La contrasena no puede superar los {MAX_BYTES_CONTRASENA} bytes."
        )

    return usuario


def validar_moneda(valor: str) -> str:
    """Normaliza y valida una moneda de 3 letras (3.1.2.I.6)."""
    texto = (valor or "").strip().upper()

    if not PATRON_MONEDA.fullmatch(texto):
        raise ErrorValidacion(
            "La moneda debe tener exactamente 3 letras (ej: USD)."
        )

    return texto


# ---------------------------------------------------------------------------
# Autenticacion y sesion
# ---------------------------------------------------------------------------
def autenticar(usuario: str, contrasena: str, config: Configuracion) -> Sesion:
    """Compara la contrasena contra el hash bcrypt y crea una sesion."""
    try:
        usuario = validar_credenciales(usuario, contrasena)
    except ErrorValidacion as error:
        # No se revela si el usuario existe o si el formato fue el problema.
        raise ErrorAutenticacion("Usuario o contrasena incorrectos.") from error

    # compare_digest evita comparaciones vulnerables a diferencias de tiempo.
    usuario_ok = hmac.compare_digest(
        usuario.encode("utf-8"), config.usuario.encode("utf-8")
    )

    try:
        # checkpw vuelve a hashear la clave ingresada con el salt del hash.
        clave_ok = bcrypt.checkpw(
            contrasena.encode("utf-8"),
            config.hash_contrasena.encode("utf-8"),
        )
    except ValueError as error:
        raise ErrorConfiguracion(
            "ECOTECH_USER_HASH no es un hash bcrypt valido."
        ) from error

    if not (usuario_ok and clave_ok):
        # Mensaje unico: no se informa cual de los dos datos fallo.
        raise ErrorAutenticacion("Usuario o contrasena incorrectos.")

    return Sesion(usuario=config.usuario, autenticada=True)


def exigir_sesion_activa(sesion: Sesion) -> None:
    """Corta el flujo si la sesion expiro (3.1.2.I.8)."""
    if not sesion.activa():
        raise ErrorSesion(
            "La sesion no es valida o expiro. Vuelva a iniciar sesion."
        )


# ---------------------------------------------------------------------------
# Consumo de la API externa
# ---------------------------------------------------------------------------
def construir_url(config: Configuracion, moneda_origen: str) -> str:
    """Arma la URL con una moneda ya validada (solo letras A-Z)."""
    return f"{config.api_url}/{moneda_origen}"


def _mensaje_http(codigo: int) -> str:
    """Traduce codigos HTTP a mensajes claros, sin mostrar el cuerpo tecnico."""
    mensajes = {
        400: "La API rechazo la solicitud (400).",
        401: "La API rechazo la autenticacion (401).",
        403: "La API denego el acceso (403).",
        404: "La API no encontro el recurso solicitado (404).",
        408: "La API agoto el tiempo de espera (408).",
        429: "Se alcanzo el limite de consultas (429). Intente mas tarde.",
    }

    if codigo in mensajes:
        return mensajes[codigo]

    if 300 <= codigo <= 399:
        return (
            "La API intento redirigir la solicitud; por seguridad no se siguio."
        )

    if 500 <= codigo <= 599:
        return "La API no esta disponible en este momento (error del servidor)."

    return f"La API respondio con un codigo inesperado ({codigo})."


def extraer_tipo_cambio(
    datos: dict, moneda_origen: str, moneda_destino: str
) -> TipoCambio:
    """Extrae y valida solo los campos necesarios del JSON (3.1.1.I.3-I.4)."""
    if not isinstance(datos, dict):
        raise ErrorApi("La API devolvio un JSON con una estructura inesperada.")

    if datos.get("result") != "success":
        raise ErrorApi("La API no pudo entregar el tipo de cambio solicitado.")

    # Consistencia: la API debe confirmar la misma moneda que se solicito.
    if datos.get("base_code") != moneda_origen:
        raise ErrorApi("La API devolvio una moneda base distinta a la solicitada.")

    tasas = datos.get("rates")
    if not isinstance(tasas, dict):
        raise ErrorApi("La API no devolvio la lista de tipos de cambio.")

    tasa = tasas.get(moneda_destino)

    # bool es subclase de int: se excluye para no aceptar True/False como tasa.
    if isinstance(tasa, bool) or not isinstance(tasa, (int, float)):
        raise ErrorApi(f"No hay un tipo de cambio disponible para {moneda_destino}.")

    tasa = float(tasa)

    # Una tasa debe ser un numero finito y mayor que cero.
    if not math.isfinite(tasa) or tasa <= 0:
        raise ErrorApi("La API devolvio un tipo de cambio invalido.")

    marca_tiempo = datos.get("time_last_update_unix")
    if (
        isinstance(marca_tiempo, bool)
        or not isinstance(marca_tiempo, int)
        or marca_tiempo <= 0
    ):
        raise ErrorApi("La API no devolvio una fecha de actualizacion valida.")

    try:
        actualizado = datetime.fromtimestamp(marca_tiempo, tz=timezone.utc)
    except (OverflowError, OSError, ValueError) as error:
        raise ErrorApi("La fecha de actualizacion de la API no es valida.") from error

    return TipoCambio(
        origen=moneda_origen,
        destino=moneda_destino,
        tasa=tasa,
        actualizado=actualizado,
    )


def consultar_tipo_cambio(
    sesion: Sesion, moneda_origen: str, config: Configuracion
) -> TipoCambio:
    """Consulta la API solo si hay sesion activa (3.1.2.I.8)."""
    exigir_sesion_activa(sesion)

    # Se revalida aunque main ya lo haya hecho: defensa en profundidad.
    moneda_origen = validar_moneda(moneda_origen)

    url = construir_url(config, moneda_origen)
    headers = {"Accept": "application/json"}

    # La API de ejemplo no usa clave; el header queda listo para otro proveedor.
    if config.api_key:
        headers["X-API-Key"] = config.api_key

    try:
        # No se siguen redirecciones: evita enviar la API key a otro destino.
        respuesta = requests.get(
            url,
            headers=headers,
            timeout=TIEMPO_ESPERA,
            allow_redirects=False,
        )
    except requests.exceptions.Timeout as error:
        raise ErrorApi(
            "La API tardo demasiado en responder. Intente nuevamente."
        ) from error
    except requests.exceptions.SSLError as error:
        raise ErrorApi(
            "No se pudo establecer una conexion segura con la API."
        ) from error
    except requests.exceptions.ConnectionError as error:
        raise ErrorApi(
            "No se pudo conectar con la API. Verifique su conexion a Internet."
        ) from error
    except requests.exceptions.RequestException as error:
        raise ErrorApi("No se pudo completar la consulta a la API.") from error

    # Cualquier respuesta distinta de 200 se traduce a un mensaje seguro.
    if respuesta.status_code != 200:
        raise ErrorApi(_mensaje_http(respuesta.status_code))

    try:
        datos = respuesta.json()
    except ValueError as error:
        # requests lanza JSONDecodeError (subclase de ValueError) si no es JSON.
        raise ErrorApi("La API devolvio una respuesta que no es JSON valido.") from error

    return extraer_tipo_cambio(datos, moneda_origen, config.moneda_destino)


# ---------------------------------------------------------------------------
# Flujo principal
# ---------------------------------------------------------------------------
def main() -> int:
    """Ejecuta el prototipo y devuelve un codigo de salida controlado."""
    print("EcoTech Solutions - Prototipo EF03 (Integrante 1)")

    try:
        config = cargar_configuracion()
    except ErrorConfiguracion as error:
        print(f"Configuracion: {error}")
        return 2

    try:
        usuario = input("Usuario: ")
        contrasena = getpass.getpass("Contrasena: ")
        sesion = autenticar(usuario, contrasena, config)
    except (EOFError, KeyboardInterrupt):
        print("\nOperacion cancelada.")
        return 1
    except ErrorAutenticacion as error:
        print(f"Acceso denegado: {error}")
        return 1
    except ErrorConfiguracion as error:
        print(f"Configuracion: {error}")
        return 2

    print(
        f"Sesion iniciada para {sesion.usuario}. "
        f"Duracion maxima: {sesion.duracion_seg} segundos."
    )

    try:
        moneda = input("Moneda de origen (3 letras, ej: USD): ")
        resultado = consultar_tipo_cambio(sesion, moneda, config)
    except (EOFError, KeyboardInterrupt):
        print("\nOperacion cancelada.")
        return 1
    except ErrorValidacion as error:
        print(f"Dato invalido: {error}")
        return 1
    except ErrorSesion as error:
        print(f"Sesion no valida: {error}")
        return 1
    except ErrorApi as error:
        print(f"No se pudo consultar la API: {error}")
        return 1

    print()
    print(
        f"1 {resultado.origen} = "
        f"{resultado.tasa:.4f} {resultado.destino}"
    )
    print(f"Ultima actualizacion: {resultado.actualizado:%Y-%m-%d %H:%M UTC}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
