"""Clase Curso (capa de negocio - Integrante 2).

Modela un curso creado por un instructor. Compuesto por Modulos
(composicion: Curso 1 -> N Modulos). Atributos privados expuestos
solo como @property; el estado solo cambia via publicar().
"""
from negocio.modulo import Modulo


class Curso:
    """Curso de la plataforma.

    Atributos privados (__prefijo) y solo lectura (@property).
    No hay setter de estado: el unico camino es el metodo publicar()
    (encapsulamiento con transicion de estado controlada).
    """

    ESTADOS_VALIDOS = ("borrador", "publicado")

    def __init__(self, titulo, descripcion="", rut_instructor=None,
                 id_curso=None, estado="borrador"):
        if not titulo or not str(titulo).strip():
            raise ValueError("El titulo del curso no puede estar vacio.")
        if estado not in Curso.ESTADOS_VALIDOS:
            raise ValueError(f"Estado invalido: '{estado}'.")
        self.__id = id_curso
        self.__titulo = str(titulo).strip()
        self.__descripcion = (descripcion or "").strip()
        self.__rut_instructor = rut_instructor
        self.__estado = estado
        self.__modulos = []

    @property
    def id(self):
        """Identificador del curso (None si aun no se persistio)."""
        return self.__id

    @property
    def titulo(self):
        return self.__titulo

    @property
    def descripcion(self):
        return self.__descripcion

    @property
    def rut_instructor(self):
        """RUT del instructor propietario del curso."""
        return self.__rut_instructor

    @property
    def estado(self):
        """'borrador' o 'publicado'. Solo lectura."""
        return self.__estado

    @property
    def esta_publicado(self):
        return self.__estado == "publicado"

    @property
    def modulos(self):
        """Tupla inmutable de modulos (no se puede alterar desde fuera)."""
        return tuple(self.__modulos)

    def agregar_modulo(self, modulo):
        """Compone un Modulo dentro del Curso."""
        if not isinstance(modulo, Modulo):
            raise TypeError("Solo se pueden agregar objetos Modulo a un Curso.")
        self.__modulos.append(modulo)

    def publicar(self):
        """Transicion de estado controlada: borrador -> publicado.

        Retorna True si cambio el estado, False si ya estaba publicado.
        """
        if self.__estado == "publicado":
            return False
        self.__estado = "publicado"
        return True

    def __repr__(self):
        return f"Curso(id={self.__id}, titulo={self.__titulo!r}, estado={self.__estado!r})"
