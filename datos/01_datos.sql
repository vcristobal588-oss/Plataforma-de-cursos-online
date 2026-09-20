CREATE DATABASE plataforma_cursos;
USE plataforma_cursos;

CREATE TABLE usuario (
    rut VARCHAR(12) PRIMARY KEY,
    nombre_completo VARCHAR(45) NOT NULL,
    correo_electronico VARCHAR(60) UNIQUE,
    contrasena VARCHAR(255) NOT NULL,
    rol VARCHAR(10) NOT NULL
) ENGINE=InnoDB;

CREATE TABLE estudiantes (
    rut_estudiante VARCHAR(12),
    carrera VARCHAR(100),
    PRIMARY KEY (rut_estudiante),
    FOREIGN KEY (rut_estudiante) REFERENCES usuario(rut)
) ENGINE=InnoDB;

CREATE TABLE instructor (
    rut_instructor VARCHAR(12),
    especialidad VARCHAR(100),
    PRIMARY KEY (rut_instructor),
    FOREIGN KEY (rut_instructor) REFERENCES usuario(rut)
) ENGINE=InnoDB;