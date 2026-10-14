"""Capa de presentacion: menu exclusivo del instructor (Integrante 2).

Toda operacion esta protegida con @requiere_permiso(puede_administrar_cursos)
y, ademas, la capa de datos valida que el curso/modulo/actividad le
pertenezca al instructor autenticado (metodos pertenece_a): defensa en
profundidad contra manipulacion de ids ajenos.
"""
from data_base.errores import ErrorBaseDatos
from data_base.curso_dao import CursoDAO
from data_base.modulo_dao import ModuloDAO
from data_base.actividad_dao import ActividadDAO
from negocio.actividad import Actividad
from negocio.curso import Curso
from negocio.modulo import Modulo
from negocio.permisos import (
    AccesoDenegado,
    puede_administrar_cursos,
    requiere_permiso,
)

MSG = "Los estudiantes no pueden administrar cursos."


def _a_entero(valor):
    """Convierte un valor de entrada a entero. Lanza ValueError si no es numerico."""
    try:
        return int(valor)
    except (TypeError, ValueError):
        raise ValueError("El id debe ser un numero entero.")


@requiere_permiso(puede_administrar_cursos, MSG)
def crear_curso(usuario, titulo, descripcion=None):
    """Crea un curso en borrador a nombre del instructor autenticado."""
    try:
        # El constructor de Curso valida el titulo (capa de negocio).
        curso = Curso(titulo, descripcion or "", rut_instructor=usuario.id)
    except ValueError as e:
        print(f"Dato no valido: {e}")
        return None
    try:
        id_curso = CursoDAO().crear(usuario.id, curso.titulo, curso.descripcion)
    except ErrorBaseDatos as e:
        print(f"Error de base de datos: {e}")
        return None
    print(f"Curso '{curso.titulo}' creado con id {id_curso} (borrador).")
    return id_curso


@requiere_permiso(puede_administrar_cursos, MSG)
def ver_cursos(usuario):
    """Muestra el arbol de cursos -> modulos -> actividades del instructor."""
    try:
        cursos = CursoDAO().listar_arbol(usuario.id)
    except ErrorBaseDatos as e:
        print(f"Error de base de datos: {e}")
        return
    if not cursos:
        print("Aun no tiene cursos creados.")
        return
    for c in cursos:
        estado = "PUBLICADO" if c.esta_publicado else "borrador"
        print(f"\n[{c.id}] {c.titulo} ({estado})")
        if c.descripcion:
            print(f"    Descripcion: {c.descripcion}")
        if not c.modulos:
            print("    (sin modulos)")
            continue
        for m in c.modulos:
            print(f"    [{m.id}] Modulo {m.orden}: {m.titulo}")
            if not m.actividades:
                print("        (sin actividades)")
                continue
            for a in m.actividades:
                estado_a = "publicada" if a.publicada else "borrador"
                print(f"        [{a.id}] {a.titulo} ({estado_a})")


@requiere_permiso(puede_administrar_cursos, MSG)
def agregar_modulo(usuario, id_curso, titulo):
    """Agrega un modulo a un curso propio del instructor autenticado."""
    try:
        id_curso = _a_entero(id_curso)
        # El constructor de Modulo valida el titulo (capa de negocio).
        modulo = Modulo(titulo, id_curso=id_curso)
    except (TypeError, ValueError) as e:
        print(f"Dato no valido: {e}")
        return None
    if not CursoDAO().pertenece_a(id_curso, usuario.id):
        print("El curso no existe o no le pertenece a este instructor.")
        return None
    try:
        id_modulo = ModuloDAO().crear(id_curso, modulo.titulo)
    except ErrorBaseDatos as e:
        print(f"Error de base de datos: {e}")
        return None
    print(f"Modulo '{modulo.titulo}' agregado al curso {id_curso} (id {id_modulo}).")
    return id_modulo


@requiere_permiso(puede_administrar_cursos, MSG)
def agregar_actividad(usuario, id_modulo, titulo):
    """Agrega una actividad a un modulo de un curso propio del instructor."""
    try:
        id_modulo = _a_entero(id_modulo)
        # El constructor de Actividad valida el titulo (capa de negocio).
        actividad = Actividad(titulo, id_modulo=id_modulo)
    except (TypeError, ValueError) as e:
        print(f"Dato no valido: {e}")
        return None
    if not ModuloDAO().pertenece_a(id_modulo, usuario.id):
        print("El modulo no existe o no le pertenece a este instructor.")
        return None
    try:
        id_actividad = ActividadDAO().crear(id_modulo, actividad.titulo)
    except ErrorBaseDatos as e:
        print(f"Error de base de datos: {e}")
        return None
    print(f"Actividad '{actividad.titulo}' agregada al modulo {id_modulo} (id {id_actividad}).")
    return id_actividad


@requiere_permiso(puede_administrar_cursos, MSG)
def publicar_curso(usuario, id_curso):
    """Publica un curso propio del instructor (borrador -> publicado)."""
    try:
        id_curso = _a_entero(id_curso)
    except (TypeError, ValueError) as e:
        print(f"Dato no valido: {e}")
        return False
    if not CursoDAO().pertenece_a(id_curso, usuario.id):
        print("El curso no existe o no le pertenece a este instructor.")
        return False
    try:
        publicado = CursoDAO().publicar(id_curso)
    except ErrorBaseDatos as e:
        print(f"Error de base de datos: {e}")
        return False
    if publicado:
        print(f"Curso {id_curso} publicado. Ya es visible para los estudiantes.")
    else:
        print(f"El curso {id_curso} ya estaba publicado.")
    return publicado


@requiere_permiso(puede_administrar_cursos, MSG)
def publicar_actividad(usuario, id_actividad):
    """Publica una actividad de un curso propio del instructor."""
    try:
        id_actividad = _a_entero(id_actividad)
    except (TypeError, ValueError) as e:
        print(f"Dato no valido: {e}")
        return False
    if not ActividadDAO().pertenece_a(id_actividad, usuario.id):
        print("La actividad no existe o no le pertenece a este instructor.")
        return False
    try:
        publicada = ActividadDAO().publicar(id_actividad)
    except ErrorBaseDatos as e:
        print(f"Error de base de datos: {e}")
        return False
    if publicada:
        print(f"Actividad {id_actividad} publicada.")
    else:
        print(f"La actividad {id_actividad} ya estaba publicada.")
    return publicada


@requiere_permiso(puede_administrar_cursos, MSG)
def eliminar_curso(usuario, id_curso):
    """Elimina un curso propio con todo su contenido (accion destructiva)."""
    try:
        id_curso = _a_entero(id_curso)
    except (TypeError, ValueError) as e:
        print(f"Dato no valido: {e}")
        return False
    if not CursoDAO().pertenece_a(id_curso, usuario.id):
        print("El curso no existe o no le pertenece a este instructor.")
        return False
    if input("Confirma eliminar el curso y todo su contenido? (s/n): ").strip().lower() != "s":
        print("Operacion cancelada.")
        return False
    try:
        eliminado = CursoDAO().eliminar(id_curso)
    except ErrorBaseDatos as e:
        print(f"Error de base de datos: {e}")
        return False
    if eliminado:
        print(f"Curso {id_curso} eliminado junto con sus modulos y actividades.")
    else:
        print(f"No se pudo eliminar el curso {id_curso}.")
    return eliminado


def mostrar_menu_instructor(usuario):
    """Bucle principal del menu exclusivo del instructor."""
    print(f"\nBienvenido, {usuario.nombre_usuario} (rol: {usuario.rol}).")
    while True:
        print("\n--- MENU INSTRUCTOR ---")
        print("1. Crear curso")
        print("2. Ver mis cursos (arbol)")
        print("3. Agregar modulo a un curso")
        print("4. Agregar actividad a un modulo")
        print("5. Publicar curso")
        print("6. Publicar actividad")
        print("7. Eliminar curso")
        print("8. Cerrar sesion")
        opcion = input("Opcion: ").strip()
        try:
            if opcion == "1":
                titulo = input("Titulo del curso: ")
                descripcion = input("Descripcion (opcional): ")
                crear_curso(usuario, titulo, descripcion or None)
            elif opcion == "2":
                ver_cursos(usuario)
            elif opcion == "3":
                agregar_modulo(usuario, input("Id del curso: "), input("Titulo del modulo: "))
            elif opcion == "4":
                agregar_actividad(usuario, input("Id del modulo: "), input("Titulo de la actividad: "))
            elif opcion == "5":
                publicar_curso(usuario, input("Id del curso: "))
            elif opcion == "6":
                publicar_actividad(usuario, input("Id de la actividad: "))
            elif opcion == "7":
                eliminar_curso(usuario, input("Id del curso: "))
            elif opcion == "8":
                print("Sesion cerrada.")
                return
            else:
                print("Opcion no valida. Intente de nuevo.")
        except AccesoDenegado as e:
            print("Acceso denegado.")
            print(e)
        except ErrorBaseDatos as e:
            print(f"Error de base de datos: {e}")
        except ValueError as e:
            print(f"Dato no valido: {e}")
        except EOFError:
            print("\nEntrada no disponible. Saliendo del menu.")
            return
