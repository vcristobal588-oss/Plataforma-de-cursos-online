"""Clase Actividad (capa de negocio - Integrante 2).

Unidad minima de contenido de un Modulo. Solo el instructor puede
publicarla (publicada 0 -> 1) mediante el metodo publicar().
"""


class Actividad:
    """Actividad de un modulo. Atributos privados y solo lectura (@property)."""

    def __init__(self, titulo, id_modulo=None, id_actividad=None, publicada=False):
        if not titulo or not str(titulo).strip():
            raise ValueError("El titulo de la actividad no puede estar vacio.")
        self.__id = id_actividad
        self.__id_modulo = id_modulo
        self.__titulo = str(titulo).strip()
        self.__publicada = bool(publicada)

    @property
    def id(self):
        return self.__id

    @property
    def id_modulo(self):
        """Identificador del modulo al que pertenece."""
        return self.__id_modulo

    @property
    def titulo(self):
        return self.__titulo

    @property
    def publicada(self):
        """True si la actividad ya fue publicada. Solo lectura."""
        return self.__publicada

    def publicar(self):
        """Transicion de estado controlada: borrador -> publicada.

        Retorna True si cambio, False si ya estaba publicada.
        """
        if self.__publicada:
            return False
        self.__publicada = True
        return True

    def __repr__(self):
        return (f"Actividad(id={self.__id}, titulo={self.__titulo!r}, "
                f"publicada={self.__publicada})")
