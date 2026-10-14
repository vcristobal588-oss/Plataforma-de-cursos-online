"""Capa de presentacion: menu principal de autenticacion (Integrante 1)."""
import re

from data_base.errores import ErrorBaseDatos, RegistroDuplicado
from data_base.usuario_dao import UsuarioDAO
from negocio.estudiante import Estudiante
from negocio.instructor import Instructor
from negocio.permisos import (ROL_ESTUDIANTE, ROL_INSTRUCTOR, ROLES_VALIDOS)
from presentacion.menu_estudiante import mostrar_menu_estudiante
from presentacion.menu_instructor import mostrar_menu_instructor

PATRON_RUT = re.compile(r"^\d{7,8}-[\dkK]$")
CONTRASENA_MINIMA = 6


def crear_usuario(datos):
    """Convierte la fila de la BD en el objeto segun su rol. None si el rol es invalido."""
    rol = datos.get("rol")
    if rol == ROL_INSTRUCTOR:
        return Instructor(datos["id"], datos["nombre_usuario"])
    if rol == ROL_ESTUDIANTE:
        return Estudiante(datos["id"], datos["nombre_usuario"])
    return None


def redirigir_por_rol(usuario):
    print(f"Inicio de sesion exitoso.\nUsuario: {usuario.nombre_usuario}\nRol: {usuario.rol}")
    if usuario.rol == ROL_INSTRUCTOR:
        mostrar_menu_instructor(usuario)
    elif usuario.rol == ROL_ESTUDIANTE:
        mostrar_menu_estudiante(usuario)
    else:
        print("Rol no valido. Acceso denegado.")


def iniciar_sesion():
    """Pide correo y contrasena; valida las credenciales contra la BD."""
    try:
        correo = input("Correo: ").strip()
        contrasena = input("Contrasena: ").strip()
        if not correo or not contrasena:
            print("El correo y la contrasena no pueden estar vacios.")
            return
        datos = UsuarioDAO().autenticar(correo, contrasena)
    except ErrorBaseDatos as e:
        print(f"Error de base de datos: {e}")
        return
    if not datos:
        print("Credenciales incorrectas.")
        return
    usuario = crear_usuario(datos)
    if usuario is None:
        print("Rol no valido. Acceso denegado.")
        return
    redirigir_por_rol(usuario)  # al cerrar sesion vuelve aqui (menu principal)


def registrar():
    """Alta de usuario con validacion estricta de cada entrada.

    Cada dato invalido lanza ValueError y se captura sin caer el sistema.
    """
    try:
        rut = input("RUT (ej: 12345678-9): ").strip()
        if not PATRON_RUT.match(rut):
            raise ValueError("RUT con formato invalido. Ejemplo: 12345678-9.")

        nombre = input("Nombre completo: ").strip()
        if not nombre:
            raise ValueError("El nombre completo no puede estar vacio.")

        correo = input("Correo electronico: ").strip()
        if "@" not in correo or correo.startswith("@") or "." not in correo.rsplit("@", 1)[-1]:
            raise ValueError("Correo electronico invalido. Ejemplo: alumno@correo.cl.")

        contrasena = input("Contrasena: ").strip()
        if len(contrasena) < CONTRASENA_MINIMA:
            raise ValueError(f"La contrasena debe tener al menos {CONTRASENA_MINIMA} caracteres.")

        rol = input("Rol (instructor/estudiante): ").strip().lower()
        if rol not in ROLES_VALIDOS:
            raise ValueError(f"Rol invalido. Debe ser {ROL_INSTRUCTOR} o {ROL_ESTUDIANTE}.")

        detalle = input("Carrera (estudiante) o especialidad (instructor): ").strip() or None

        UsuarioDAO().registrar(rut, nombre, correo, contrasena, rol, detalle)
    except ValueError as e:
        print(f"Dato no valido: {e}")
    except RegistroDuplicado as e:
        print(f"No se pudo registrar: {e}")
    except ErrorBaseDatos as e:
        print(f"Error de base de datos: {e}")
    else:
        print("Usuario registrado correctamente. Ya puede iniciar sesion.")


def menu_principal():
    while True:
        print("\n=== PLATAFORMA DE CURSOS ===\n1. Iniciar sesion\n2. Registrarse\n3. Salir")
        try:
            opcion = int(input("Opcion: ").strip())
        except ValueError:
            print("Debe ingresar un numero de opcion (1-3).")
            continue
        except EOFError:
            print("\nEntrada no disponible. Saliendo.")
            break
        try:
            if opcion == 1:
                iniciar_sesion()
            elif opcion == 2:
                registrar()
            elif opcion == 3:
                print("Hasta pronto.")
                break
            else:
                print("Opcion no valida.")
        except ErrorBaseDatos as e:
            print(f"Error de base de datos: {e}")


if __name__ == "__main__":
    menu_principal()
