"""DAO de la tabla actividad (capa de datos - Integrante 2).

Reutiliza DaoBase (consultar/ejecutar/ejecutar_con_id con rollback y finally).
Todos los SQL usan parametros: sin concatenacion => sin inyeccion.
"""
from data_base.dao_base import DaoBase


class ActividadDAO(DaoBase):
    """CRUD de la tabla actividad."""

    def crear(self, id_modulo, titulo):
        """Inserta una actividad en borrador (publicada=0) y retorna su id."""
        consulta = (
            "INSERT INTO actividad (id_modulo, titulo, publicada) "
            "VALUES (%s, %s, 0)"
        )
        return self.ejecutar_con_id(consulta, (id_modulo, titulo))

    def buscar_por_id(self, id_actividad):
        """Retorna la fila de la actividad como dict, o None si no existe."""
        consulta = "SELECT * FROM actividad WHERE id_actividad = %s"
        filas = self.consultar(consulta, (id_actividad,))
        return filas[0] if filas else None

    def listar_por_modulo(self, id_modulo):
        """Retorna las actividades de un modulo, como dicts."""
        consulta = (
            "SELECT * FROM actividad WHERE id_modulo = %s ORDER BY id_actividad"
        )
        return self.consultar(consulta, (id_modulo,))

    def actualizar(self, id_actividad, titulo):
        """Actualiza el titulo de la actividad. Retorna True si hubo filas afectadas."""
        consulta = "UPDATE actividad SET titulo = %s WHERE id_actividad = %s"
        return self.ejecutar(consulta, (titulo, id_actividad)) > 0

    def publicar(self, id_actividad):
        """Cambia publicada 0 -> 1. Retorna False si ya estaba publicada."""
        consulta = (
            "UPDATE actividad SET publicada = 1 "
            "WHERE id_actividad = %s AND publicada = 0"
        )
        return self.ejecutar(consulta, (id_actividad,)) > 0

    def eliminar(self, id_actividad):
        """Elimina la actividad. Retorna True si existia y fue eliminada."""
        consulta = "DELETE FROM actividad WHERE id_actividad = %s"
        return self.ejecutar(consulta, (id_actividad,)) > 0

    def pertenece_a(self, id_actividad, rut_instructor):
        """True si la actividad existe y su curso pertenece al instructor indicado."""
        consulta = (
            "SELECT COUNT(*) AS total FROM actividad a "
            "INNER JOIN modulo m ON m.id_modulo = a.id_modulo "
            "INNER JOIN curso c ON c.id_curso = m.id_curso "
            "WHERE a.id_actividad = %s AND c.rut_instructor = %s"
        )
        filas = self.consultar(consulta, (id_actividad, rut_instructor))
        return filas[0]["total"] > 0
