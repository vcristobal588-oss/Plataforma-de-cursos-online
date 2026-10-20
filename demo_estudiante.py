"""Evidencia Integrante 3: Inscripciones, avance y notas del estudiante.

Uso: python demo_estudiante.py
"""
from data_base.actividad_dao import ActividadDAO
from data_base.curso_dao import CursoDAO
from data_base.errores import ErrorBaseDatos
from data_base.inscripcion_dao import InscripcionDAO
from data_base.modulo_dao import ModuloDAO
from data_base.usuario_dao import UsuarioDAO
from negocio.inscripcion import Inscripcion
from negocio.progreso import Progreso

# RUTs nuevos para evitar el choque con la prueba anterior
RUT_EST = "99888777-6"
RUT_INS = "88777666-5"


def resultado(titulo, ok, detalle=""):
    marca = "OK  " if ok else "FALLA"
    print(f"[{marca}] {titulo}" + (f" -> {detalle}" if detalle else ""))
    return 0 if ok else 1


def main():
    fallos = 0
    u_dao = UsuarioDAO()
    c_dao = CursoDAO()
    m_dao = ModuloDAO()
    a_dao = ActividadDAO()
    i_dao = InscripcionDAO()

    print("== Integrante 3 - Demostracion de Inscripciones y Progreso ==")
    
    # 1. Crear usuarios de prueba con correos nuevos
    try:
        u_dao.registrar(RUT_INS, "Profesor Demo 2", "profe2@demo.cl", "clave1234", "instructor", "Informatica")
        u_dao.registrar(RUT_EST, "Alumno Demo 2", "alumno2@demo.cl", "clave1234", "estudiante", "Ingenieria")
    except:
        pass # Si ya existen, simplemente lo ignoramos y continuamos

    # 2. Crear un curso con 2 actividades publicadas
    id_curso = c_dao.crear(RUT_INS, "Curso Pruebas Integrante 3", "Descripcion")
    c_dao.publicar(id_curso)
    id_mod = m_dao.crear(id_curso, "Modulo 1")
    id_act1 = a_dao.crear(id_mod, "Actividad 1")
    id_act2 = a_dao.crear(id_mod, "Actividad 2")
    a_dao.publicar(id_act1)
    a_dao.publicar(id_act2)

    print("\n1) PRUEBAS DE DOMINIO (Validaciones POO)")
    try:
        Progreso(id_inscripcion=1, id_actividad=1, nota=8.5) # Nota invalida
        fallos += resultado("Nota invalida (> 7.0) rechazada", False)
    except ValueError as e:
        fallos += resultado("Nota invalida (> 7.0) rechazada con ValueError", True, str(e))

    print("\n2) INSCRIPCION Y CONTROL DE DUPLICADOS")
    id_ins = i_dao.inscribir(RUT_EST, id_curso)
    fallos += resultado("Inscripcion creada exitosamente", bool(id_ins))
    fallos += resultado("esta_inscrito detecta la inscripcion", i_dao.esta_inscrito(RUT_EST, id_curso))

    print("\n3) REGISTRO DE AVANCE Y NOTAS")
    fallos += resultado("Avance inicial es 0%", i_dao.calcular_porcentaje_avance(id_ins) == 0.0)
    
    # Completar 1 de 2 actividades -> 50%
    i_dao.registrar_actividad_completada(id_ins, id_act1, nota=6.5)
    fallos += resultado("Completar 1 de 2 actividades da 50% de avance", i_dao.calcular_porcentaje_avance(id_ins) == 50.0)

    # Completar 2 de 2 actividades -> 100%
    i_dao.registrar_actividad_completada(id_ins, id_act2, nota=7.0)
    fallos += resultado("Completar 2 de 2 actividades da 100% de avance", i_dao.calcular_porcentaje_avance(id_ins) == 100.0)

    print("\n4) LIMPIEZA DE DATOS")
    # Borramos las notas y la inscripcion ANTES de borrar el curso para evitar bloqueos
    i_dao.ejecutar("DELETE FROM progreso_actividad WHERE id_inscripcion = %s", (id_ins,))
    i_dao.ejecutar("DELETE FROM inscripcion WHERE id_inscripcion = %s", (id_ins,))
    
    c_dao.eliminar(id_curso)
    u_dao.eliminar(RUT_EST)
    u_dao.eliminar(RUT_INS)
    fallos += resultado("Limpieza completa sin chocar con llaves foraneas", True)

    print(f"\n{'='*50}\nRESULTADO: {'TODOS LOS TESTS PASARON' if fallos == 0 else f'{fallos} FALLAS'}")


if __name__ == "__main__":
    main()