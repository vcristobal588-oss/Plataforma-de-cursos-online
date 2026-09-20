CREATE DATABASE curso_1;
USE curso_1;

CREATE TABLE curso_1 (
    id_curso INTEGER AUTO_INCREMENT,
    nombre_curso VARCHAR(25) NOT NULL,
    descripcion_curso VARCHAR(60) NOT NULL,
    habilitado TINYINT NOT NULL DEFAULT 1,
    CONSTRAINT pk_curso_1 PRIMARY KEY(id_curso)
);

CREATE TABLE direccion(
    id_direccion INTEGER AUTO_INCREMENT,
    comuna INTEGER NOT NULL,
    calle VARCHAR(10) NOT NULL,
    numero VARCHAR(5) NULL,
    departamento VARCHAR(5) NULL,
    tipo_direccion INTEGER  NULL,
);