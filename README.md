# Plataforma-de-cursos-online

Proyecto de desarrollo con Programación Orientada a Objetos (POO) — Evaluación N°3 (continuidad del proyecto de la Evaluación N°2).

## Integrantes

- Cristóbal Saíd Vásquez San Martín[cite: 10]
- Erick Bustamante[cite: 10]

## Descripción general

Aplicación multicapa para la gestión de una plataforma de cursos en línea (cursos, módulos, actividades, estudiantes, instructores, inscripciones, progreso y usuarios), construida como continuación de la Evaluación N°2 e integrando persistencia con ORM Peewee, organización por capas, autenticación y módulos de apoyo[cite: 5, 10, 11, 12, 13].

## Estructura del proyecto

```text
Plataforma-de-cursos-online/
├── datos/
│   ├── conexion.py
│   ├── modelos/
│   ├── repositorio/
│   └── sql/
│       ├── 01_datos.sql
│       ├── 02_direccion.sql
│       ├── 03_cursos.sql
│       └── 04_inscripciones.sql
├── negocio/
├── presentacion/
├── auxiliares/
├── main.py
├── requirements.txt
└── README.mdProyecto de desarrollo con POO
