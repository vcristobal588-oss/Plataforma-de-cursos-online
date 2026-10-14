"""Evidencia Integrante 2: CRUD completo de cursos, modulos y actividades.

Cubre los criterios:
  2.1.1 -> clases Curso/Modulo/Actividad con atributos privados y @property
  2.1.2 -> composicion (Curso.agregar_modulo, Modulo.agregar_actividad)
  2.1.3 -> DAOs con SQL parametrizado sobre curso/modulo/actividad
  2.1.4 -> try/except/finally con rollback y validacion de entradas
  2.1.5 -> permisos de instructor (decorador + pertenece_a) y FK en BD

Uso: python demo_cursos.py
"""
from data_base.actividad_dao import ActividadDAO
from data_base.curso_dao import CursoDAO
from data_base.errores import ErrorBaseDatos
from data_base.modulo_dao import ModuloDAO
from data_base.usuario_dao import UsuarioDAO
from negocio.actividad import Actividad
from negocio.curso import Curso
from negocio.estudiante import Estudiante
from negocio.instructor import Instructor
from negocio.modulo import Modulo
from negocio.permisos import AccesoDenegado
from presentacion.menu_instructor import agregar_modulo, crear_curso, publicar_curso

RUT = "20999888-7"
CORREO = "demo.cursos@plataforma.cl"
NOMBRE = "Instructor Cursos"


def resultado(nombre, ok):
    print(f"[{'OK ' if ok else 'FALLA'}] {nombre}")
    return 0 if ok else 1


def _limpiar(rut):
    """Elimina los cursos y el usuario temporal (idempotente)."""
    try:
        for fila in CursoDAO().listar_por_instructor(rut):
            CursoDAO().eliminar(fila["id_curso"])
        UsuarioDAO().eliminar(rut)
    except ErrorBaseDatos as e:
        print(f"[aviso] limpieza: {e}")


def main():
    fallos = 0
    dao_usuario = UsuarioDAO()
    dao_curso = CursoDAO()
    dao_modulo = ModuloDAO()
    dao_actividad = ActividadDAO()

    _limpiar(RUT)  # por si una corrida anterior quedo a medias
    try:
        # --- 1. Instructor temporal real (usuario + fila instructor, atomicos) ---
        print("== Integrante 2 - CRUD cursos/modulos/actividades ==")
        print("\n== Preparacion: instructor temporal ==")
        nuevo = dao_usuario.registrar(RUT, NOMBRE, CORREO, "clave1234", "instructor", "Software")
        fallos += resultado("Registro atomico de instructor (usuario + instructor)", bool(nuevo))

        # --- 2. dominio: encapsulamiento y validaciones (2.1.1 / 2.1.2) ---
        print("\n== Dominio: Curso / Modulo / Actividad ==")
        curso = Curso("Python basico", "Intro a Python", rut_instructor=RUT)
        fallos += resultado("Curso valido se construye con @property", curso.titulo == "Python basico" and not curso.esta_publicado)
        fallos += resultado("Curso sin titulo lanza ValueError", _lanza(ValueError, Curso, ""))
        fallos += resultado("Estado invalido lanza ValueError", _lanza(ValueError, Curso, "X", estado="inventado"))
        fallos += resultado("Curso.publicar() hace la transicion borrador -> publicado",
                            curso.publicar() and curso.esta_publicado)
        fallos += resultado("Curso.publicar() dos veces retorna False (idempotente)", curso.publicar() is False)
        modulo = Modulo("Variables", id_curso=1, orden=1)
        actividad = Actividad("Tarea 1", id_modulo=1)
        fallos += resultado("Modulo sin titulo lanza ValueError", _lanza(ValueError, Modulo, ""))
        fallos += resultado("Actividad sin titulo lanza ValueError", _lanza(ValueError, Actividad, ""))
        fallos += resultado("Actividad.publicar() cambia publicada", actividad.publicar() and actividad.publicada)
        curso2 = Curso("Dominio", rut_instructor=RUT)
        curso2.agregar_modulo(modulo)
        modulo.agregar_actividad(actividad)
        fallos += resultado("Composicion Curso -> Modulo -> Actividad",
                            len(curso2.modulos) == 1 and len(modulo.actividades) == 1)
        fallos += resultado("Agregar objeto no valido lanza TypeError",
                            _lanza(TypeError, curso2.agregar_modulo, "no soy modulo"))

        # --- 3. CRUD de base de datos (2.1.3) ---
        print("\n== Datos: CRUD con SQL parametrizado ==")
        id_curso = dao_curso.crear(RUT, "Python basico", "Intro a Python")
        fallos += resultado("CursoDAO.crear retorna id > 0", bool(id_curso) and id_curso > 0)
        fila = dao_curso.buscar_por_id(id_curso)
        fallos += resultado("CursoDAO.buscar_por_id (lectura) con estado borrador",
                            fila is not None and fila["estado"] == "borrador")
        fallos += resultado("Curso con instructor inexistente lanza ErrorBaseDatos (FK 1452)",
                            _lanza(ErrorBaseDatos, dao_curso.crear, "99999999-9", "Hack"))
        fallos += resultado("CursoDAO.listar_todos muestra el curso", any(f["id_curso"] == id_curso for f in dao_curso.listar_todos()))

        id_modulo_1 = dao_modulo.crear(id_curso, "Variables")
        id_modulo_2 = dao_modulo.crear(id_curso, "Condicionales")
        modulos = dao_modulo.listar_por_curso(id_curso)
        fallos += resultado("ModuloDAO.crear autoasigna orden 1 y 2",
                            len(modulos) == 2 and modulos[0]["orden"] == 1 and modulos[1]["orden"] == 2)
        fallos += resultado("Modulo con curso inexistente lanza ErrorBaseDatos (FK 1452)",
                            _lanza(ErrorBaseDatos, dao_modulo.crear, 999999, "Hack"))

        id_actividad_1 = dao_actividad.crear(id_modulo_1, "Tarea variables")
        id_actividad_2 = dao_actividad.crear(id_modulo_1, "Mini proyecto")
        fallos += resultado("ActividadDAO.crear y listar_por_modulo",
                            len(dao_actividad.listar_por_modulo(id_modulo_1)) == 2)

        fallos += resultado("CursoDAO.actualizar (titulo/descripcion)",
                            dao_curso.actualizar(id_curso, "Python basico v2", "Actualizado")
                            and dao_curso.buscar_por_id(id_curso)["titulo"] == "Python basico v2")
        fallos += resultado("ModuloDAO.actualizar (titulo)",
                            dao_modulo.actualizar(id_modulo_1, "Variables y tipos"))

        # --- 4. publicar via DAO y arbol compuesto (2.1.1 / 2.1.5) ---
        print("\n== Publicacion y arbol de contenidos ==")
        fallos += resultado("CursoDAO.publicar (borrador -> publicado)", dao_curso.publicar(id_curso))
        fallos += resultado("CursoDAO.publicar dos veces retorna False (idempotente)",
                            dao_curso.publicar(id_curso) is False)
        fallos += resultado("ActividadDAO.publicar (0 -> 1)", dao_actividad.publicar(id_actividad_1))
        arbol = dao_curso.listar_arbol(RUT)
        fallos += resultado("listar_arbol: un curso con 2 modulos", len(arbol) == 1 and len(arbol[0].modulos) == 2)
        fallos += resultado("listar_arbol: composicion con 2 actividades en el modulo 1",
                            len(arbol[0].modulos[0].actividades) == 2)
        fallos += resultado("listar_arbol: estados publicados correctos",
                            arbol[0].esta_publicado and arbol[0].modulos[0].actividades[0].publicada)

        # --- 5. autorizacion: propiedad del instructor y roles (2.1.5) ---
        print("\n== Autorizacion: propiedad y roles ==")
        fallos += resultado("pertenece_a True para el dueno", dao_curso.pertenece_a(id_curso, RUT))
        fallos += resultado("pertenece_a False para otro instructor",
                            not dao_curso.pertenece_a(id_curso, "99999999-9"))
        fallos += resultado("pertenece_a en modulo y actividad",
                            dao_modulo.pertenece_a(id_modulo_1, RUT)
                            and dao_actividad.pertenece_a(id_actividad_2, RUT))
        instructor_ajeno = Instructor("99999999-9", "instructor02")
        res = agregar_modulo(instructor_ajeno, id_curso, "Intento de intrusion")
        fallos += resultado("Menu bloquea modulo en curso ajeno (pertenece_a)",
                            res is None and len(dao_modulo.listar_por_curso(id_curso)) == 2)
        estudiante = Estudiante("33444555-6", "estudiante01")
        fallos += resultado("Menu lanza AccesoDenegado para estudiante",
                            _lanza(AccesoDenegado, crear_curso, estudiante, "Hack"))
        fallos += resultado("Menu lanza AccesoDenegado para estudiante (publicar_curso)",
                            _lanza(AccesoDenegado, publicar_curso, estudiante, id_curso))

        # --- 6. eliminar curso en cascada y proteccion FK (2.1.3 / 2.1.5) ---
        print("\n== Eliminar en cascada y proteccion FK ==")
        fallos += resultado("UsuarioDAO.eliminar instructor con cursos lanza ErrorBaseDatos (FK 1451)",
                            _lanza(ErrorBaseDatos, dao_usuario.eliminar, RUT))
        fallos += resultado("CursoDAO.eliminar borra curso + modulos + actividades",
                            dao_curso.eliminar(id_curso)
                            and dao_curso.buscar_por_id(id_curso) is None
                            and dao_modulo.listar_por_curso(id_curso) == []
                            and dao_actividad.listar_por_modulo(id_modulo_1) == [])
        fallos += resultado("Tras eliminar, el instructor si puede borrarse (FK liberada)",
                            dao_usuario.eliminar(RUT) and not dao_usuario.buscar_por_rut(RUT))

        print(f"\n{'='*50}\nRESULTADO: {'TODOS LOS TESTS PASARON' if fallos == 0 else f'{fallos} FALLAS'}")
    finally:
        _limpiar(RUT)
        print("Limpieza: la BD quedo en su estado original.")


def _lanza(excepcion, funcion, *args, **kwargs):
    """True si funcion(*args) lanza la excepcion esperada."""
    try:
        funcion(*args, **kwargs)
    except excepcion:
        return True
    return False


if __name__ == "__main__":
    main()
