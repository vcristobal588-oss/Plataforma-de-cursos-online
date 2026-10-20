"""DAO de direcciones: CRUD con SQL parametrizado (tabla `direccion`)."""
from data_base.dao_base import DaoBase


class DireccionDAO(DaoBase):
    """CRUD de direcciones asociadas a un usuario (FK: rut_usuario).

    `listar_todos` y `eliminar` se heredan del CRUD generico de DaoBase.
    """

    tabla = "direccion"
    clave = "id_direccion"

    def agregar(self, rut_usuario, comuna, calle, numero=None,
                departamento=None, tipo_direccion=None):
        """Crea una direccion y retorna su id autogenerado (0 si fallo)."""
        return self.ejecutar_con_id(
            "INSERT INTO direccion (rut_usuario, comuna, calle, numero, departamento, tipo_direccion) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (rut_usuario, comuna, calle, numero, departamento, tipo_direccion),
        )

    def listar_por_usuario(self, rut_usuario):
        """Retorna las direcciones de un usuario."""
        return self.consultar(
            "SELECT id_direccion, comuna, calle, numero, departamento, tipo_direccion "
            "FROM direccion WHERE rut_usuario = %s ORDER BY id_direccion",
            (rut_usuario,),
        )

    def actualizar(self, id_direccion, comuna, calle, numero=None,
                   departamento=None, tipo_direccion=None):
        """Actualiza una direccion. Retorna True si existia."""
        return self.ejecutar([
            ("UPDATE direccion SET comuna = %s, calle = %s, numero = %s, departamento = %s, "
             "tipo_direccion = %s WHERE id_direccion = %s",
             (comuna, calle, numero, departamento, tipo_direccion, id_direccion)),
        ]) > 0
