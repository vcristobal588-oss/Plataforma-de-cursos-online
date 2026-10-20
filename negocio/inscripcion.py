"""Clase Inscripcion (capa de negocio - Integrante 3).

Modela la relacion entre un Estudiante y un Curso.
Atributos privados (__prefijo) y solo lectura (@property).
"""


class Inscripcion:
    """Inscripcion de un estudiante a un curso."""

    def __init__(self, rut_estudiante, id_curso, id_inscripcion=None, fecha_inscripcion=None):
        if not rut_estudiante or not str(rut_estudiante).strip():
            raise ValueError("El RUT del estudiante no puede estar vacio.")
        if not id_curso:
            raise ValueError("El id del curso es obligatorio.")
            
        self.__id = id_inscripcion
        self.__rut_estudiante = str(rut_estudiante).strip()
        self.__id_curso = int(id_curso)
        self.__fecha_inscripcion = fecha_inscripcion

    @property
    def id(self):
        """Identificador unico de la inscripcion."""
        return self.__id

    @property
    def rut_estudiante(self):
        """RUT del estudiante inscrito."""
        return self.__rut_estudiante

    @property
    def id_curso(self):
        """Identificador del curso."""
        return self.__id_curso

    @property
    def fecha_inscripcion(self):
        """Fecha y hora de registro."""
        return self.__fecha_inscripcion

    def __repr__(self):
        return f"Inscripcion(id={self.__id}, estudiante={self.__rut_estudiante!r}, curso={self.__id_curso})"