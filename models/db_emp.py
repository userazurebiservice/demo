
import mysql.connector

def obtener_conexion():
    """ Obtiene una conexión a la base de datos.
    Returns:  mysql.connector.connection: Una conexión a la base de datos.
    """
    try:
        conexion = mysql.connector.connect(
            host='mysqlbiservice.mysql.database.azure.com',
            user='userazuremysql',
            password='admin.2024',  # ¡Recuerda encriptar la contraseña!
            database='acceso_bireport'
        )
        return conexion
    except mysql.connector.Error as error:
        print(f"Error al conectar a la base de datos: {error}")
        return None

def cerrar_conexion(conexion):
    """ Cierra una conexión a la base de datos.
    Args:    conexion (mysql.connector.connection): La conexión a cerrar.
    """
    if conexion:
        conexion.close()



