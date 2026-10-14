"""DAO base: concentra el manejo de errores y transacciones (criterio 2.1.4).

Todos los DAO heredan de esta clase para no duplicar el bloque
try/except/finally con rollback (criterio 2.1.2: reutilizacion).
"""
import mysql.connector
from mysql.connector import errorcode

from data_base.conexion import obtener_conexion
from data_base.errores import ErrorBaseDatos, RegistroDuplicado


class DaoBase:
    """Clase reutilizable de la que heredan los DAO concretos.

    - Todas las consultas son parametrizadas (%s): previene inyeccion SQL.
    - Transaccion: commit solo si todo sale bien; rollback si algo falla.
    - finally: siempre cierra cursor y conexion, sin importar el resultado.
    """

    def consultar(self, consulta, parametros=()):
        """Ejecuta un SELECT parametrizado y retorna las filas (como dict)."""
        conexion = None
        cursor = None
        try:
            conexion = obtener_conexion()
            cursor = conexion.cursor(dictionary=True)
            cursor.execute(consulta, parametros)
            return cursor.fetchall()
        except mysql.connector.Error as error:
            self._rollback(conexion)
            raise self._a_excepcion(error) from error
        finally:
            self._cerrar(cursor, conexion)

    def ejecutar(self, operaciones, parametros=None):
        """Ejecuta una sentencia o varias en UNA sola transaccion.

        Acepta: ejecutar("SQL", (p,)) para una sentencia, o una lista de
        tuplas (consulta, parametros) para varias.

        Si todas las operaciones tienen exito hace commit; si alguna
        falla, revierte TODO con rollback. Retorna las filas afectadas
        de la ultima operacion.
        """
        if parametros is not None:
            operaciones = [(operaciones, parametros)]
        return self._correr(operaciones, con_id=False)

    def ejecutar_con_id(self, consulta, parametros):
        """Ejecuta un INSERT y retorna el id autogenerado (lastrowid).

        Util para tablas con AUTO_INCREMENT (p.ej. direccion).
        """
        return self._correr([(consulta, parametros)], con_id=True)

    def _correr(self, operaciones, con_id):
        """Nucleo transaccional: commit si todo va bien, rollback si algo falla."""
        conexion = None
        cursor = None
        try:
            conexion = obtener_conexion()
            cursor = conexion.cursor()
            for consulta, parametros in operaciones:
                cursor.execute(consulta, parametros)
            conexion.commit()
            return cursor.lastrowid if con_id else cursor.rowcount
        except mysql.connector.Error as error:
            self._rollback(conexion)
            raise self._a_excepcion(error) from error
        finally:
            self._cerrar(cursor, conexion)

    # --- Métodos auxiliares privados ---

    @staticmethod
    def _a_excepcion(error):
        """Traduce un error de MySQL a una excepcion propia con mensaje seguro."""
        if error.errno == errorcode.ER_DUP_ENTRY:
            return RegistroDuplicado("El RUT o el correo electronico ya estan registrados.")
        if error.errno == errorcode.ER_NO_REFERENCED_ROW_2:
            return ErrorBaseDatos("La operacion fallo: el registro referenciado no existe.")
        if error.errno == errorcode.ER_ROW_IS_REFERENCED_2:
            return ErrorBaseDatos("No se puede eliminar: existen registros que dependen de este registro.")
        # Mensaje generico a proposito: no se exponen consultas,
        # tablas ni parametros internos (seguridad).
        return ErrorBaseDatos(f"Operacion no completada en la base de datos (codigo {error.errno}).")

    @staticmethod
    def _rollback(conexion):
        if conexion is not None:
            try:
                if conexion.is_connected():
                    conexion.rollback()
            except mysql.connector.Error:
                pass

    @staticmethod
    def _cerrar(cursor, conexion):
        if cursor is not None:
            try:
                cursor.close()
            except mysql.connector.Error:
                pass
        if conexion is not None:
            try:
                if conexion.is_connected():
                    conexion.close()
            except mysql.connector.Error:
                pass
