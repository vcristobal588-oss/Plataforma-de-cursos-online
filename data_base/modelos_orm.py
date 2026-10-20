"""Capa de mapeo objeto-relacional (ORM Peewee) del modelo UML.

ROL EN EL PROYECTO (arquitectura hibrida acordada):
- Consigna de clases: "trabajaremos con Peewee" -> aqui viven los modelos que
  traducen CADA entidad del diagrama UML a su tabla (criterios 2.1.1.I.3 y
  2.1.1.I.4: correspondencia exacta entidad -> clase -> atributos -> tabla).
- Rúbrica 2.1.3.G.9: la persistencia transaccional existente sigue con
  mysql-connector-python (libreria oficial de MySQL para Python) en la capa
  DAO. Este modulo NO la reemplaza: lo usa el módulo de inscripcion
  (data_base/inscripcion_dao.py) y lo demas tablas quedan mapeadas aqui como
  fuente de la correspondencia UML <-> BD.

CONFIGURACION: reutiliza las constantes de data_base.conexion (unica fuente
de verdad de host/puerto/usuario/contrasena; criterio 2.1.3.I.11).

PEWEE APORTA AQUÍ: SQL parametrizado generado, transacciones atomicas
(atomic = commit/rollback automatico) y errores traducidos a las excepciones
propias de la capa de datos (2.1.4.G.13).
"""
from contextlib import contextmanager
from datetime import datetime

import peewee
from peewee import (
    AutoField,
    CharField,
    DateTimeField,
    ForeignKeyField,
    MySQLDatabase,
    Model,
    SmallIntegerField,
    TextField,
)

from data_base.conexion import (
    BASE_DATOS,
    CODIFICACION,
    CONTRASENA_BD,
    HOST,
    PUERTO,
    USUARIO_BD,
)
from data_base.errores import excepcion_para_codigo

# Base Peewee: mismos parametros que usa la capa DAO (sin credenciales repetidas).
database = MySQLDatabase(
    BASE_DATOS,
    host=HOST,
    port=PUERTO,
    user=USUARIO_BD,
    password=CONTRASENA_BD,
    charset=CODIFICACION,
)

# Mismo modo estricto que aplica data_base/conexion.py: MySQL rechaza datos
# invalidos en vez de truncarlos en silencio (el rollback depende de esto).
SQL_MODE_ESTRICTO = "STRICT_TRANS_TABLES,NO_ENGINE_SUBSTITUTION"


def conectar():
    """Abre la sesion ORM y aplica el modo estricto de la base (si es MySQL)."""
    if database.is_closed():
        database.connect()
        if isinstance(database, MySQLDatabase):
            database.execute_sql(f"SET SESSION sql_mode = '{SQL_MODE_ESTRICTO}'")


@contextmanager
def sesion():
    """Abre la sesion ORM y la cierra SIEMPRE (finally implicito).

    Es el equivalente ORM del bloque try/finally de DaoBase._cerrar()
    (criterio 2.1.4.G.13: nunca queda una conexion abierta).
    """
    conectar()
    try:
        yield database
    finally:
        if not database.is_closed():
            database.close()


# ---------------------------------------------------------------------------
# MODELOS: una clase por entidad del diagrama UML / tabla de la base de datos
# ---------------------------------------------------------------------------

class UsuarioModel(Model):
    """ENTIDAD UML `Usuario` -> tabla `usuario` (atributos 1:1 con el diagrama).

    Corresponde a la clase negocio Usuario (negocio/usuario.py): aqui se
    modela su persistencia, no su encapsulamiento (ese vive en la capa de
    negocio con atributos privados y @property).
    """

    rut = CharField(max_length=12, primary_key=True)
    nombre_completo = CharField(max_length=45)
    correo_electronico = CharField(max_length=60, null=True, unique=True)
    contrasena = CharField(max_length=255)  # hash bcrypt, nunca texto plano
    rol = CharField(max_length=10)

    class Meta:
        table_name = "usuario"
        database = database


class EstudianteModel(Model):
    """ENTIDAD UML `Estudiante` (hereda de Usuario) -> tabla `estudiantes`.

    RELACION UML de generalizacion: en la BD se resuelve con clave primaria
    compuesta que ES foranea a usuario (estension 1:1), tal como lo define el
    esquema 01_datos.sql.
    """

    rut_estudiante = ForeignKeyField(
        UsuarioModel, field="rut", column_name="rut_estudiante", primary_key=True
    )
    carrera = CharField(max_length=100, null=True)

    class Meta:
        table_name = "estudiantes"
        database = database


class InstructorModel(Model):
    """ENTIDAD UML `Instructor` (hereda de Usuario) -> tabla `instructor`.

    Misma estrategia de herencia relacional que EstudianteModel.
    """

    rut_instructor = ForeignKeyField(
        UsuarioModel, field="rut", column_name="rut_instructor", primary_key=True
    )
    especialidad = CharField(max_length=100, null=True)

    class Meta:
        table_name = "instructor"
        database = database


class DireccionModel(Model):
    """ENTIDAD UML `Direccion` (asociada a Usuario) -> tabla `direccion`."""

    id_direccion = AutoField()
    rut_usuario = ForeignKeyField(UsuarioModel, field="rut", column_name="rut_usuario")
    comuna = CharField(max_length=50)
    calle = CharField(max_length=100)
    numero = CharField(max_length=10, null=True)
    departamento = CharField(max_length=10, null=True)
    tipo_direccion = CharField(max_length=20, null=True)

    class Meta:
        table_name = "direccion"
        database = database


class CursoModel(Model):
    """ENTIDAD UML `Curso` -> tabla `curso`.

    RELACION UML: Instructor 1 -> N Curso (asociacion `rut_instructor`);
    Curso 1 -> N Modulo (composicion, representada por ModuloModel.id_curso).
    """

    id_curso = AutoField()
    rut_instructor = ForeignKeyField(
        InstructorModel,
        field="rut_instructor",
        column_name="rut_instructor",
        backref="cursos",
    )
    titulo = CharField(max_length=100)
    descripcion = TextField(null=True)
    estado = CharField(max_length=15, default="borrador")  # borrador | publicado

    class Meta:
        table_name = "curso"
        database = database


class ModuloModel(Model):
    """ENTIDAD UML `Modulo` -> tabla `modulo` (composicion Curso -> Modulo)."""

    id_modulo = AutoField()
    id_curso = ForeignKeyField(
        CursoModel, field="id_curso", column_name="id_curso", backref="modulos"
    )
    titulo = CharField(max_length=100)
    orden = SmallIntegerField(default=1)

    class Meta:
        table_name = "modulo"
        database = database


class ActividadModel(Model):
    """ENTIDAD UML `Actividad` -> tabla `actividad` (composicion Modulo -> Actividad)."""

    id_actividad = AutoField()
    id_modulo = ForeignKeyField(
        ModuloModel,
        field="id_modulo",
        column_name="id_modulo",
        backref="actividades",
    )
    titulo = CharField(max_length=100)
    publicada = SmallIntegerField(default=0)  # 0 = borrador, 1 = publicada

    class Meta:
        table_name = "actividad"
        database = database


class InscripcionModel(Model):
    """ENTIDAD UML `Inscripcion` (Estudiante * -> Curso *) -> tabla `inscripcion`.

    Es la ASOCIACION many-to-many Estudiante <-> Curso con sus atributos
    propios (fecha, progreso, estado); la unica tabla nueva de la solucion.
    """

    id_inscripcion = AutoField()
    rut_estudiante = ForeignKeyField(
        EstudianteModel,
        field="rut_estudiante",
        column_name="rut_estudiante",
        backref="inscripciones",
    )
    id_curso = ForeignKeyField(
        CursoModel,
        field="id_curso",
        column_name="id_curso",
        backref="inscripciones",
    )
    fecha_inscripcion = DateTimeField(default=datetime.now)
    progreso = SmallIntegerField(default=0)  # 0 a 100 (% completado)
    estado = CharField(max_length=15, default="activa")  # activa | completada

    class Meta:
        table_name = "inscripcion"
        database = database


#: Todas las entidades del modelo UML mapeadas (se usa en pruebas y docs).
MODELOS = (
    UsuarioModel,
    EstudianteModel,
    InstructorModel,
    DireccionModel,
    CursoModel,
    ModuloModel,
    ActividadModel,
    InscripcionModel,
)


def usar(base):
    """Apunta los modelos a otra base de datos (solo para pruebas en memoria)."""
    global database
    database = base
    base.bind(MODELOS)


# ---------------------------------------------------------------------------
# TRADUCCION DE ERRORES (capa 2.1.4: nunca se filtra un error crudo del driver)
# ---------------------------------------------------------------------------

def _errno_de(error):
    """Extrae el codigo errno de MySQL desde una excepcion de Peewee/PyMySQL.

    Peewee envuelve el error del driver en `error.orig`; se recorre esa cadena
    (y `__cause__`) hasta encontrar un errno entero. Si no existe retorna None.
    """
    actual = error
    for _ in range(5):
        if actual is None:
            return None
        args = getattr(actual, "args", None)
        if isinstance(args, tuple) and args and isinstance(args[0], int):
            return args[0]
        actual = getattr(actual, "orig", None) or getattr(actual, "__cause__", None)
    return None


def traducir_error(error, mensaje_duplicado=None):
    """Convierte cualquier excepcion ORM en ErrorBaseDatos/RegistroDuplicado.

    Usa la misma tabla de mensajes que la capa DAO (`excepcion_para_codigo`
    en data_base/errores.py): el usuario recibe identica informacion sin
    importar la tecnologia de persistencia subyacente.
    """
    if isinstance(error, peewee.PeeweeException) or _errno_de(error) is not None:
        return excepcion_para_codigo(_errno_de(error), mensaje_duplicado)
    # Errores de logica (ValueError de validacion, etc.) no se tocan.
    return error
