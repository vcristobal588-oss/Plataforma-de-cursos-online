"""Autorización centralizada: la usan los menús Y las operaciones sensibles."""
from functools import wraps
 
ROL_INSTRUCTOR = "instructor"
ROL_ESTUDIANTE = "estudiante"
ROLES_VALIDOS = (ROL_INSTRUCTOR, ROL_ESTUDIANTE)
 
 
class AccesoDenegado(Exception):
    pass
 
 
def _rol(usuario):
    return usuario.rol if usuario is not None else None
 
 
def esta_autenticado(usuario):
    return _rol(usuario) in ROLES_VALIDOS
 
 
def puede_administrar_cursos(usuario):
    return _rol(usuario) == ROL_INSTRUCTOR
 
 
def puede_explorar_cursos(usuario):
    return _rol(usuario) == ROL_ESTUDIANTE
 
 
def requiere_permiso(verificador, mensaje):
    """Decorador: la función protegida recibe 'usuario' como primer argumento."""
    def decorador(funcion):
        @wraps(funcion)
        def envoltura(usuario, *args, **kwargs):
            if not verificador(usuario):
                raise AccesoDenegado(mensaje)
            return funcion(usuario, *args, **kwargs)
        return envoltura
    return decorador