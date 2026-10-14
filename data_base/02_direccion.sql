-- Tabla direccion (Integrante 1): requiere que exista la tabla usuario de 01_datos.sql
CREATE TABLE IF NOT EXISTS direccion (
    id_direccion INT AUTO_INCREMENT PRIMARY KEY,
    rut_usuario VARCHAR(12) NOT NULL,
    comuna VARCHAR(50) NOT NULL,
    calle VARCHAR(100) NOT NULL,
    numero VARCHAR(10) NULL,
    departamento VARCHAR(10) NULL,
    tipo_direccion VARCHAR(20) NULL,
    CONSTRAINT fk_direccion_usuario
        FOREIGN KEY (rut_usuario) REFERENCES usuario(rut)
) ENGINE=InnoDB;
