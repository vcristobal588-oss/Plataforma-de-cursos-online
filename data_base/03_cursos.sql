-- Tablas de cursos (Integrante 2). Requiere 01_datos.sql (usuario, instructor).
-- La FK apunta a `instructor` (no a `usuario`): la base de datos misma
-- garantiza que solo un instructor real pueda tener cursos (defensa en profundidad).

CREATE TABLE IF NOT EXISTS curso (
    id_curso INT AUTO_INCREMENT PRIMARY KEY,
    rut_instructor VARCHAR(12) NOT NULL,
    titulo VARCHAR(100) NOT NULL,
    descripcion TEXT NULL,
    estado VARCHAR(15) NOT NULL DEFAULT 'borrador'
        CHECK (estado IN ('borrador', 'publicado')),
    CONSTRAINT fk_curso_instructor
        FOREIGN KEY (rut_instructor) REFERENCES instructor(rut_instructor)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS modulo (
    id_modulo INT AUTO_INCREMENT PRIMARY KEY,
    id_curso INT NOT NULL,
    titulo VARCHAR(100) NOT NULL,
    orden INT NOT NULL DEFAULT 1,
    CONSTRAINT fk_modulo_curso
        FOREIGN KEY (id_curso) REFERENCES curso(id_curso)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS actividad (
    id_actividad INT AUTO_INCREMENT PRIMARY KEY,
    id_modulo INT NOT NULL,
    titulo VARCHAR(100) NOT NULL,
    publicada TINYINT(1) NOT NULL DEFAULT 0
        CHECK (publicada IN (0, 1)),
    CONSTRAINT fk_actividad_modulo
        FOREIGN KEY (id_modulo) REFERENCES modulo(id_modulo)
) ENGINE=InnoDB;
