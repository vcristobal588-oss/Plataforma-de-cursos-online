"""Clase Progreso (capa de negocio - Integrante 3).

Modela el avance de un estudiante en una actividad y su calificacion.
"""


class Progreso:
    """Progreso y nota de una actividad dentro de una inscripcion."""

    def __init__(self, id_inscripcion, id_actividad, completada=True, nota=None, id_progreso=None):
        if not id_inscripcion or not id_actividad:
            raise ValueError("Los IDs de inscripcion y actividad son obligatorios.")
            
        if nota is not None:
            nota = float(nota)
            if nota < 1.0 or nota > 7.0:
                raise ValueError("La nota debe estar en el rango chileno entre 1.0 y 7.0.")

        self.__id = id_progreso
        self.__id_inscripcion = int(id_inscripcion)
        self.__id_actividad = int(id_actividad)
        self.__completada = bool(completada)
        self.__nota = nota

    @property
    def id(self):
        return self.__id

    @property
    def id_inscripcion(self):
        return self.__id_inscripcion

    @property
    def id_actividad(self):
        return self.__id_actividad

    @property
    def completada(self):
        return self.__completada

    @property
    def nota(self):
        return self.__nota

    def __repr__(self):
        return (f"Progreso(id={self.__id}, inscripcion={self.__id_inscripcion}, "
                f"actividad={self.__id_actividad}, completada={self.__completada}, nota={self.__nota})")