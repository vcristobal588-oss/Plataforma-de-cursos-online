"""DAO base: abstraccion + reutilizacion + manejo de errores (criterios 2.1.2 y 2.1.4).

Es una CLASE ABSTRACTA (abc.ABC): define el contrato que toda tabla debe
declarar (propiedades `tabla` y `clave`) y entrega el CRUD generico listo para
usar. Los DAO concretos heredan de aqui y SOLO escriben SQL cuando la
operacion es especial (JOINs, borrados en cascada, transacciones multi-tabla).

 asi se evita duplicar el bloque try/except/finally con rollback en cada DAO
 (criterio 2.1.2.G.6: reutilizacion de clases) y se aplica abstraccion
 (criterio 2.1.2.G.5).

Garantias que hereda todo DAO:
- Consultas parametrizadas (%s): sin concatenacion => sin inyeccion SQL.
- Transaccion: commit solo si todo sale bien; rollback si algo falla.
- finally: siempre cierra cursor y conexion, sin importar el resultado.
- Errores de MySQL traducidos a excepciones propias (excepcion_para_codigo).
"""
from abc import ABC, abstractmethod

import mysql.connector

from data_base.conexion import obtener_conexion
from data_base.errores import excepcion_para_codigo


class DaoBase(ABC):
    """Clase abstracta de la que heredan todos los DAO concretos."""

    # --- Contrato que cada subclase DEBE cumplir (abstraccion) ---

    @property
    @abstractmethod
    def tabla(self):
        """Nombre de la tabla que administra este DAO (constante de clase)."""

    @property
    @abstractmethod
    def clave(self):
        """Nombre de la columna de la clave primaria de esa tabla."""

    # --- Operaciones genericas reutilizadas por los DAO concretos ---

    def buscar_por_id(self, valor):
        """Retorna la fila de la clave primaria indicada como dict, o None."""
        return self._fila(
            f"SELECT * FROM {self.tabla} WHERE {self.clave} = %s", (valor,)
        )

    def listar_todos(self):
        """Retorna todas las filas de la tabla (ordenadas por su clave)."""
        return self.consultar(f"SELECT * FROM {self.tabla} ORDER BY {self.clave}")

    def contar(self, columna, valor):
        """Retorna la cantidad de filas donde columna = valor (parametrizado)."""
        filas = self.consultar(
            f"SELECT COUNT(*) AS total FROM {self.tabla} WHERE {columna} = %s",
            (valor,),
        )
        return filas[0]["total"]

    def listar_por(self, columna, valor, orden=None):
        """Retorna las filas donde columna = valor, opcionalmente ordenadas.

        `orden` es una constante de la subclase (nunca dato del usuario),
        igual que `tabla` y `clave`: los unicos valores interpolados en el SQL
        provienen de codigo, nunca de la entrada.
        """
        consulta = f"SELECT * FROM {self.tabla} WHERE {columna} = %s"
        if orden:
            consulta += f" ORDER BY {orden}"
        return self.consultar(consulta, (valor,))

    def eliminar(self, valor):
        """Elimina la fila de la clave primaria indicada. True si existia.

        Los DAO concretos pueden sobreescribirlo cuando el borrado debe ser
        en cascada (p.ej. CursoDAO elimina modulos y actividades primero).
        """
        return (
            self.ejecutar(
                f"DELETE FROM {self.tabla} WHERE {self.clave} = %s", (valor,)
            )
            > 0
        )

    # --- Primitivas transaccionales (compartidas por todos los DAO) ---

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
            raise excepcion_para_codigo(error.errno) from error
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
        elif isinstance(operaciones, str):
            # Guarda: sin esta validacion se iteraria la cadena caracter a
            # caracter en vez de ejecutar una sentencia.
            raise ValueError(
                "Faltan los parametros de la consulta: usa %s con una tupla, "
                "p.ej. ejecutar('DELETE FROM x WHERE id = %s', (id,))."
            )
        if not operaciones:
            raise ValueError("No hay operaciones para ejecutar.")
        return self._correr(operaciones, con_id=False)

    def ejecutar_con_id(self, consulta, parametros):
        """Ejecuta un INSERT y retorna el id autogenerado (lastrowid).

        Util para tablas con AUTO_INCREMENT (p.ej. direccion, curso).
        """
        return self._correr([(consulta, parametros)], con_id=True)

    def _fila(self, consulta, parametros=()):
        """Ejecuta un SELECT y retorna la primera fila (dict) o None."""
        filas = self.consultar(consulta, parametros)
        return filas[0] if filas else None

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
            raise excepcion_para_codigo(error.errno) from error
        finally:
            self._cerrar(cursor, conexion)

    # --- Metodos auxiliares privados ---

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
