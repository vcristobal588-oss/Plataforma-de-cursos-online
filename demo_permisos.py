"""Evidencia: permisos exclusivos del instructor para crear cursos.

Usa la base de datos real: registra un instructor temporal, crea un curso
con el (el decorator @requiere_permiso deja pasar a los instructores) y
verifica que un estudiante reciba AccesoDenegado. Limpia todo al finalizar.

Uso: python demo_permisos.py
"""
from data_base.errores import ErrorBaseDatos
from data_base.usuario_dao import UsuarioDAO
from data_base.curso_dao import CursoDAO
from negocio.estudiante import Estudiante
from negocio.instructor import Instructor
from negocio.permisos import AccesoDenegado
from presentacion.menu_instructor import crear_curso

RUT_INSTRUCTOR = "20111222-3"


def _limpiar(rut):
    """Elimina los cursos y el usuario temporal (idempotente)."""
    try:
        for fila in CursoDAO().listar_por_instructor(rut):
            CursoDAO().eliminar(fila["id_curso"])
        UsuarioDAO().eliminar(rut)
    except ErrorBaseDatos as e:
        print(f"[aviso] limpieza: {e}")


def main():
    dao = UsuarioDAO()
    _limpiar(RUT_INSTRUCTOR)  # por si una corrida anterior quedo a medias
    try:
        dao.registrar(
            RUT_INSTRUCTOR, "Instructor Permisos", "demo.permisos@plataforma.cl",
            "clave1234", "instructor", "Docencia",
        )
        usuarios = (
            Instructor(RUT_INSTRUCTOR, "Instructor Permisos"),
            Estudiante("33444555-6", "estudiante01"),
        )
        for u in usuarios:
            print(f"\nUsuario: {u.nombre_usuario} | Rol: {u.rol}")
            try:
                crear_curso(u, "Python basico")
            except AccesoDenegado as e:
                print("Acceso denegado.")
                print(e)
        print("\nEl instructor creo su curso; el estudiante fue bloqueado. OK")
    finally:
        _limpiar(RUT_INSTRUCTOR)
        print("Limpieza final: usuario temporal y sus cursos eliminados.")


if __name__ == "__main__":
    main()
