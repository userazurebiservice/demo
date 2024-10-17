import mysql.connector

database1 = mysql.connector.connect(
    host='mysqlbiservice.mysql.database.azure.com',
    user='userazuremysql',
    password='admin.2024', # encriptar user y psw con mismo metodo de password usuario
    database='demo_biservice'
)
