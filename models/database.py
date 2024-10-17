import mysql.connector

database = mysql.connector.connect(
    host='mysqlbiservice.mysql.database.azure.com',
    user='userazuremysql',
    password='admin.2024', # encriptar user y psw con mismo metodo de password usuario
    database='demo_biservice'
)

