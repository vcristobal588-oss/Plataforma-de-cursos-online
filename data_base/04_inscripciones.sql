-- Tablas para el Integrante 3: Inscripciones y Control de Avance
-- Requiere que existan las tablas estudiantes (01_datos.sql) y curso/actividad (03_cursos.sql)

CREATE TABLE IF NOT EXISTS inscripcion (
    id_inscripcion INT AUTO_INCREMENT PRIMARY KEY,
    rut_estudiante VARCHAR(12) NOT NULL,
    id_curso INT NOT NULL,
    fecha_inscripcion DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_inscripcion_estudiante
        FOREIGN KEY (rut_estudiante) REFERENCES estudiantes(rut_estudiante),
    CONSTRAINT fk_inscripcion_curso
        FOREIGN KEY (id_curso) REFERENCES curso(id_curso),
    CONSTRAINT uq_estudiante_curso
        UNIQUE (rut_estudiante, id_curso) -- Evita que un alumno se inscriba 2 veces al mismo curso
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS progreso_actividad (
    id_progreso INT AUTO_INCREMENT PRIMARY KEY,
    id_inscripcion INT NOT NULL,
    id_actividad INT NOT NULL,
    completada TINYINT(1) NOT NULL DEFAULT 1 CHECK (completada IN (0, 1)),
    nota DECIMAL(3,1) NULL CHECK (nota >= 1.0 AND nota <= 7.0),
    CONSTRAINT fk_progreso_inscripcion
        FOREIGN KEY (id_inscripcion) REFERENCES inscripcion(id_inscripcion) ON DELETE CASCADE,
    CONSTRAINT fk_progreso_actividad
        FOREIGN KEY (id_actividad) REFERENCES actividad(id_actividad),
    CONSTRAINT uq_inscripcion_actividad
        UNIQUE (id_inscripcion, id_actividad) -- Una sola entrada por actividad e inscripcion
) ENGINE=InnoDB;