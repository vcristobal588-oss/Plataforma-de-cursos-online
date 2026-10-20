"""Clase Inscripcion (capa de negocio - modulo de estudiante).

Modela la ASOCIACION Estudiante * <-> Curso * del diagrama UML: un estudiante
puede inscribirse a varios cursos y un curso acepta varios estudiantes; el
objeto Inscripcion lleva los atributos de ese enlace (fecha, progreso,
estado).

Reglas de negocio (validadas en el constructor y en los metodos):
- progreso: entero de 0 a 100 (porcentaje completado del curso).
- estado: 'activa' o 'completada' (transicion controlada al llegar a 100).
- el progreso solo cambia a traves de actualizar_progreso()/completar():
  encapsulamiento con transicion de estado controlada, igual que Curso.
"""


class Inscripcion:
    """Inscripcion de un estudiante a un curso. Atributos privados y solo lectura."""

    ESTADOS_VALIDOS = ("activa", "completada")

    def __init__(self, rut_estudiante, id_curso, id_inscripcion=None,
                 fecha_inscripcion=None, progreso=0, estado="activa"):
        if not rut_estudiante or not str(rut_estudiante).strip():
            raise ValueError("La inscripcion requiere el RUT del estudiante.")
        if not isinstance(id_curso, int) or isinstance(id_curso, bool) or id_curso < 1:
            raise ValueError("El id del curso debe ser un entero mayor a 0.")
        if estado not in Inscripcion.ESTADOS_VALIDOS:
            raise ValueError(f"Estado de inscripcion invalido: '{estado}'.")
        self.__id = id_inscripcion
        self.__rut_estudiante = str(rut_estudiante).strip()
        self.__id_curso = id_curso
        self.__fecha = fecha_inscripcion
        self.__progreso = self._validar_progreso(progreso)
        self.__estado = estado

    @staticmethod
    def _validar_progreso(valor):
        """Valida y normaliza el porcentaje de progreso (0 a 100)."""
        if not isinstance(valor, int) or isinstance(valor, bool):
            raise ValueError("El progreso debe ser un numero entero (0 a 100).")
        if not 0 <= valor <= 100:
            raise ValueError("El progreso debe estar entre 0 y 100.")
        return valor

    @property
    def id(self):
        """Identificador de la inscripcion (None si aun no se persistio)."""
        return self.__id

    @property
    def rut_estudiante(self):
        """RUT del estudiante inscrito. Solo lectura."""
        return self.__rut_estudiante

    @property
    def id_curso(self):
        """Identificador del curso al que se inscribio. Solo lectura."""
        return self.__id_curso

    @property
    def fecha_inscripcion(self):
        """Fecha/hora del alta (asignada por la base de datos). Solo lectura."""
        return self.__fecha

    @property
    def progreso(self):
        """Porcentaje completado (0 a 100). Solo lectura."""
        return self.__progreso

    @property
    def estado(self):
        """'activa' o 'completada'. Solo lectura."""
        return self.__estado

    @property
    def esta_completada(self):
        return self.__estado == "completada"

    def actualizar_progreso(self, valor):
        """Actualiza el progreso validado. Retorna True si cambio.

        Al alcanzar 100 la inscripcion pasa automaticamente a 'completada'
        (transicion de estado unidireccional, igual que Curso.publicar()).
        """
        nuevo = self._validar_progreso(valor)
        if nuevo == self.__progreso:
            return False
        self.__progreso = nuevo
        if nuevo == 100:
            self.__estado = "completada"
        return True

    def completar(self):
        """Marca la inscripcion como completada (100%). True si cambio."""
        return self.actualizar_progreso(100)

    def __repr__(self):
        return (f"Inscripcion(id={self.__id}, rut={self.__rut_estudiante!r}, "
                f"curso={self.__id_curso}, progreso={self.__progreso}, "
                f"estado={self.__estado!r})")
