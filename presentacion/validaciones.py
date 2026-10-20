"""Validaciones de entrada compartidas por la capa de presentacion.

Criterio 2.1.2.G.6: las reglas de formato viven UNA sola vez aqui y las
reutilizan menu_auth, menu_instructor y menu_estudiante (si cada menu
reescribiera sus validaciones, la logica se duplicaria).

Toda funcion lanza ValueError con un mensaje claro; la capa de presentacion
lo captura e informa sin que el programa se interrumpa (criterio 2.1.4.G.14).
"""
import re

PATRON_RUT = re.compile(r"^\d{7,8}-[\dkK]$")
CONTRASENA_MINIMA = 6

# Largos maximos = tamaños de columna definidos en data_base/*.sql.
# Validar aqui evita errores 1406 de MySQL a mitad de operacion.
LONG_NOMBRE = 45
LONG_CORREO = 60
LONG_TITULO = 100
LONG_DETALLE = 100   # carrera / especialidad
LONG_COMUNA = 50
LONG_CALLE = 100


def a_entero(valor, etiqueta="El id"):
    """Convierte una entrada a entero. Lanza ValueError si no es numerico."""
    try:
        return int(valor)
    except (TypeError, ValueError):
        raise ValueError(f"{etiqueta} debe ser un numero entero.")


def no_vacio(valor, etiqueta="El dato"):
    """Retorna el valor sin espacios exteriores. ValueError si queda vacio."""
    texto = "" if valor is None else str(valor).strip()
    if not texto:
        raise ValueError(f"{etiqueta} no puede estar vacio.")
    return texto


def validar_longitud(valor, maximo, etiqueta="El texto"):
    """Valida que el dato no supere el largo maximo de su columna."""
    texto = "" if valor is None else str(valor).strip()
    if len(texto) > maximo:
        raise ValueError(
            f"{etiqueta} no puede superar los {maximo} caracteres "
            f"(ingresó {len(texto)})."
        )
    return texto


def _digito_verificador(cuerpo):
    """Calcula el digito verificador chileno (modulo 11) de un RUT."""
    serie = (2, 3, 4, 5, 6, 7)
    total = sum(
        int(digito) * serie[indice % len(serie)]
        for indice, digito in enumerate(reversed(cuerpo))
    )
    resto = total % 11
    dv = 11 - resto
    if dv == 11:
        return "0"
    if dv == 10:
        return "K"
    return str(dv)


def validar_rut(rut):
    """Valida formato (7-8 digitos + guion + dv) y CALCULA el digito verificador.

    Retorna el RUT en mayusculas. ValueError si el formato o el dv no
    coinciden (evita altas con RUT inventados o mal escritos).
    """
    rut = no_vacio(rut, "El RUT")
    if not PATRON_RUT.match(rut):
        raise ValueError("RUT con formato invalido. Ejemplo: 12345678-9.")
    cuerpo, dv_ingresado = rut.split("-")
    esperado = _digito_verificador(cuerpo)
    if dv_ingresado.upper() != esperado:
        raise ValueError(
            f"Digito verificador incorrecto: para {cuerpo} deberia ser {esperado}."
        )
    return f"{cuerpo}-{esperado}"


def validar_correo(correo):
    """Valida estructura basica de correo electronico. Retorna el correo."""
    correo = no_vacio(correo, "El correo electronico")
    if "@" not in correo or correo.startswith("@") or "." not in correo.rsplit("@", 1)[-1]:
        raise ValueError("Correo electronico invalido. Ejemplo: alumno@correo.cl.")
    return correo


def validar_contrasena(contrasena, minima=CONTRASENA_MINIMA, maxima=72):
    """Valida la longitud minima de la contrasena (bcrypt admite hasta 72)."""
    if len(contrasena or "") < minima:
        raise ValueError(
            f"La contrasena debe tener al menos {minima} caracteres."
        )
    if len(contrasena) > maxima:
        raise ValueError(
            f"La contrasena no puede superar los {maxima} caracteres."
        )
    return contrasena
