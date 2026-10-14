from negocio.permisos import (AccesoDenegado, puede_administrar_cursos,
                              requiere_permiso)
 
MSG = "Los estudiantes no pueden administrar cursos."
 
 
# --- Operaciones protegidas (validan el rol aunque se llamen directamente) ---
@requiere_permiso(puede_administrar_cursos, MSG)
def crear_curso(usuario, titulo):
    # TODO: llamar a la lógica/DAO de cursos (integrante 2)
    print(f"Curso '{titulo}' creado por {usuario.nombre_usuario}.")
 
 
@requiere_permiso(puede_administrar_cursos, MSG)
def agregar_modulo(usuario, curso, titulo):
    # TODO: integrante 2
    print(f"Módulo '{titulo}' agregado a '{curso}'.")
 
 
@requiere_permiso(puede_administrar_cursos, MSG)
def agregar_actividad(usuario, modulo, titulo):
    # TODO: integrante 3
    print(f"Actividad '{titulo}' agregada a '{modulo}'.")
 
 
def mostrar_menu_instructor(usuario):
    print(f"\nAcceso autorizado al menú de instructor ({usuario.nombre_usuario}).")
    while True:
        print("\n--- MENÚ INSTRUCTOR ---\n1. Crear curso\n2. Agregar módulo"
              "\n3. Agregar actividad\n4. Cerrar sesión")
        opcion = input("Opción: ").strip()
        try:
            if opcion == "1":
                crear_curso(usuario, input("Título del curso: "))
            elif opcion == "2":
                agregar_modulo(usuario, input("Curso: "), input("Título del módulo: "))
            elif opcion == "3":
                agregar_actividad(usuario, input("Módulo: "), input("Título de la actividad: "))
            elif opcion == "4":
                print("Sesión cerrada.")
                return
            else:
                print("Opción no válida.")
        except AccesoDenegado as e:
            print(f"Acceso denegado.\n{e}")