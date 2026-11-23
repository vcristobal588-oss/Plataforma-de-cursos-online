"""EF03 - Integrante 2: Seguridad, Autenticacion, Variables de Entorno y Validacion.

Proyecto: EcoTech Solutions - Plataforma de cursos online
Asignatura: TI3021 - Programacion Orientada a Objeto Seguro

Criterios cubiertos:
- 3.1.2.I.5: Autenticacion con hash bcrypt, tiempo constante y bloqueo por intentos.
- 3.1.2.I.6: Validacion y saneamiento estricto de credenciales, moneda y URL (anti-SSRF).
- 3.1.2.I.7: Carga segura de configuracion y secretos desde .env / variables de entorno.
- 3.1.2.I.8: Control de sesion con token criptografico interno, expiracion y cierre.
"""
from dataclasses import dataclass, field
import hmac
import os
import re
import secrets
import time
from urllib.parse import urlparse

import bcrypt

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None


PATRON_USUARIO = re.compile(r"^[A-Za-z0-9_.-]{3,30}$")
PATRON_MONEDA = re.compile(r"^[A-Za-z]{3}$")
PATRON_HASH_BCRYPT = re.compile(r"^\$2[aby]\$\d{2}\$[./A-Za-z0-9]{53}$")

DURACION_SESION = 300
MAX_BYTES_CONTRASENA = 72
MAX_INTENTOS_LOGIN = 3

HASH_DUMMY_BCRYPT = b"$2b$12$C6UzMDM.H6dfI/f/IKxGhuOb1M21N7.zR5s.u.P3pP7P7p7P7p7Pu"


class ErrorEcoTech(Exception):
    """Error base del prototipo EF03."""


class ErrorConfiguracion(ErrorEcoTech):
    """Falta una variable de entorno o su valor no cumple reglas de seguridad."""


class ErrorAutenticacion(ErrorEcoTech):
    """Fallo de credenciales o bloqueo por exceso de intentos."""


class ErrorSesion(ErrorEcoTech):
    """La sesion no existe, fue falsificada, cerrada o ya expiro."""


class ErrorValidacion(ErrorEcoTech):
    """Una entrada del usuario contiene formato o caracteres no permitidos."""


@dataclass(frozen=True)
class Configuracion:
    """Parametros y secretos cargados desde el entorno (3.1.2.I.7)."""

    usuario: str
    hash_contrasena: str
    api_url: str
    api_key: str | None
    moneda_destino: str
    hosts_permitidos: tuple[str, ...]


@dataclass(frozen=True)
class Sesion:
    """Representa una sesion autenticada asociada a un token criptografico."""

    usuario: str
    token: str = field(repr=False)
    duracion_seg: int = DURACION_SESION
    inicio: float = field(default_factory=time.monotonic, repr=False)

    def no_expirada(self) -> bool:
        """Verifica con reloj monotonico que no haya vencido el tiempo maximo."""
        return (time.monotonic() - self.inicio) < self.duracion_seg


class _RegistroSesiones:
    """Almacen interno de tokens emitidos por autenticar() (anti-falsificacion)."""

    def __init__(self) -> None:
        self._activas: dict[str, str] = {}

    def emitir(self, usuario: str) -> str:
        token = secrets.token_urlsafe(32)
        self._activas[token] = usuario
        return token

    def es_valido(self, sesion: Sesion) -> bool:
        if not isinstance(sesion, Sesion) or not sesion.token:
            return False
        usuario_registrado = self._activas.get(sesion.token)
        if usuario_registrado is None:
            return False
        return hmac.compare_digest(usuario_registrado, sesion.usuario)

    def revocar(self, sesion: Sesion) -> None:
        if isinstance(sesion, Sesion) and sesion.token:
            self._activas.pop(sesion.token, None)


_SESIONES_ACTIVAS = _RegistroSesiones()


class ControlIntentos:
    """Limita intentos fallidos consecutivos de inicio de sesion (3.1.2.I.5)."""

    def __init__(self, maximo: int = MAX_INTENTOS_LOGIN) -> None:
        if maximo < 1:
            raise ValueError("El maximo de intentos debe ser al menos 1.")
        self.maximo = maximo
        self.fallos = 0

    @property
    def bloqueado(self) -> bool:
        return self.fallos >= self.maximo

    def registrar_fallo(self) -> None:
        self.fallos += 1

    def reiniciar(self) -> None:
        self.fallos = 0


def _asegurar_texto_limpio(valor: object, etiqueta: str) -> str:
    """Rechaza valores no textuales, bytes nulos o saltos de linea (CRLF)."""
    if not isinstance(valor, str):
        raise ErrorValidacion(f"{etiqueta} debe ser una cadena de texto.")
    if "\x00" in valor or "\r" in valor or "\n" in valor:
        raise ErrorValidacion(f"{etiqueta} contiene caracteres de control no permitidos.")
    return valor


def validar_url_segura(url: str, hosts_permitidos: tuple[str, ...]) -> str:
    """Valida HTTPS, ausencia de credenciales en URL y host en lista blanca."""
    url = _asegurar_texto_limpio(url, "ECOTECH_API_URL").strip().rstrip("/")
    parsed = urlparse(url)

    if parsed.scheme != "https":
        raise ErrorConfiguracion("ECOTECH_API_URL debe usar protocolo HTTPS.")
    if not parsed.hostname:
        raise ErrorConfiguracion("ECOTECH_API_URL no tiene un dominio valido.")
    if parsed.username or parsed.password:
        raise ErrorConfiguracion("ECOTECH_API_URL no debe incluir credenciales embebidas.")
    if parsed.hostname.lower() not in {h.lower() for h in hosts_permitidos}:
        raise ErrorConfiguracion(
            f"El host '{parsed.hostname}' no esta en la lista blanca permitida."
        )
    return url


def validar_credenciales(usuario: str, contrasena: str) -> str:
    """Valida formato de usuario y limites de contrasena antes de autenticar."""
    usuario_limpio = _asegurar_texto_limpio(usuario, "El usuario").strip()
    _asegurar_texto_limpio(contrasena, "La contrasena")

    if not PATRON_USUARIO.fullmatch(usuario_limpio):
        raise ErrorValidacion(
            "El usuario debe tener entre 3 y 30 caracteres (letras, numeros, '.', '_' o '-')."
        )
    if not contrasena:
        raise ErrorValidacion("La contrasena no puede estar vacia.")
    if len(contrasena.encode("utf-8")) > MAX_BYTES_CONTRASENA:
        raise ErrorValidacion(
            f"La contrasena no puede superar los {MAX_BYTES_CONTRASENA} bytes."
        )
    return usuario_limpio


def validar_moneda(valor: str) -> str:
    """Sanea y valida un codigo ISO de moneda de 3 letras (3.1.2.I.6)."""
    texto = _asegurar_texto_limpio(valor, "La moneda").strip().upper()
    if not PATRON_MONEDA.fullmatch(texto):
        raise ErrorValidacion("La moneda debe tener exactamente 3 letras (ej: USD).")
    return texto


def cargar_configuracion(ruta_env: str | None = None) -> Configuracion:
    """Carga variables de entorno (incluyendo .env local si existe) y las valida."""
    if load_dotenv is not None:
        load_dotenv(dotenv_path=ruta_env, override=False)

    usuario = (os.getenv("ECOTECH_USER") or "").strip()
    hash_contrasena = (os.getenv("ECOTECH_USER_HASH") or "").strip()
    api_key = (os.getenv("ECOTECH_API_KEY") or "").strip() or None
    moneda_destino = (os.getenv("ECOTECH_MONEDA_DESTINO") or "CLP").strip().upper()

    hosts_raw = os.getenv("ECOTECH_ALLOWED_HOSTS") or "open.er-api.com"
    hosts_permitidos = tuple(
        h.strip().lower() for h in hosts_raw.split(",") if h.strip()
    )
    if not hosts_permitidos:
        raise ErrorConfiguracion("ECOTECH_ALLOWED_HOSTS debe definir al menos un dominio.")

    api_url_raw = os.getenv("ECOTECH_API_URL") or "https://open.er-api.com/v6/latest"
    api_url = validar_url_segura(api_url_raw, hosts_permitidos)

    if not usuario or not hash_contrasena:
        raise ErrorConfiguracion(
            "Defina ECOTECH_USER y ECOTECH_USER_HASH en su archivo .env o entorno."
        )
    if not PATRON_USUARIO.fullmatch(usuario):
        raise ErrorConfiguracion(
            "ECOTECH_USER debe tener entre 3 y 30 caracteres validos."
        )
    if not PATRON_HASH_BCRYPT.fullmatch(hash_contrasena):
        raise ErrorConfiguracion(
            "ECOTECH_USER_HASH no tiene el formato de un hash bcrypt valido."
        )
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
        hosts_permitidos=hosts_permitidos,
    )


def autenticar(
    usuario: str,
    contrasena: str,
    config: Configuracion,
    control: ControlIntentos | None = None,
) -> Sesion:
    """Verifica credenciales con bcrypt en tiempo constante y emite sesion."""
    if control is not None and control.bloqueado:
        raise ErrorAutenticacion(
            "Acceso bloqueado por demasiados intentos fallidos."
        )

    try:
        usuario_valido = validar_credenciales(usuario, contrasena)
    except ErrorValidacion as error:
        bcrypt.checkpw(b"tiempo_constante", HASH_DUMMY_BCRYPT)
        if control is not None:
            control.registrar_fallo()
        raise ErrorAutenticacion("Usuario o contrasena incorrectos.") from error

    usuario_ok = hmac.compare_digest(
        usuario_valido.encode("utf-8"), config.usuario.encode("utf-8")
    )
    hash_objetivo = (
        config.hash_contrasena.encode("utf-8") if usuario_ok else HASH_DUMMY_BCRYPT
    )

    try:
        clave_ok = bcrypt.checkpw(contrasena.encode("utf-8"), hash_objetivo)
    except ValueError as error:
        raise ErrorConfiguracion(
            "ECOTECH_USER_HASH no es un hash bcrypt valido."
        ) from error

    if not (usuario_ok and clave_ok):
        if control is not None:
            control.registrar_fallo()
        raise ErrorAutenticacion("Usuario o contrasena incorrectos.")

    if control is not None:
        control.reiniciar()

    token = _SESIONES_ACTIVAS.emitir(config.usuario)
    return Sesion(usuario=config.usuario, token=token)


def exigir_sesion_activa(sesion: Sesion) -> None:
    """Impide ejecutar operaciones sensibles sin sesion valida y vigente (3.1.2.I.8)."""
    if not isinstance(sesion, Sesion) or not _SESIONES_ACTIVAS.es_valido(sesion):
        raise ErrorSesion("Sesion inexistente o no autorizada. Inicie sesion primero.")
    if not sesion.no_expirada():
        _SESIONES_ACTIVAS.revocar(sesion)
        raise ErrorSesion("La sesion expiro. Vuelva a iniciar sesion.")


def cerrar_sesion(sesion: Sesion) -> None:
    """Invalida inmediatamente el token de la sesion."""
    _SESIONES_ACTIVAS.revocar(sesion)