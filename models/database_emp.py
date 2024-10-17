
import mysql.connector

database_emp = mysql.connector.connect(
    host='mysqlbiservice.mysql.database.azure.com',
    user='userazuremysql',
    password='admin.2024', # encriptar user y psw con mismo metodo de password usuario
    database='acceso_bireport'
)





