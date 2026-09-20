import mysql.connector
import bcrypt

def iniciar_sesion():
    print("PLATAFORMA DE CURSOS ONLINE: SISTEMA DE LOGIN")
    email_ingresado = input("Ingresa tu correo: ")
    password_ingresada = input("Ingresa tu contraseña: ")

    try:
        conexion = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="plataforma_cursos"
        )

        cursor = conexion.cursor(dictionary=True)

        consulta = "SELECT * FROM usuario WHERE correo_electronico = %s"
        cursor.execute(consulta, (email_ingresado,))
        usuario = cursor.fetchone()

        if usuario:
            if bcrypt.checkpw(password_ingresada.encode(), usuario['contrasena'].encode()):
                print(f"\n¡Bienvenido/a, {usuario['nombre_completo']}!")

                if usuario['rol'] == 'instructor':
                    print("Acceso concedido: Perfil de INSTRUCTOR.")
                elif usuario['rol'] == 'estudiante':
                    print("Acceso concedido: Perfil de ESTUDIANTE.")
            else:
                print("\nError: Contraseña incorrecta.")
        else:
            print("\nError: El correo no está registrado en el sistema.")

        cursor.close()
        conexion.close()

    except mysql.connector.Error as error:
        print(f"Error al conectar con la base de datos: {error}")

if __name__ == "__main__":
    iniciar_sesion()