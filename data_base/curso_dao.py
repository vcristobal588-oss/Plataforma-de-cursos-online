"""DAO de la tabla curso (capa de datos - Integrante 2).

Reutiliza DaoBase (consultar/ejecutar/ejecutar_con_id con rollback y finally).
Todos los SQL usan parametros (?/:nombre): sin concatenacion => sin inyeccion.
"""
from data_base.dao_base import DaoBase
from negocio.curso import Curso
from negocio.modulo import Modulo
from negocio.actividad import Actividad


class CursoDAO(DaoBase):
    """CRUD de la tabla curso."""

    tabla = "curso"
    clave = "id_curso"

    def crear(self, rut_instructor, titulo, descripcion=None):
        """Inserta un curso en borrador y retorna su id (lastrowid)."""
        consulta = (
            "INSERT INTO curso (rut_instructor, titulo, descripcion, estado) "
            "VALUES (%s, %s, %s, 'borrador')"
        )
        return self.ejecutar_con_id(consulta, (rut_instructor, titulo, descripcion))

    def listar_todos(self, estado=None):
        """Retorna todos los cursos con el nombre de su instructor (para catalogos).

        estado=None lista todos; estado='publicado' devuelve el catalogo
        visible para los estudiantes (criterio 2.1.3.G.10: consulta filtrada).
        """
        consulta = (
            "SELECT c.id_curso, c.titulo, c.descripcion, c.estado, "
            "c.rut_instructor, u.nombre_completo AS instructor "
            "FROM curso c "
            "INNER JOIN usuario u ON u.rut = c.rut_instructor "
            "WHERE (%s IS NULL OR c.estado = %s) "
            "ORDER BY c.id_curso"
        )
        return self.consultar(consulta, (estado, estado))

    def listar_publicados(self):
        """Catalogo que ve el estudiante: unicamente cursos publicados."""
        return self.listar_todos(estado="publicado")


    def listar_por_instructor(self, rut_instructor):
        """Retorna las filas de los cursos de un instructor (dicts)."""
        consulta = (
            "SELECT * FROM curso WHERE rut_instructor = %s ORDER BY id_curso"
        )
        return self.consultar(consulta, (rut_instructor,))

    def listar_arbol(self, rut_instructor=None):
        """Retorna la lista de objetos Curso con sus Modulos y Actividades.

        Usa una sola consulta LEFT JOIN (mas eficiente que N+1 consultas)
        y luego agrupa las filas en objetos de negocio (composicion).
        """
        consulta = (
            "SELECT c.id_curso, c.titulo AS curso_titulo, c.descripcion, "
            "c.estado, c.rut_instructor, "
            "m.id_modulo, m.titulo AS modulo_titulo, m.orden, "
            "a.id_actividad, a.titulo AS actividad_titulo, a.publicada "
            "FROM curso c "
            "LEFT JOIN modulo m ON m.id_curso = c.id_curso "
            "LEFT JOIN actividad a ON a.id_modulo = m.id_modulo "
            "WHERE (%s IS NULL OR c.rut_instructor = %s) "
            "ORDER BY c.id_curso, m.orden, a.id_actividad"
        )
        filas = self.consultar(consulta, (rut_instructor, rut_instructor))

        cursos = {}
        for fila in filas:
            id_curso = fila["id_curso"]
            if id_curso not in cursos:
                cursos[id_curso] = Curso(
                    titulo=fila["curso_titulo"],
                    descripcion=fila["descripcion"],
                    rut_instructor=fila["rut_instructor"],
                    id_curso=id_curso,
                    estado=fila["estado"],
                )
            if fila["id_modulo"] is None:
                continue
            curso = cursos[id_curso]
            if not any(m.id == fila["id_modulo"] for m in curso.modulos):
                curso.agregar_modulo(Modulo(
                    titulo=fila["modulo_titulo"],
                    id_curso=id_curso,
                    id_modulo=fila["id_modulo"],
                    orden=fila["orden"],
                ))
            if fila["id_actividad"] is None:
                continue
            modulo = next(m for m in curso.modulos if m.id == fila["id_modulo"])
            modulo.agregar_actividad(Actividad(
                titulo=fila["actividad_titulo"],
                id_modulo=fila["id_modulo"],
                id_actividad=fila["id_actividad"],
                publicada=bool(fila["publicada"]),
            ))
        return list(cursos.values())

    def actualizar(self, id_curso, titulo, descripcion=None):
        """Actualiza titulo y descripcion. Retorna True si hubo filas afectadas."""
        consulta = (
            "UPDATE curso SET titulo = %s, descripcion = %s WHERE id_curso = %s"
        )
        return self.ejecutar(consulta, (titulo, descripcion, id_curso)) > 0

    def publicar(self, id_curso):
        """Cambia estado borrador -> publicado. Retorna False si ya estaba publicado."""
        consulta = (
            "UPDATE curso SET estado = 'publicado' "
            "WHERE id_curso = %s AND estado = 'borrador'"
        )
        return self.ejecutar(consulta, (id_curso,)) > 0

    def eliminar(self, id_curso):
        """Elimina el curso y todo su contenido (actividades, modulos, curso).

        Los tres DELETE corren en la MISMA transaccion: si el ultimo falla,
        los anteriores se revierten (rollback automatico de DaoBase.ejecutar).
        """
        consulta = [
            (
                "DELETE FROM actividad WHERE id_modulo IN "
                "(SELECT id_modulo FROM modulo WHERE id_curso = %s)",
                (id_curso,),
            ),
            ("DELETE FROM modulo WHERE id_curso = %s", (id_curso,)),
            ("DELETE FROM curso WHERE id_curso = %s", (id_curso,)),
        ]
        return self.ejecutar(consulta) > 0

    def pertenece_a(self, id_curso, rut_instructor):
        """True si el curso existe y pertenece al instructor indicado.

        Se usa como control de propiedad (autorizacion) en la capa de datos:
        un instructor jamas puede tocar el curso de otro.
        """
        consulta = (
            "SELECT COUNT(*) AS total FROM curso "
            "WHERE id_curso = %s AND rut_instructor = %s"
        )
        filas = self.consultar(consulta, (id_curso, rut_instructor))
        return filas[0]["total"] > 0
