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
