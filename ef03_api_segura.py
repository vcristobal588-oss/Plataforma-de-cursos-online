"""EF03 - Integracion: Consumo seguro de API externa (Integrantes 1 y 2).

Proyecto: EcoTech Solutions - Plataforma de cursos online
Asignatura: TI3021 - Programacion Orientada a Objeto Seguro

Arquitectura del avance:
- Integrante 1 (ef03_api_segura.py): Peticion HTTP, extraccion JSON y resiliencia de red.
- Integrante 2 (seguridad_ef03.py): Variables .env, validacion/saneamiento, bcrypt y sesion.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
import getpass
import math

import requests

from seguridad_ef03 import (
    Configuracion,
    ControlIntentos,
    ErrorAutenticacion,
    ErrorConfiguracion,
    ErrorEcoTech,
    ErrorSesion,
    ErrorValidacion,
    Sesion,
    autenticar,
    cargar_configuracion,
    cerrar_sesion,
    exigir_sesion_activa,
    validar_moneda,
)

TIEMPO_ESPERA = (3.05, 5)


class ErrorApi(ErrorEcoTech):
    """Fallo controlado al consultar o interpretar la API externa (Integrante 1)."""


@dataclass(frozen=True)
class TipoCambio:
    """Solo los datos necesarios extraidos del JSON (3.1.1.I.3)."""

    origen: str
    destino: str
    tasa: float
    actualizado: datetime


def construir_url(config: Configuracion, moneda_origen: str) -> str:
    """Arma la URL con una moneda ya validada (solo 3 letras A-Z)."""
    return f"{config.api_url}/{moneda_origen}"


def _mensaje_http(codigo: int) -> str:
    """Traduce codigos HTTP a mensajes claros sin exponer detalles internos."""
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
        return "La API intento redirigir la solicitud; por seguridad no se siguio."
    if 500 <= codigo <= 599:
        return "La API no esta disponible en este momento (error del servidor)."
    return f"La API respondio con un codigo inesperado ({codigo})."


def extraer_tipo_cambio(
    datos: dict, moneda_origen: str, moneda_destino: str
) -> TipoCambio:
    """Extrae y valida tipos/consistencia del JSON (3.1.1.I.3 - 3.1.1.I.4)."""
    if not isinstance(datos, dict):
        raise ErrorApi("La API devolvio un JSON con una estructura inesperada.")
    if datos.get("result") != "success":
        raise ErrorApi("La API no pudo entregar el tipo de cambio solicitado.")
    if datos.get("base_code") != moneda_origen:
        raise ErrorApi("La API devolvio una moneda base distinta a la solicitada.")

    tasas = datos.get("rates")
    if not isinstance(tasas, dict):
        raise ErrorApi("La API no devolvio la lista de tipos de cambio.")

    tasa = tasas.get(moneda_destino)
    if isinstance(tasa, bool) or not isinstance(tasa, (int, float)):
        raise ErrorApi(f"No hay un tipo de cambio disponible para {moneda_destino}.")

    tasa = float(tasa)
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
    """Consulta la API externa solo si existe una sesion activa (3.1.2.I.8)."""
    exigir_sesion_activa(sesion)
    moneda_origen = validar_moneda(moneda_origen)

    url = construir_url(config, moneda_origen)
    headers = {"Accept": "application/json"}
    if config.api_key:
        headers["X-API-Key"] = config.api_key

    try:
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

    if respuesta.status_code != 200:
        raise ErrorApi(_mensaje_http(respuesta.status_code))

    try:
        datos = respuesta.json()
    except ValueError as error:
        raise ErrorApi("La API devolvio una respuesta que no es JSON valido.") from error

    return extraer_tipo_cambio(datos, moneda_origen, config.moneda_destino)


def main() -> int:
    """Orquesta configuracion, login (Integrante 2) y consulta API (Integrante 1)."""
    print("EcoTech Solutions - Consulta Segura de Tipo de Cambio (EF03)")

    try:
        config = cargar_configuracion()
    except ErrorConfiguracion as error:
        print(f"Configuracion: {error}")
        return 2

    control_intentos = ControlIntentos(maximo=3)
    sesion: Sesion | None = None

    while not control_intentos.bloqueado:
        try:
            usuario = input("Usuario: ")
            contrasena = getpass.getpass("Contrasena: ")
            sesion = autenticar(usuario, contrasena, config, control_intentos)
            break
        except (EOFError, KeyboardInterrupt):
            print("\nOperacion cancelada.")
            return 1
        except ErrorAutenticacion as error:
            restantes = control_intentos.maximo - control_intentos.fallos
            print(f"Acceso denegado: {error} (intentos restantes: {restantes})")
            if control_intentos.bloqueado:
                return 1
        except ErrorConfiguracion as error:
            print(f"Configuracion: {error}")
            return 2

    assert sesion is not None
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
    finally:
        cerrar_sesion(sesion)

    print()
    print(f"1 {resultado.origen} = {resultado.tasa:.4f} {resultado.destino}")
    print(f"Ultima actualizacion: {resultado.actualizado:%Y-%m-%d %H:%M UTC}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())