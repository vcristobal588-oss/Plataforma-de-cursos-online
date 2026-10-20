"""Excepciones propias de la capa de datos (Integrante 1).

La capa de presentacion captura estas excepciones en lugar de las
excepciones crudas del driver, de modo que el sistema no se cae y
los mensajes no exponen detalles internos de MySQL.
"""


class ErrorBaseDatos(Exception):
    """Error generico al ejecutar una operacion sobre la base de datos."""


class ErrorConexion(ErrorBaseDatos):
    """No se pudo establecer la conexion con el servidor MySQL."""


class RegistroDuplicado(ErrorBaseDatos):
    """Se intento guardar un RUT o correo que ya existen (clave unica)."""


def excepcion_para_codigo(errno, mensaje_duplicado=None):
    """Construye la excepcion propia correspondiente a un codigo de error MySQL.

    Compartida por las DOS tecnologias de persistencia del proyecto:
    - DaoBase (mysql.connector / libreria oficial)  -> criterio 2.1.3.G.9
    - capa ORM (Peewee)                            -> consigna de clases
    Asi ambos caminos informan exactamente los mismos mensajes seguros
    (criterio 2.1.2.G.6: se reutiliza la logica en vez de duplicarla).

    Codigos: 1062 = ER_DUP_ENTRY (clave unica),
             1452 = ER_NO_REFERENCED_ROW_2 (FK inexistente),
             1451 = ER_ROW_IS_REFERENCED_2 (registro referenciado).
    """
    if errno == 1062:
        return RegistroDuplicado(
            mensaje_duplicado or "El RUT o el correo electronico ya estan registrados."
        )
    if errno == 1452:
        return ErrorBaseDatos("La operacion fallo: el registro referenciado no existe.")
    if errno == 1451:
        return ErrorBaseDatos(
            "No se puede eliminar: existen registros que dependen de este registro."
        )
    if errno is None:
        return ErrorBaseDatos("Operacion no completada en la base de datos.")
    # Mensaje generico a proposito: no se exponen consultas, tablas,
    # parametros ni el detalle crudo del driver (seguridad).
    return ErrorBaseDatos(f"Operacion no completada en la base de datos (codigo {errno}).")
