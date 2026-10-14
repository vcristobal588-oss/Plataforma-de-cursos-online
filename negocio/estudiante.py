from negocio.usuario import Usuario
 
 
class Estudiante(Usuario):
    def __init__(self, id_usuario, nombre_usuario):
        super().__init__(id_usuario, nombre_usuario, "estudiante")
 