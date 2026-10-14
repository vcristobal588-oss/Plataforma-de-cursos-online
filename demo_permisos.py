"""Evidencia: un estudiante intenta crear un curso (sin necesitar BD)."""
from negocio.estudiante import Estudiante
from negocio.instructor import Instructor
from negocio.permisos import AccesoDenegado
from presentacion.menu_instructor import crear_curso
 
for u in (Instructor(1, "instructor01"), Estudiante(2, "estudiante01")):
    print(f"\nUsuario: {u.nombre_usuario} | Rol: {u.rol}")
    try:
        crear_curso(u, "Python básico")
    except AccesoDenegado as e:
        print(f"Acceso denegado.\n{e}")
 