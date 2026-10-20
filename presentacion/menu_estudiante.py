"""Capa de presentacion: menu exclusivo del estudiante (Integrante 3).

Permite explorar cursos publicados, inscribirse, marcar actividades como completadas
y consultar calificaciones y % de avance.
"""
from data_base.curso_dao import CursoDAO
from data_base.errores import ErrorBaseDatos
from data_base.inscripcion_dao import InscripcionDAO
from negocio.inscripcion import Inscripcion
from negocio.permisos import (
    AccesoDenegado,
    puede_explorar_cursos,
    requiere_permiso,
)
from negocio.progreso import Progreso

MSG = "Los instructores no pueden usar funciones de estudiante."


def _a_entero(valor):
    """Valida y convierte la entrada a entero."""
    try:
        return int(valor)
    except (TypeError, ValueError):
        raise ValueError("El id debe ser un numero entero.")


@requiere_permiso(puede_explorar_cursos, MSG)
def explorar_cursos(usuario):
    """Lista todos los cursos existentes que se encuentran en estado PUBLICADO."""
    try:
        cursos = CursoDAO().listar_todos()
        publicados = [c for c in cursos if c["estado"] == "publicado"]
        
        if not publicados:
            print("\nNo hay cursos publicados disponibles en este momento.")
            return

        print("\n=== CURSOS DISPONIBLES EN LA PLATAFORMA ===")
        for c in publicados:
            print(f"[{c['id_curso']}] {c['titulo']}")
            print(f"    Instructor: {c['instructor']}")
            if c['descripcion']:
                print(f"    Descripcion: {c['descripcion']}")
            print("-" * 40)
    except ErrorBaseDatos as e:
        print(f"Error de base de datos: {e}")


@requiere_permiso(puede_explorar_cursos, MSG)
def inscribirse(usuario, id_curso_input):
    """Inscribe al estudiante en un curso publicado."""
    try:
        id_curso = _a_entero(id_curso_input)
        
        # Validar que el curso existe y esta publicado
        curso = CursoDAO().buscar_por_id(id_curso)
        if not curso or curso["estado"] != "publicado":
            print("El curso seleccionado no existe o no se encuentra publicado.")
            return

        dao = InscripcionDAO()
        if dao.esta_inscrito(usuario.id, id_curso):
            print(f"Ya te encuentras inscrito en el curso '{curso['titulo']}'.")
            return

        # Validacion del objeto de negocio
        inscripcion = Inscripcion(rut_estudiante=usuario.id, id_curso=id_curso)
        id_ins = dao.inscribir(inscripcion.rut_estudiante, inscripcion.id_curso)
        
        print(f"\n¡Inscripcion exitosa! Te has inscrito en '{curso['titulo']}' (Inscripcion Nº {id_ins}).")
    except ValueError as e:
        print(f"Dato no valido: {e}")
    except ErrorBaseDatos as e:
        print(f"Error de base de datos: {e}")


@requiere_permiso(puede_explorar_cursos, MSG)
def marcar_actividad(usuario):
    """Permite al estudiante marcar una actividad realizada y registrar su nota."""
    try:
        dao = InscripcionDAO()
        mis_cursos = dao.listar_cursos_estudiante(usuario.id)
        if not mis_cursos:
            print("\nNo estas inscrito en ningun curso.")
            return

        print("\n=== MIS CURSOS INSCRITOS ===")
        for c in mis_cursos:
            print(f"[{c['id_inscripcion']}] {c['curso_titulo']} (Avance: {c['porcentaje_avance']}%)")

        id_ins = _a_entero(input("\nIngresa el ID de la INSCRIPCION a trabajar: "))
        if not dao.pertenece_a_estudiante(id_ins, usuario.id):
            print("Esa inscripcion no existe o no te pertenece.")
            return

        actividades = dao.obtener_detalle_progreso(id_ins)
        if not actividades:
            print("Este curso aun no tiene actividades publicadas.")
            return

        print("\n--- Actividades del Curso ---")
        for a in actividades:
            estado = "COMPLETADA" if a["completada"] else "pendiente"
            nota_str = f" | Nota: {a['nota']}" if a['nota'] is not None else ""
            print(f"[{a['id_actividad']}] {a['modulo_titulo']} -> {a['actividad_titulo']} ({estado}{nota_str})")

        id_act = _a_entero(input("\nIngresa el ID de la actividad a completar: "))
        
        # Validar que la actividad pertenezca a este curso
        if not any(a["id_actividad"] == id_act for a in actividades):
            print("Esa actividad no pertenece a tu curso inscrito.")
            return

        str_nota = input("Ingresa tu nota obtenida (1.0 a 7.0, o Presiona ENTER si no aplica): ").strip()
        nota = float(str_nota) if str_nota else None

        # Objeto de negocio valida rango de nota
        progreso = Progreso(id_inscripcion=id_ins, id_actividad=id_act, completada=True, nota=nota)

        dao.registrar_actividad_completada(progreso.id_inscripcion, progreso.id_actividad, progreso.nota)
        print("\n¡Actividad registrada exitosamente!")
        
        # Mostrar nuevo avance %
        nuevo_avance = dao.calcular_porcentaje_avance(id_ins)
        print(f"Tu nuevo porcentaje de avance en el curso es: {nuevo_avance}%")

    except ValueError as e:
        print(f"Dato no valido: {e}")
    except ErrorBaseDatos as e:
        print(f"Error de base de datos: {e}")


@requiere_permiso(puede_explorar_cursos, MSG)
def ver_progreso(usuario):
    """Muestra el resumen de avance y notas detalladas del estudiante."""
    try:
        dao = InscripcionDAO()
        mis_cursos = dao.listar_cursos_estudiante(usuario.id)
        if not mis_cursos:
            print("\nAun no te has inscrito en ningun curso.")
            return

        print(f"\n=== INFORME DE PROGRESO DE {usuario.nombre_usuario.upper()} ===")
        for c in mis_cursos:
            print(f"\nCurso: {c['curso_titulo']} (Instructor: {c['instructor']})")
            print(f"Porcentaje de Avance: [{c['porcentaje_avance']}%]")
            
            actividades = dao.obtener_detalle_progreso(c['id_inscripcion'])
            if not actividades:
                print("  (Sin actividades publicadas)")
                continue

            for a in actividades:
                estado = "✔ Completada" if a["completada"] else "❌ Pendiente"
                nota_str = f" | Nota: {a['nota']}" if a['nota'] is not None else ""
                print(f"   • [{a['modulo_titulo']}] {a['actividad_titulo']}: {estado}{nota_str}")
            print("-" * 50)
    except ErrorBaseDatos as e:
        print(f"Error de base de datos: {e}")


def mostrar_menu_estudiante(usuario):
    """Bucle principal del menu exclusivo del estudiante."""
    print(f"\nBienvenido/a, {usuario.nombre_usuario} (rol: {usuario.rol}).")
    while True:
        print("\n--- MENÚ ESTUDIANTE ---")
        print("1. Explorar cursos disponibles")
        print("2. Inscribirme en un curso")
        print("3. Registrar actividad completada / nota")
        print("4. Ver mi progreso y calificaciones")
        print("5. Cerrar sesion")
        
        opcion = input("Opcion: ").strip()
        try:
            if opcion == "1":
                explorar_cursos(usuario)
            elif opcion == "2":
                explorar_cursos(usuario)
                id_c = input("\nIngresa el ID del curso al que deseas inscribirte: ").strip()
                if id_c:
                    inscribirse(usuario, id_c)
            elif opcion == "3":
                marcar_actividad(usuario)
            elif opcion == "4":
                ver_progreso(usuario)
            elif opcion == "5":
                print("Sesion cerrada.")
                return
            else:
                print("Opcion no valida.")
        except AccesoDenegado as e:
            print(f"Acceso denegado: {e}")
        except ErrorBaseDatos as e:
            print(f"Error de base de datos: {e}")
        except EOFError:
            print("\nEntrada no disponible. Saliendo del menu.")
            return