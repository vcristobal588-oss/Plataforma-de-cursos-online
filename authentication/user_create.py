"""Script historico de alta de usuario (version anterior al patron DAO).

SE CONSERVA COMO EVIDENCIA, no es el flujo activo del sistema.

Problemas que motivaron su descarte como implementacion vigente:
- Credenciales de la BD y datos de prueba en claro dentro del codigo.
- Alta sin transaccion y sin cierre en finally: un fallo a mitad de la
  ejecucion dejaba la conexion abierta y sin rollback.
- Registraba un solo INSERT: hoy el alta es atomica en usuario + fila de
  rol (estudiantes/instructor) con rollback automatico.

Flujo activo: presentacion/menu_auth.py -> UsuarioDAO.registrar()
"""
import mysql.connector
import bcrypt

rut = "12345678-9"
nombre_completo = "Said Pérez"
correo_electronico = "said@plataforma.cl"
password = "said2024"
rol = "estudiante"

hash_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

conexion = mysql.connector.connect(
    host="localhost", user="root", password="", database="plataforma_cursos"
)
cursor = conexion.cursor()
cursor.execute(
    "INSERT INTO usuario (rut, nombre_completo, correo_electronico, contrasena, rol) VALUES (%s, %s, %s, %s, %s)",
    (rut, nombre_completo, correo_electronico, hash_password, rol)
)
conexion.commit()
cursor.close()
conexion.close()

print("Usuario creado.")