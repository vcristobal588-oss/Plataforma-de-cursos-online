class Usuario:
    """Clase base. Atributos privados (__prefijo) expuestos SOLO como
    propiedades de solo lectura (@property): no pueden modificarse
    desde fuera del objeto (encapsulamiento estricto)."""

    def __init__(self, id_usuario, nombre_usuario, rol):
        self.__id = id_usuario
        self.__nombre_usuario = nombre_usuario
        self.__rol = rol

    @property
    def id(self):
        """Identificador unico del usuario (RUT). Solo lectura."""
        return self.__id

    @property
    def nombre_usuario(self):
        """Nombre visible del usuario. Solo lectura."""
        return self.__nombre_usuario

    @property
    def rol(self):
        """Rol del usuario ('estudiante' o 'instructor'). Solo lectura."""
        return self.__rol
