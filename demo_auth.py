"""Evidencia Integrante 1: CRUD de usuarios y direcciones contra la BD real.

Cubre los criterios:
  2.1.3 -> consultas SQL parametrizadas (%s) en todos los DAO.
  2.1.4 -> try/except/finally con rollback y validacion de entradas.
  2.1.2 -> reutilizacion (DaoBase) y encapsulamiento (@property).

Uso: python demo_auth.py
"""
from data_base.direccion_dao import DireccionDAO
from data_base.errores import ErrorBaseDatos, RegistroDuplicado
from data_base.usuario_dao import UsuarioDAO
from presentacion.menu_auth import crear_usuario, registrar

INSTRUCTOR = {
    "rut": "22333444-5",
    "nombre": "Ana Instructora",
    "correo": "ana.instructora@plataforma.cl",
    "clave": "clave1234",
    "rol": "instructor",
    "detalle": "Robótica",
}
ESTUDIANTE = {
    "rut": "33444555-6",
    "nombre": "Luis Estudiante",
    "correo": "luis.estudiante@plataforma.cl",
    "clave": "clave1234",
    "rol": "estudiante",
    "detalle": "Ing. Informática",
}


def resultado(titulo, ok, detalle=""):
    marca = "OK  " if ok else "FALLA"
    print(f"[{marca}] {titulo}" + (f" -> {detalle}" if detalle else ""))
    return ok


def main():
    dao = UsuarioDAO()
    dir_dao = DireccionDAO()
    fallos = 0

    print("=== 1) REGISTRO TRANSACCIONAL (usuario + fila de rol) ===")
    ok = dao.registrar(INSTRUCTOR["rut"], INSTRUCTOR["nombre"], INSTRUCTOR["correo"],
                       INSTRUCTOR["clave"], INSTRUCTOR["rol"], INSTRUCTOR["detalle"])
    fallos += not resultado("Registrar instructor en dos tablas con UN commit", ok)
    ok = dao.registrar(ESTUDIANTE["rut"], ESTUDIANTE["nombre"], ESTUDIANTE["correo"],
                       ESTUDIANTE["clave"], ESTUDIANTE["rol"], ESTUDIANTE["detalle"])
    fallos += not resultado("Registrar estudiante", ok)

    print("\n=== 2) ERRORES CONTROLADOS (sin caida del sistema) ===")
    try:
        dao.registrar(INSTRUCTOR["rut"], "Duplicado", "otro@correo.cl", "clave1234", "instructor")
        fallos += not resultado("RUT duplicado detectado", False, "no lanzo excepcion")
    except RegistroDuplicado as e:
        fallos += not resultado("RUT duplicado detectado", True, str(e))
    try:
        dao.registrar("11222333-4", "Sin Rol", "sinrol@correo.cl", "clave1234", "superadmin")
        fallos += not resultado("Rol invalido rechazado con ValueError", False)
    except ValueError as e:
        fallos += not resultado("Rol invalido rechazado con ValueError", True, str(e))

    print("\n=== 3) ROLLBACK: si falla el 2.º INSERT, se revierte el 1.º ===")
    rut_rollback = "99888777-6"
    try:
        # carrera VARCHAR(100): 150 caracteres hace fallar el 2.º INSERT en modo estricto
        dao.registrar(rut_rollback, "Rollback Demo", "rollback@correo.cl",
                      "clave1234", "estudiante", "x" * 150)
        fallos += not resultado("Segundo INSERT falla por largo de columna", False, "no fallo")
    except ErrorBaseDatos as e:
        quedo = dao.buscar_por_rut(rut_rollback)
        fallos += not resultado("ROLLBACK del INSERT de usuario (fila ausente)", quedo == [], str(e))

    print("\n=== 4) AUTENTICACION CON BCRYPT ===")
    datos = dao.autenticar(INSTRUCTOR["correo"], INSTRUCTOR["clave"])
    esperado = {"id": INSTRUCTOR["rut"], "nombre_usuario": INSTRUCTOR["nombre"], "rol": "instructor"}
    fallos += not resultado("Login correcto", datos == esperado, str(datos))
    fallos += not resultado("Contrasena incorrecta -> None", dao.autenticar(INSTRUCTOR["correo"], "mala") is None)
    fallos += not resultado("Correo inexistente -> None", dao.autenticar("nada@nada.cl", "clave1234") is None)

    print("\n=== 5) OBJETO DE DOMINIO A PARTIR DE LA BD ===")
    usuario = crear_usuario(datos)
    fallos += not resultado("crear_usuario fabrica un Instructor", usuario is not None and usuario.rol == "instructor")
    fallos += not resultado("Encapsulamiento: rol solo lectura (@property)",
                            not hasattr(usuario, "rol") or getattr(type(usuario), "rol", None) is not None)
    try:
        usuario.rol = "admin"
        fallos += not resultado("Asignar usuario.rol debe fallar (solo lectura)", False, "permitio escribir")
    except AttributeError:
        fallos += not resultado("Asignar usuario.rol falla (solo lectura)", True)

    print("\n=== 6) LISTAR Y ACTUALIZAR ===")
    usuarios = dao.listar_todos()
    sin_secretos = all("contrasena" not in u for u in usuarios)
    fallos += not resultado("listar_todos no expone contrasenas", sin_secretos, f"{len(usuarios)} usuarios")
    fallos += not resultado("actualizar datos", dao.actualizar(ESTUDIANTE["rut"], "Luis Est. Actualizado",
                                                               "luis.actualizado@plataforma.cl"))

    print("\n=== 7) CRUD DE DIRECCIONES (Integrante 1) ===")
    id_dir = dir_dao.agregar(INSTRUCTOR["rut"], "Santiago", "Av. Providencia", "1234", "801", "casa")
    fallos += not resultado("direccion.agregar devuelve id", isinstance(id_dir, int) and id_dir > 0, str(id_dir))
    filas = dir_dao.listar_por_usuario(INSTRUCTOR["rut"])
    fallos += not resultado("direccion.listar_por_usuario", len(filas) == 1)
    fallos += not resultado("direccion.actualizar",
                            dir_dao.actualizar(id_dir, "Ñuñoa", "Calle Nueva", "99", "12", "depto"))
    try:
        dir_dao.agregar("00000000-0", "Valparaiso", "Calle Sin Usuario")
        fallos += not resultado("FK con usuario inexistente rechazada", False, "no fallo")
    except ErrorBaseDatos as e:
        fallos += not resultado("FK con usuario inexistente rechazada", True, str(e))
    fallos += not resultado("direccion.eliminar", dir_dao.eliminar(id_dir))

    print("\n=== 8) BORRADO EN CASCADA (rol + usuario en UNA transaccion) ===")
    fallos += not resultado("eliminar instructor (usuario + rol + direcciones)",
                            dao.eliminar(INSTRUCTOR["rut"]))
    fallos += not resultado("fila de instructor eliminada",
                            dao.consultar("SELECT rut_instructor FROM instructor WHERE rut_instructor = %s",
                                          (INSTRUCTOR["rut"],)) == [])
    fallos += not resultado("eliminar estudiante", dao.eliminar(ESTUDIANTE["rut"]))
    fallos += not resultado("fila de estudiante eliminada",
                            dao.consultar("SELECT rut_estudiante FROM estudiantes WHERE rut_estudiante = %s",
                                          (ESTUDIANTE["rut"],)) == [])

    print(f"\n{'=' * 50}\nRESULTADO: {fallos} fallas de las pruebas ejecutadas.")
    return fallos


if __name__ == "__main__":
    raise SystemExit(main())
