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