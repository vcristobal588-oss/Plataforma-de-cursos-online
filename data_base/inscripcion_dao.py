"""DAO de inscripciones y avance de estudiante (capa de datos - Integrante 3).

Reutiliza DaoBase (consultar/ejecutar con rollback y finalmente cierre de conexion).
Consultas parametrizadas con %s para seguridad ante inyeccion SQL.
"""
from data_base.dao_base import DaoBase


class InscripcionDAO(DaoBase):
    """CRUD para inscripciones y control de avance de estudiantes."""

    def inscribir(self, rut_estudiante, id_curso):
        """Inscribe un estudiante en un curso. Retorna el id de la inscripcion."""
        consulta = (
            "INSERT INTO inscripcion (rut_estudiante, id_curso) "
            "VALUES (%s, %s)"
        )
        return self.ejecutar_con_id(consulta, (rut_estudiante, id_curso))

    def esta_inscrito(self, rut_estudiante, id_curso):
        """Retorna True si el estudiante ya esta inscrito en el curso."""
        consulta = (
            "SELECT COUNT(*) AS total FROM inscripcion "
            "WHERE rut_estudiante = %s AND id_curso = %s"
        )
        filas = self.consultar(consulta, (rut_estudiante, id_curso))
        return filas[0]["total"] > 0

    def listar_cursos_estudiante(self, rut_estudiante):
        """Lista los cursos en los que el estudiante esta inscrito con su porcentaje de avance."""
        consulta = (
            "SELECT i.id_inscripcion, c.id_curso, c.titulo AS curso_titulo, c.descripcion, "
            "u.nombre_completo AS instructor, i.fecha_inscripcion "
            "FROM inscripcion i "
            "INNER JOIN curso c ON c.id_curso = i.id_curso "
            "INNER JOIN usuario u ON u.rut = c.rut_instructor "
            "WHERE i.rut_estudiante = %s "
            "ORDER BY i.fecha_inscripcion DESC"
        )
        inscripciones = self.consultar(consulta, (rut_estudiante,))
        
        # Calcular porcentaje para cada curso
        for ins in inscripciones:
            ins["porcentaje_avance"] = self.calcular_porcentaje_avance(ins["id_inscripcion"])
            
        return inscripciones

    def registrar_actividad_completada(self, id_inscripcion, id_actividad, nota=None):
        """Guarda o actualiza la finalizacion de una actividad y su nota."""
        consulta = (
            "INSERT INTO progreso_actividad (id_inscripcion, id_actividad, completada, nota) "
            "VALUES (%s, %s, 1, %s) "
            "ON DUPLICATE KEY UPDATE completada = 1, nota = VALUES(nota)"
        )
        return self.ejecutar(consulta, (id_inscripcion, id_actividad, nota)) > 0

    def calcular_porcentaje_avance(self, id_inscripcion):
        """Calcula el % de avance: (actividades completadas / total actividades publicadas del curso) * 100."""
        # 1. Total actividades publicadas en el curso
        consulta_total = (
            "SELECT COUNT(a.id_actividad) AS total "
            "FROM actividad a "
            "INNER JOIN modulo m ON m.id_modulo = a.id_modulo "
            "INNER JOIN inscripcion i ON i.id_curso = m.id_curso "
            "WHERE i.id_inscripcion = %s AND a.publicada = 1"
        )
        res_total = self.consultar(consulta_total, (id_inscripcion,))
        total_actividades = res_total[0]["total"] if res_total else 0

        if total_actividades == 0:
            return 0.0

        # 2. Actividades completadas por el estudiante
        consulta_completadas = (
            "SELECT COUNT(pa.id_progreso) AS completadas "
            "FROM progreso_actividad pa "
            "INNER JOIN actividad a ON a.id_actividad = pa.id_actividad "
            "WHERE pa.id_inscripcion = %s AND pa.completada = 1 AND a.publicada = 1"
        )
        res_comp = self.consultar(consulta_completadas, (id_inscripcion,))
        completadas = res_comp[0]["completadas"] if res_comp else 0

        return round((completadas / total_actividades) * 100, 1)

    def obtener_detalle_progreso(self, id_inscripcion):
        """Retorna las actividades del curso con el estado de avance del estudiante y sus notas."""
        consulta = (
            "SELECT m.titulo AS modulo_titulo, a.id_actividad, a.titulo AS actividad_titulo, "
            "COALESCE(pa.completada, 0) AS completada, pa.nota "
            "FROM inscripcion i "
            "INNER JOIN modulo m ON m.id_curso = i.id_curso "
            "INNER JOIN actividad a ON a.id_modulo = m.id_modulo "
            "LEFT JOIN progreso_actividad pa ON pa.id_actividad = a.id_actividad AND pa.id_inscripcion = i.id_inscripcion "
            "WHERE i.id_inscripcion = %s AND a.publicada = 1 "
            "ORDER BY m.orden, a.id_actividad"
        )
        return self.consultar(consulta, (id_inscripcion,))

    def pertenece_a_estudiante(self, id_inscripcion, rut_estudiante):
        """Verifica que la inscripcion le pertenezca al estudiante (seguridad/autorizacion)."""
        consulta = (
            "SELECT COUNT(*) AS total FROM inscripcion "
            "WHERE id_inscripcion = %s AND rut_estudiante = %s"
        )
        filas = self.consultar(consulta, (id_inscripcion, rut_estudiante))
        return filas[0]["total"] > 0