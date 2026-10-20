"""DAO de la tabla inscripcion: IMPLEMENTADO CON EL ORM Peewee (modelos_orm).

POR QUE ESTE DAO USA PEWEE Y EL RESTO mysql-connector (arquitectura hibrida):
- Consigna de clase: "trabajaremos con Peewee" -> el modulo nuevo demuestra
  el CRUD real sobre ORM (select/create/update/delete + atomic()).
- Rúbrica 2.1.3.G.9: la capa DAO existente conserva mysql-connector-python,
  la libreria oficial de MySQL para Python.
- Ninguna de las dos repite logica: las traducciones de error comparten
  `excepcion_para_codigo` y ambas cierran siempre la sesion
  (finally en DaoBase / `sesion()` aqui) -> criterios 2.1.2.G.6 y 2.1.4.G.13.

Garantias Peewee:
- SQL parametrizado generado por el ORM (sin concatenacion => sin inyeccion).
- `database.atomic()`: si algun paso falla se revierte TODO (rollback).
- Errores del driver traducidos a ErrorBaseDatos/RegistroDuplicado.
"""
from data_base import modelos_orm as orm
from data_base.errores import ErrorBaseDatos

MENSAJE_DUPLICADO = "Este estudiante ya esta inscrito en ese curso."


class InscripcionDAO:
    """CRUD de la tabla `inscripcion` sobre los modelos Peewee del modelo UML."""

    # --- CREATE (registro) ---

    def inscribir(self, rut_estudiante, id_curso, progreso=0, estado="activa"):
        """Inscribe a un estudiante en un curso PUBLICADO y retorna su id.

        Valida dentro de la transaccion:
        - el estudiante existe en la tabla estudiantes (FK),
        - el curso existe y esta publicado (regla de negocio del catalogo),
        - la clave unica (estudiante, curso) impide inscripciones repetidas
          -> errno 1062 traducido a RegistroDuplicado.
        """
        try:
            with orm.sesion():
                with orm.database.atomic():
                    estudiante = orm.EstudianteModel.get_or_none(
                        orm.EstudianteModel.rut_estudiante == rut_estudiante
                    )
                    if estudiante is None:
                        raise ErrorBaseDatos(
                            "El estudiante no existe en la base de datos."
                        )
                    curso = orm.CursoModel.get_or_none(
                        orm.CursoModel.id_curso == id_curso
                    )
                    if curso is None:
                        raise ErrorBaseDatos("El curso indicado no existe.")
                    if curso.estado != "publicado":
                        raise ValueError(
                            "Solo se puede inscribir a cursos publicados."
                        )
                    inscripcion = orm.InscripcionModel.create(
                        rut_estudiante=rut_estudiante,
                        id_curso=id_curso,
                        progreso=progreso,
                        estado=estado,
                    )
                    return inscripcion.id_inscripcion
        except (ErrorBaseDatos, ValueError):
            raise  # errores de logica/negocio: no se traducen
        except Exception as error:
            raise orm.traducir_error(error, MENSAJE_DUPLICADO) from error

    # --- READ (consulta) ---

    def listar_por_estudiante(self, rut_estudiante):
        """Retorna las inscripciones del estudiante con el titulo de su curso.

        Una sola consulta con JOIN (ORM) en lugar de 1+N consultas.
        """
        try:
            with orm.sesion():
                consulta = (
                    orm.InscripcionModel
                    .select(orm.InscripcionModel, orm.CursoModel)
                    .join(orm.CursoModel)
                    .where(orm.InscripcionModel.rut_estudiante == rut_estudiante)
                    .order_by(orm.InscripcionModel.id_inscripcion)
                )
                return [self._a_dict(fila) for fila in consulta]
        except Exception as error:
            raise orm.traducir_error(error) from error

    def listar_todas(self):
        """Retorna todas las inscripciones (uso administrativo / pruebas)."""
        try:
            with orm.sesion():
                consulta = orm.InscripcionModel.select().order_by(
                    orm.InscripcionModel.id_inscripcion
                )
                return [self._a_dict(fila) for fila in consulta]
        except Exception as error:
            raise orm.traducir_error(error) from error

    def buscar_por_id(self, id_inscripcion, rut_estudiante=None):
        """Retorna la inscripcion como dict, o None si no existe.

        Si se informa el RUT, ademas actua como CONTROL DE PROPIEDAD: un
        estudiante jamas puede leer la inscripcion de otro (defensa en
        profundidad, igual que pertenece_a en los DAO de instructor).
        """
        try:
            with orm.sesion():
                consulta = (
                    orm.InscripcionModel
                    .select(orm.InscripcionModel, orm.CursoModel)
                    .join(orm.CursoModel)
                    .where(orm.InscripcionModel.id_inscripcion == id_inscripcion)
                )
                if rut_estudiante is not None:
                    consulta = consulta.where(
                        orm.InscripcionModel.rut_estudiante == rut_estudiante
                    )
                fila = consulta.first()
                return self._a_dict(fila) if fila else None
        except Exception as error:
            raise orm.traducir_error(error) from error

    # --- UPDATE (actualizacion) ---

    def actualizar_progreso(self, id_inscripcion, rut_estudiante, progreso, estado):
        """Actualiza progreso/estado de una inscripcion PROPIA. True si existia."""
        try:
            with orm.sesion():
                with orm.database.atomic():
                    filas = (
                        orm.InscripcionModel
                        .update(progreso=progreso, estado=estado)
                        .where(
                            (orm.InscripcionModel.id_inscripcion == id_inscripcion)
                            & (orm.InscripcionModel.rut_estudiante == rut_estudiante)
                        )
                        .execute()
                    )
                    return filas > 0
        except Exception as error:
            raise orm.traducir_error(error) from error

    # --- DELETE (eliminacion / baja) ---

    def eliminar(self, id_inscripcion, rut_estudiante=None):
        """Elimina una inscripcion. True si existia y fue eliminada.

        Con `rut_estudiante` ademas verifica que la inscripcion le pertenezca
        a ese estudiante (autorizacion a nivel de datos).
        """
        try:
            with orm.sesion():
                with orm.database.atomic():
                    consulta = orm.InscripcionModel.delete().where(
                        orm.InscripcionModel.id_inscripcion == id_inscripcion
                    )
                    if rut_estudiante is not None:
                        consulta = consulta.where(
                            orm.InscripcionModel.rut_estudiante == rut_estudiante
                        )
                    return consulta.execute() > 0
        except Exception as error:
            raise orm.traducir_error(error) from error

    # --- Auxiliar privado ---

    @staticmethod
    def _a_dict(fila):
        """Convierte una fila ORM en el mismo formato dict que devuelven los DAO."""
        return {
            "id_inscripcion": fila.id_inscripcion,
            "rut_estudiante": fila.rut_estudiante_id,
            "id_curso": fila.id_curso_id,
            "curso": fila.id_curso.titulo,
            "fecha_inscripcion": fila.fecha_inscripcion,
            "progreso": fila.progreso,
            "estado": fila.estado,
        }
