"""Capa de datos: conexion centralizada a MySQL.

Unico punto del sistema que sabe como conectarse: host, usuario y
contrasena se declaran una sola vez aqui (evita credenciales
duplicadas en varios archivos).
"""
import mysql.connector

from data_base.errores import ErrorConexion

# --- Configuracion centralizada ---
HOST = "localhost"
PUERTO = 3306
USUARIO_BD = "root"
CONTRASENA_BD = ""
BASE_DATOS = "plataforma_cursos"
CODIFICACION = "utf8mb4"


def obtener_conexion():
    """Crea y retorna una conexion a la base de datos.

    Cualquier error del driver se traduce en ErrorConexion (excepcion
    propia de la capa de datos) para no exponer detalles de MySQL.
    """
    try:
        conexion = mysql.connector.connect(
            host=HOST,
            port=PUERTO,
            user=USUARIO_BD,
            password=CONTRASENA_BD,
            database=BASE_DATOS,
            charset=CODIFICACION,
            connection_timeout=5,
        )
        # Modo estricto SOLO en esta sesion: MySQL debe rechazar datos
        # invalidos (p.ej. exceso de largo) en vez de truncarlos en
        # silencio. Sin esto, el rollback de transacciones no se activa
        # y se pierden datos sin aviso.
        with conexion.cursor() as cursor:
            cursor.execute("SET SESSION sql_mode = 'STRICT_TRANS_TABLES,NO_ENGINE_SUBSTITUTION'")
        return conexion
    except mysql.connector.Error as error:
        raise ErrorConexion(f"No se pudo conectar a la base de datos: {error}") from error
