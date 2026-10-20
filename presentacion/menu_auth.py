"""Capa de presentacion: menu principal de autenticacion (Integrante 1).

Valida TODA la entrada antes de tocar la base de datos (criterio 2.1.4.G.14)
y captura los errores sin que el programa se interrumpa (2.1.4.G.13).
Las reglas de formato viven en presentacion/validaciones.py (reutilizadas
por el resto de los menues).
"""
import getpass

from data_base.errores import ErrorBaseDatos, RegistroDuplicado
from data_base.usuario_dao import UsuarioDAO
from negocio.estudiante import Estudiante
from negocio.instructor import Instructor
from negocio.permisos import (ROL_ESTUDIANTE, ROL_INSTRUCTOR, ROLES_VALIDOS)
from presentacion.menu_estudiante import mostrar_menu_estudiante
from presentacion.menu_instructor import mostrar_menu_instructor
from presentacion.validaciones import (
    LONG_CORREO,
    LONG_DETALLE,
    LONG_NOMBRE,
    no_vacio,
    validar_contrasena,
    validar_correo,
    validar_longitud,
    validar_rut,
)


def pedir_contrasena(mensaje="Contrasena: "):
    """Lee la contrasena SIN mostrarla en pantalla (getpass).

    Si la consola no soporta getpass, Python usa la entrada normal: aun asi
    la validacion posterior se mantiene.
    """
    return getpass.getpass(mensaje)


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
        correo = no_vacio(input("Correo: "), "El correo")
        contrasena = pedir_contrasena()
        if not contrasena:
            print("La contrasena no puede estar vacia.")
            return
        datos = UsuarioDAO().autenticar(correo, contrasena)
    except ValueError as e:
        print(f"Dato no valido: {e}")
        return
    except (EOFError, KeyboardInterrupt):
        print("\nEntrada no disponible. Volviendo al menu principal.")
        return
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
    Se valida ademas el digito verificador del RUT (modulo 11) y que ningun
    texto supere el largo de su columna (evita errores 1406 de MySQL).
    """
    try:
        rut = validar_rut(input("RUT (ej: 12345678-5): "))

        nombre = validar_longitud(
            no_vacio(input("Nombre completo: "), "El nombre completo"),
            LONG_NOMBRE,
            "El nombre completo",
        )

        correo = validar_longitud(
            validar_correo(input("Correo electronico: ")), LONG_CORREO, "El correo"
        )

        contrasena = validar_contrasena(pedir_contrasena())
        confirmacion = pedir_contrasena("Repite la contrasena: ")
        if contrasena != confirmacion:
            raise ValueError("Las contrasenas no coinciden.")

        rol = no_vacio(input("Rol (instructor/estudiante): "), "El rol").lower()
        if rol not in ROLES_VALIDOS:
            raise ValueError(f"Rol invalido. Debe ser {ROL_INSTRUCTOR} o {ROL_ESTUDIANTE}.")

        detalle = input("Carrera (estudiante) o especialidad (instructor): ").strip() or None
        if detalle is not None:
            detalle = validar_longitud(detalle, LONG_DETALLE, "Carrera/especialidad")

        UsuarioDAO().registrar(rut, nombre, correo, contrasena, rol, detalle)
    except ValueError as e:
        print(f"Dato no valido: {e}")
    except RegistroDuplicado as e:
        print(f"No se pudo registrar: {e}")
    except ErrorBaseDatos as e:
        print(f"Error de base de datos: {e}")
    except (EOFError, KeyboardInterrupt):
        print("\nRegistro cancelado. Volviendo al menu principal.")
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
        except (EOFError, KeyboardInterrupt):
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
