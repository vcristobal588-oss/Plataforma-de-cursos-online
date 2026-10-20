"""Capa de presentacion: menu exclusivo del estudiante (Integrante 3).

Toda funcion esta protegida con @requiere_permiso(puede_explorar_cursos) y,
ademas, la capa de datos vuelve a verificar que la inscripcion le pertenezca
al estudiante autenticado (metodo buscar_por_id/eliminar con RUT): defensa en
profundidad contra la manipulacion de ids ajenos.

PERSISTENCIA HIBRIDA DEMOSTRADA AQUI:
- catalogo de cursos  -> CursoDAO (mysql-connector-python, libreria oficial)
- inscripciones       -> InscripcionDAO (ORM Peewee, consigna de clases)
Ambas rutas informan los mismos errores (excepcion_para_codigo) y cierran
siempre su sesion (finally en DaoBase / sesion() en Peewee).
"""
from data_base.curso_dao import CursoDAO
from data_base.errores import ErrorBaseDatos, RegistroDuplicado
from data_base.inscripcion_dao import InscripcionDAO
from negocio.inscripcion import Inscripcion
from negocio.permisos import (AccesoDenegado, puede_explorar_cursos,
                              requiere_permiso)
from presentacion.validaciones import a_entero

MSG = "Los instructores no pueden usar funciones de estudiante."


@requiere_permiso(puede_explorar_cursos, MSG)
def explorar_cursos(usuario):
    """Lista el catalogo de cursos PUBLICADOS en los que puede inscribirse."""
    try:
        cursos = CursoDAO().listar_publicados()
    except ErrorBaseDatos as e:
        print(f"Error de base de datos: {e}")
        return []
    if not cursos:
        print("Aun no hay cursos publicados. Vuelva mas tarde.")
        return []
    print("\n--- CURSOS PUBLICADOS ---")
    for curso in cursos:
        print(f"[{curso['id_curso']}] {curso['titulo']}  (instructor: {curso['instructor']})")
        if curso["descripcion"]:
            print(f"      {curso['descripcion']}")
    print("\nUse el id de un curso para inscribirse.")
    return cursos


@requiere_permiso(puede_explorar_cursos, MSG)
def inscribirse(usuario, id_curso):
    """Inscribe al estudiante en el curso indicado. Retorna el id o None."""
    try:
        id_curso = a_entero(id_curso, "El id del curso")
        # El constructor valida RUT e id (capa de negocio) antes de tocar la BD.
        inscripcion = Inscripcion(usuario.id, id_curso)
    except ValueError as e:
        print(f"Dato no valido: {e}")
        return None
    try:
        id_inscripcion = InscripcionDAO().inscribir(
            inscripcion.rut_estudiante,
            inscripcion.id_curso,
            inscripcion.progreso,
            inscripcion.estado,
        )
    except RegistroDuplicado as e:
        print(f"No se pudo inscribir: {e}")
        return None
    except ValueError as e:  # curso no publicado / progreso invalido
        print(f"Dato no valido: {e}")
        return None
    except ErrorBaseDatos as e:
        print(f"Error de base de datos: {e}")
        return None
    print(f"Inscripcion registrada (id {id_inscripcion}) al curso {id_curso}.")
    return id_inscripcion


@requiere_permiso(puede_explorar_cursos, MSG)
def ver_progreso(usuario):
    """Muestra las inscripciones del estudiante con su porcentaje de avance."""
    try:
        filas = InscripcionDAO().listar_por_estudiante(usuario.id)
    except ErrorBaseDatos as e:
        print(f"Error de base de datos: {e}")
        return []
    if not filas:
        print("Aun no estas inscrito en ningun curso. Use la opcion 1 para ver el catalogo.")
        return []
    print(f"\n--- MI PROGRESO ({usuario.nombre_usuario}) ---")
    for fila in filas:
        estado = fila["estado"].upper()
        print(
            f"[{fila['id_inscripcion']}] Curso {fila['id_curso']}: {fila['curso']} | "
            f"progreso {fila['progreso']}% | {estado} | "
            f"inscrito el {fila['fecha_inscripcion']:%d-%m-%Y}"
        )
    return filas


@requiere_permiso(puede_explorar_cursos, MSG)
def actualizar_progreso(usuario, id_inscripcion, valor):
    """Actualiza el progreso de una inscripcion PROPIA. Retorna True si cambio."""
    try:
        id_inscripcion = a_entero(id_inscripcion, "El id de la inscripcion")
        valor = a_entero(valor, "El progreso")
    except ValueError as e:
        print(f"Dato no valido: {e}")
        return False
    try:
        # Con el RUT del sesion: si no es suya, la BD devuelve None (autorizacion).
        fila = InscripcionDAO().buscar_por_id(id_inscripcion, usuario.id)
    except ErrorBaseDatos as e:
        print(f"Error de base de datos: {e}")
        return False
    if fila is None:
        print("La inscripcion no existe o no le pertenece a este estudiante.")
        return False
    try:
        # Se reconstruye el objeto de dominio para que SUS reglas validen
        # el nuevo progreso (0 a 100) antes de persistirlo.
        inscripcion = Inscripcion(
            fila["rut_estudiante"],
            fila["id_curso"],
            id_inscripcion=fila["id_inscripcion"],
            fecha_inscripcion=fila["fecha_inscripcion"],
            progreso=fila["progreso"],
            estado=fila["estado"],
        )
        if not inscripcion.actualizar_progreso(valor):
            print("El progreso no cambio (valor igual al actual).")
            return False
    except ValueError as e:
        print(f"Dato no valido: {e}")
        return False
    try:
        actualizado = InscripcionDAO().actualizar_progreso(
            inscripcion.id, usuario.id, inscripcion.progreso, inscripcion.estado
        )
    except ErrorBaseDatos as e:
        print(f"Error de base de datos: {e}")
        return False
    if actualizado:
        print(
            f"Progreso actualizado a {inscripcion.progreso}% "
            f"(estado: {inscripcion.estado})."
        )
    else:
        print("No se pudo actualizar la inscripcion.")
    return actualizado


@requiere_permiso(puede_explorar_cursos, MSG)
def darse_de_baja(usuario, id_inscripcion):
    """Elimina la inscripcion del estudiante tras confirmar. True si se elimino."""
    try:
        id_inscripcion = a_entero(id_inscripcion, "El id de la inscripcion")
    except ValueError as e:
        print(f"Dato no valido: {e}")
        return False
    if input("Confirma darte de baja de este curso? (s/n): ").strip().lower() != "s":
        print("Operacion cancelada.")
        return False
    try:
        # Segundo argumento = RUT: la capa de datos exige que sea suya.
        eliminada = InscripcionDAO().eliminar(id_inscripcion, usuario.id)
    except ErrorBaseDatos as e:
        print(f"Error de base de datos: {e}")
        return False
    if eliminada:
        print(f"Inscripcion {id_inscripcion} eliminada.")
    else:
        print("La inscripcion no existe o no le pertenece a este estudiante.")
    return eliminada


def mostrar_menu_estudiante(usuario):
    """Bucle principal del menu exclusivo del estudiante."""
    print(f"\nAcceso autorizado al menu de estudiante ({usuario.nombre_usuario}).")
    while True:
        print("\n--- MENU ESTUDIANTE ---")
        print("1. Explorar cursos publicados")
        print("2. Inscribirse a un curso")
        print("3. Ver mi progreso")
        print("4. Actualizar mi progreso")
        print("5. Darme de baja de un curso")
        print("6. Cerrar sesion")
        opcion = input("Opcion: ").strip()
        try:
            if opcion == "1":
                explorar_cursos(usuario)
            elif opcion == "2":
                inscribirse(usuario, input("Id del curso: "))
            elif opcion == "3":
                ver_progreso(usuario)
            elif opcion == "4":
                actualizar_progreso(
                    usuario,
                    input("Id de la inscripcion: "),
                    input("Nuevo progreso (0-100): "),
                )
            elif opcion == "5":
                darse_de_baja(usuario, input("Id de la inscripcion: "))
            elif opcion == "6":
                print("Sesion cerrada.")
                return
            else:
                print("Opcion no valida. Intente de nuevo.")
        except AccesoDenegado as e:
            print(f"Acceso denegado.\n{e}")
        except ErrorBaseDatos as e:
            print(f"Error de base de datos: {e}")
        except ValueError as e:
            print(f"Dato no valido: {e}")
        except (EOFError, KeyboardInterrupt):
            print("\nEntrada no disponible. Saliendo del menu.")
            return
