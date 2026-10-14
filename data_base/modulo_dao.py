"""DAO de la tabla modulo (capa de datos - Integrante 2).

Reutiliza DaoBase (consultar/ejecutar/ejecutar_con_id con rollback y finally).
Todos los SQL usan parametros: sin concatenacion => sin inyeccion.
"""
from data_base.dao_base import DaoBase


class ModuloDAO(DaoBase):
    """CRUD de la tabla modulo."""

    def crear(self, id_curso, titulo):
        """Inserta un modulo. El orden se calcula solo (MAX(orden)+1 del curso).

        Retorna el id del modulo nuevo (lastrowid).
        """
        consulta = (
            "INSERT INTO modulo (id_curso, titulo, orden) "
            "SELECT %s, %s, COALESCE(MAX(orden), 0) + 1 "
            "FROM modulo WHERE id_curso = %s"
        )
        return self.ejecutar_con_id(consulta, (id_curso, titulo, id_curso))

    def buscar_por_id(self, id_modulo):
        """Retorna la fila del modulo como dict, o None si no existe."""
        consulta = "SELECT * FROM modulo WHERE id_modulo = %s"
        filas = self.consultar(consulta, (id_modulo,))
        return filas[0] if filas else None

    def listar_por_curso(self, id_curso):
        """Retorna los modulos de un curso ordenados, como dicts."""
        consulta = (
            "SELECT * FROM modulo WHERE id_curso = %s ORDER BY orden, id_modulo"
        )
        return self.consultar(consulta, (id_curso,))

    def actualizar(self, id_modulo, titulo):
        """Actualiza el titulo del modulo. Retorna True si hubo filas afectadas."""
        consulta = "UPDATE modulo SET titulo = %s WHERE id_modulo = %s"
        return self.ejecutar(consulta, (titulo, id_modulo)) > 0

    def eliminar(self, id_modulo):
        """Elimina el modulo y sus actividades en la MISMA transaccion.

        Si el ultimo DELETE falla, el primero se revierte (rollback automatico).
        """
        consulta = [
            ("DELETE FROM actividad WHERE id_modulo = %s", (id_modulo,)),
            ("DELETE FROM modulo WHERE id_modulo = %s", (id_modulo,)),
        ]
        return self.ejecutar(consulta) > 0

    def pertenece_a(self, id_modulo, rut_instructor):
        """True si el modulo existe y su curso pertenece al instructor indicado."""
        consulta = (
            "SELECT COUNT(*) AS total FROM modulo m "
            "INNER JOIN curso c ON c.id_curso = m.id_curso "
            "WHERE m.id_modulo = %s AND c.rut_instructor = %s"
        )
        filas = self.consultar(consulta, (id_modulo, rut_instructor))
        return filas[0]["total"] > 0
