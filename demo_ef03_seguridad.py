"""Evidencia Integrante 2: Pruebas autonomas de seguridad, auth, .env y sesion.

Uso: python demo_ef03_seguridad.py
"""
import os
import time
import bcrypt

from ef03_api_segura import consultar_tipo_cambio
from seguridad_ef03 import (
    ControlIntentos,
    ErrorAutenticacion,
    ErrorConfiguracion,
    ErrorSesion,
    ErrorValidacion,
    Sesion,
    autenticar,
    cargar_configuracion,
    cerrar_sesion,
    exigir_sesion_activa,
    validar_moneda,
)


def probar(nombre: str, ok: bool, detalle: str = "") -> int:
    marca = "OK   " if ok else "FALLA"
    print(f"[{marca}] {nombre}" + (f" -> {detalle}" if detalle else ""))
    return 0 if ok else 1


def _lanza(excepcion, fn, *args, **kwargs) -> bool:
    try:
        fn(*args, **kwargs)
    except excepcion:
        return True
    return False


def main() -> int:
    fallos = 0
    claves_env = (
        "ECOTECH_USER",
        "ECOTECH_USER_HASH",
        "ECOTECH_API_URL",
        "ECOTECH_ALLOWED_HOSTS",
        "ECOTECH_MONEDA_DESTINO",
    )
    respaldo = {k: os.environ.get(k) for k in claves_env}

    try:
        hash_demo = bcrypt.hashpw(b"ClaveSegura2026!", bcrypt.gensalt()).decode()
        os.environ["ECOTECH_USER"] = "admin_ecotech"
        os.environ["ECOTECH_USER_HASH"] = hash_demo
        os.environ["ECOTECH_API_URL"] = "https://open.er-api.com/v6/latest"
        os.environ["ECOTECH_ALLOWED_HOSTS"] = "open.er-api.com"
        os.environ["ECOTECH_MONEDA_DESTINO"] = "CLP"

        print("=== 1) VARIABLES DE ENTORNO Y ANTI-SSRF (3.1.2.I.7) ===")
        cfg = cargar_configuracion()
        fallos += probar("Carga correcta desde entorno", cfg.usuario == "admin_ecotech")

        os.environ["ECOTECH_API_URL"] = "http://open.er-api.com/v6/latest"
        fallos += probar("Rechaza HTTP sin cifrar", _lanza(ErrorConfiguracion, cargar_configuracion))

        os.environ["ECOTECH_API_URL"] = "https://evil.com/v6/latest"
        fallos += probar("Rechaza host fuera de lista blanca (anti-SSRF)", _lanza(ErrorConfiguracion, cargar_configuracion))

        os.environ["ECOTECH_API_URL"] = "https://user:pass@open.er-api.com/v6/latest"
        fallos += probar("Rechaza credenciales embebidas en URL", _lanza(ErrorConfiguracion, cargar_configuracion))

        os.environ["ECOTECH_API_URL"] = "https://open.er-api.com/v6/latest"
        cfg = cargar_configuracion()

        print("\n=== 2) VALIDACION Y SANEAMIENTO DE ENTRADAS (3.1.2.I.6) ===")
        fallos += probar("Normaliza ' usd ' -> 'USD'", validar_moneda(" usd ") == "USD")
        fallos += probar("Bloquea vacio", _lanza(ErrorValidacion, validar_moneda, "   "))
        fallos += probar("Bloquea path traversal ('../')", _lanza(ErrorValidacion, validar_moneda, "../"))
        fallos += probar("Bloquea inyeccion CRLF", _lanza(ErrorValidacion, validar_moneda, "USD\r\n"))
        fallos += probar("Bloquea tipo no textual (int)", _lanza(ErrorValidacion, validar_moneda, 123))

        print("\n=== 3) AUTENTICACION BCRYPT Y BLOQUEO DE INTENTOS (3.1.2.I.5) ===")
        control = ControlIntentos(maximo=3)
        fallos += probar("Rechaza clave incorrecta (intento 1)", _lanza(ErrorAutenticacion, autenticar, "admin_ecotech", "mala", cfg, control))
        fallos += probar("Rechaza usuario inexistente (intento 2)", _lanza(ErrorAutenticacion, autenticar, "otro.user", "mala", cfg, control))
        fallos += probar("Rechaza entrada maliciosa (intento 3)", _lanza(ErrorAutenticacion, autenticar, "admin'--", "mala", cfg, control))
        fallos += probar("Bloquea al 4to intento aunque clave sea correcta",
                         _lanza(ErrorAutenticacion, autenticar, "admin_ecotech", "ClaveSegura2026!", cfg, control))

        sesion = autenticar("admin_ecotech", "ClaveSegura2026!", cfg)
        fallos += probar("Autenticacion exitosa emite token seguro", bool(sesion.token))

        print("\n=== 4) CONTROL DE SESION Y REVOCACION (3.1.2.I.8) ===")
        sesion_falsa = Sesion(usuario="admin_ecotech", token="token_inventado")
        fallos += probar("Bloquea sesion falsificada en memoria",
                         _lanza(ErrorSesion, consultar_tipo_cambio, sesion_falsa, "USD", cfg))

        sesion_expirada = Sesion(usuario="admin_ecotech", token=sesion.token, duracion_seg=0)
        time.sleep(0.01)
        fallos += probar("Bloquea sesion expirada", _lanza(ErrorSesion, exigir_sesion_activa, sesion_expirada))

        cerrar_sesion(sesion)
        fallos += probar("Bloquea sesion tras cerrar_sesion()", _lanza(ErrorSesion, exigir_sesion_activa, sesion))

        print(f"\n{'=' * 55}\nRESULTADO INTEGRANTE 2: {fallos} fallos.")
        return 1 if fallos else 0
    finally:
        for k, v in respaldo.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


if __name__ == "__main__":
    raise SystemExit(main())