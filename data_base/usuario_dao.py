"""DAO de usuarios: CRUD completo con SQL parametrizado (criterio 2.1.3)."""
import bcrypt

from data_base.dao_base import DaoBase
# La fuente unica de verdad de los roles vive en la capa de negocio.
from negocio.permisos import ROL_ESTUDIANTE, ROL_INSTRUCTOR, ROLES_VALIDOS


class UsuarioDAO(DaoBase):
    """Operaciones CRUD sobre la tabla `usuario` y sus tablas de rol."""

    tabla = "usuario"
    clave = "rut"

    def buscar_por_id(self, rut):
        """Version segura del CRUD genérico: NUNCA retorna la contraseña.

        Sobreescribe DaoBase.buscar_por_id (que haría SELECT *) por el
        principio de mínimo privilegio: el hash bcrypt no debe salir de la
        capa de datos.
        """
        return self._fila(
            "SELECT rut, nombre_completo, correo_electronico, rol "
            "FROM usuario WHERE rut = %s",
            (rut,),
        )

    def autenticar(self, correo, contrasena):
        """Valida las credenciales con bcrypt.

        Retorna un dict {id, nombre_usuario, rol} si coinciden, o None
        si el correo no existe o la contrasena es incorrecta.
        """
        if not correo or not contrasena:
            return None
        filas = self.consultar(
            "SELECT rut, nombre_completo, contrasena, rol "
            "FROM usuario WHERE correo_electronico = %s",
            (correo,),
        )
        if not filas:
            return None
        fila = filas[0]
        try:
            coincide = bcrypt.checkpw(contrasena.encode(), fila["contrasena"].encode())
        except ValueError:
            return None  # hash invalido en la BD: credenciales no validas
        if not coincide:
            return None
        return {
            "id": fila["rut"],
            "nombre_usuario": fila["nombre_completo"],
            "rol": fila["rol"],
        }

    def registrar(self, rut, nombre, correo, contrasena, rol, detalle=None):
        """Crea el usuario y su fila de rol en UNA transaccion atomica.

        detalle = carrera (estudiante) o especialidad (instructor).
        Si el segundo INSERT falla, el primero se revierte (rollback).
        """
        if rol not in ROLES_VALIDOS:
            raise ValueError(f"Rol no valido: '{rol}'. Debe ser {', '.join(ROLES_VALIDOS)}.")
        hash_contrasena = bcrypt.hashpw(contrasena.encode(), bcrypt.gensalt()).decode()
        operaciones = [
            (
                "INSERT INTO usuario (rut, nombre_completo, correo_electronico, contrasena, rol) "
                "VALUES (%s, %s, %s, %s, %s)",
                (rut, nombre, correo, hash_contrasena, rol),
            ),
        ]
        if rol == ROL_ESTUDIANTE:
            operaciones.append(
                ("INSERT INTO estudiantes (rut_estudiante, carrera) VALUES (%s, %s)",
                 (rut, detalle))
            )
        else:
            operaciones.append(
                ("INSERT INTO instructor (rut_instructor, especialidad) VALUES (%s, %s)",
                 (rut, detalle))
            )
        return self.ejecutar(operaciones) > 0

    def listar_todos(self):
        """Lista todos los usuarios. Nunca retorna contrasenas (minimo privilegio)."""
        return self.consultar(
            "SELECT rut, nombre_completo, correo_electronico, rol "
            "FROM usuario ORDER BY nombre_completo"
        )

    def buscar_por_rut(self, rut):
        """Retorna los datos (sin contrasena) de un usuario por su RUT."""
        return self.consultar(
            "SELECT rut, nombre_completo, correo_electronico, rol "
            "FROM usuario WHERE rut = %s",
            (rut,),
        )

    def actualizar(self, rut, nombre, correo):
        """Actualiza nombre y correo. Retorna True si existia el usuario."""
        return self.ejecutar([
            ("UPDATE usuario SET nombre_completo = %s, correo_electronico = %s WHERE rut = %s",
             (nombre, correo, rut)),
        ]) > 0

    def eliminar(self, rut):
        """Elimina el usuario y sus registros dependientes en una transaccion.

        Borra primero direcciones y fila de rol (claves foraneas) y
        recien despues el usuario. Retorna False si no existia.
        """
        return self.ejecutar([
            ("DELETE FROM direccion WHERE rut_usuario = %s", (rut,)),
            ("DELETE FROM estudiantes WHERE rut_estudiante = %s", (rut,)),
            ("DELETE FROM instructor WHERE rut_instructor = %s", (rut,)),
            ("DELETE FROM usuario WHERE rut = %s", (rut,)),
        ]) > 0
