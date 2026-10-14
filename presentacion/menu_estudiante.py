from negocio.permisos import (AccesoDenegado, puede_explorar_cursos,
                              requiere_permiso)
 
MSG = "Los instructores no pueden usar funciones de estudiante."
 
 
@requiere_permiso(puede_explorar_cursos, MSG)
def explorar_cursos(usuario):
    # TODO: integrante 2/3
    print("Listado de cursos disponibles...")
 
 
@requiere_permiso(puede_explorar_cursos, MSG)
def inscribirse(usuario, curso):
    # TODO: integrante 3
    print(f"{usuario.nombre_usuario} inscrito en '{curso}'.")
 
 
@requiere_permiso(puede_explorar_cursos, MSG)
def ver_progreso(usuario):
    # TODO: integrante 3
    print("Progreso y calificaciones...")
 
 
def mostrar_menu_estudiante(usuario):
    print(f"\nAcceso autorizado al menú de estudiante ({usuario.nombre_usuario}).")
    while True:
        print("\n--- MENÚ ESTUDIANTE ---\n1. Explorar cursos\n2. Inscribirse"
              "\n3. Ver progreso\n4. Cerrar sesión")
        opcion = input("Opción: ").strip()
        try:
            if opcion == "1":
                explorar_cursos(usuario)
            elif opcion == "2":
                inscribirse(usuario, input("Curso: "))
            elif opcion == "3":
                ver_progreso(usuario)
            elif opcion == "4":
                print("Sesión cerrada.")
                return
            else:
                print("Opción no válida.")
        except AccesoDenegado as e:
            print(f"Acceso denegado.\n{e}")