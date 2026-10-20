"""[EVIDENCIA - CODIGO DESCARTADO] Modelo generado con Peewee (pwiz).

Procedencia: archivo `models.py` que estuvo en la raíz del proyecto (28-sep),
generado con la herramienta `pwiz` de Peewee sobre la base `plataforma_cursos`.

¿POR QUÉ SE DESCARTÓ? (criterios 2.1.5.G.18 y 2.1.5.I.20)
1. Seguridad: traía credenciales de la base de datos en claro (usuario y
   contraseña reales de otra máquina). Aquí fueron REDACTADAS; la única fuente
   de verdad de la configuración es data_base/conexion.py.
2. Cobertura incompleta: mapeaba sólo 3 de las 8 tablas del proyecto
   (usuario, estudiantes, instructor); faltaban direccion, curso, modulo,
   actividad e inscripcion.
3. Codificación UTF-16: Python no podía compilarlo
   (SyntaxError: source code string cannot contain null bytes).
4. Arquitectura: el proyecto resuelve la persistencia con el patrón DAO y SQL
   parametrizado sobre mysql-connector-python (librería oficial de MySQL para
   Python), que es lo que exigen los criterios 2.1.3 (conexión y CRUD) y
   2.1.4 (excepciones) de la rúbrica.

REEMPLAZO VIGENTE EN EL PROYECTO:
- data_base/modelos_orm.py  -> modelos Peewee limpios (capa de mapeo
  objeto-relacional del modelo UML, usada por el módulo de inscripción).
- data_base/dao_base.py     -> CRUD transaccional con la librería oficial.
"""
from peewee import *

# [REDACTADO POR SEGURIDAD] el archivo original contenía usuario y contraseña
# en claro. Ver data_base/conexion.py para la configuración vigente.
database = MySQLDatabase(
    'plataforma_cursos',
    **{'charset': 'utf8mb4', 'host': 'localhost', 'port': 3306,
       'user': '***REDACTADO***', 'password': '***REDACTADO***'}
)


class UnknownField(object):
    def __init__(self, *_, **__):
        pass


class BaseModel(Model):
    class Meta:
        database = database


class Usuario(BaseModel):
    contrasena = CharField()
    correo_electronico = CharField(max_length=60, null=True, unique=True)
    nombre_completo = CharField(max_length=45)
    rol = CharField(max_length=10)
    rut = CharField(max_length=12, primary_key=True)

    class Meta:
        table_name = 'usuario'


class Estudiantes(BaseModel):
    carrera = CharField(max_length=100, null=True)
    rut_estudiante = ForeignKeyField(column_name='rut_estudiante', field='rut',
                                     model=Usuario, primary_key=True)

    class Meta:
        table_name = 'estudiantes'


class Instructor(BaseModel):
    especialidad = CharField(max_length=100, null=True)
    rut_instructor = ForeignKeyField(column_name='rut_instructor', field='rut',
                                     model=Usuario, primary_key=True)

    class Meta:
        table_name = 'instructor'
