"""Clase Modulo (capa de negocio - Integrante 2).

Un Modulo pertenece a un Curso y esta compuesto por Actividades
(composicion: Modulo 1 -> N Actividades).
"""
from negocio.actividad import Actividad


class Modulo:
    """Modulo de un curso. Atributos privados y solo lectura (@property)."""

    def __init__(self, titulo, id_curso=None, id_modulo=None, orden=1):
        if not titulo or not str(titulo).strip():
            raise ValueError("El titulo del modulo no puede estar vacio.")
        if orden < 1:
            raise ValueError("El orden del modulo debe ser un entero mayor o igual a 1.")
        self.__id = id_modulo
        self.__id_curso = id_curso
        self.__titulo = str(titulo).strip()
        self.__orden = orden
        self.__actividades = []

    @property
    def id(self):
        return self.__id

    @property
    def id_curso(self):
        """Identificador del curso al que pertenece."""
        return self.__id_curso

    @property
    def titulo(self):
        return self.__titulo

    @property
    def orden(self):
        return self.__orden

    @property
    def actividades(self):
        """Tupla inmutable de actividades del modulo."""
        return tuple(self.__actividades)

    def agregar_actividad(self, actividad):
        """Compone una Actividad dentro del Modulo."""
        if not isinstance(actividad, Actividad):
            raise TypeError("Solo se pueden agregar objetos Actividad a un Modulo.")
        self.__actividades.append(actividad)

    def __repr__(self):
        return f"Modulo(id={self.__id}, titulo={self.__titulo!r}, orden={self.__orden})"
