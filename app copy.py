# Copyright (c) BI service 09.08.2024.

import webbrowser
from threading import Timer
from flask import make_response 

from services.pbiembedservice import PbiEmbedService
#from services.aadservice import AadService
from models.utils import Utils
#from flask import Flask, render_template, request, jsonify, send_from_directory
from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, url_for, flash, session
from flask_mysqldb import MySQL
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager, login_user, logout_user, login_required
from config import config
import json
import os
import mysql.connector
from models.database import database
from models.database1 import database1
from models.database_emp import database_emp
from models.database_emp import obtener_conexion, cerrar_conexion

#import platform
#import subprocess
import datetime  
from werkzeug.security import check_password_hash, generate_password_hash
# Models:
from models.ModelUser import ModelUser
# Entities:
from models.entities.User import User

template_dir = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
template_dir = os.path.join(template_dir, 'Py_PBIE', 'templates')

# Initialize the Flask app
#app = Flask(__name__, template_folder = 'templates')
app = Flask(__name__)

app.config['TEMPLATES_AUTO_RELOAD'] = True

#app.template_folder = 'Py_PBI/templates'

################## 12-08-2024 ########################################################
#12-08-2024 configuracion login con mysql
csrf = CSRFProtect()
#print("CSRF protection is enabled")

db = MySQL(app)
login_manager_app = LoginManager(app)

@login_manager_app.user_loader
def load_user(id):
    return ModelUser.get_by_id(db, id)

@app.route('/') # ruta inicial
def login1():
    return redirect(url_for('login'))


##################


def valida_empresa(rut_empresa):
    cur_emp = database_emp.cursor()
    cur_emp.execute("SELECT fecha_expiracion FROM acceso_empresa WHERE rut_empresa = %s", (rut_empresa,))
    resultado  = cur_emp.fetchone()
    cur_emp.close()

    if resultado:         # Si se encontró un resultado, extraemos la fecha
        fecha_expiracion = resultado[0]
        return fecha_expiracion
    else:
        return None


def valida_rut(rut_empresa):
    cur_emp = database_emp.cursor()
    cur_emp.execute("SELECT rut_empresa FROM acceso_empresa WHERE rut_empresa = %s", (rut_empresa,))
    rut  = cur_emp.fetchone()
    cur_emp.close()

    if rut:     
        rut_empresa = rut[0]
        return rut_empresa
    else:
        return None


##################

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # print(request.form['username'])
        # print(request.form['password'])

        print(request.form['rut_empresa'])
        rut_empresa = valida_rut(request.form['rut_empresa']) 

        if rut_empresa is None or rut_empresa =='':
            flash("Debe ingresar Rut Empresa permitido")
            return render_template('auth/login.html')
        else:

            fecha_clie_expira =valida_empresa(request.form['rut_empresa']) 
            fecha_hoy=datetime.date.today()
            if fecha_clie_expira is None or fecha_clie_expira < fecha_hoy:
                flash("Acceso caducado. Contacte a BIservice")
                return render_template('auth/login.html')
            else:
                user = User(0, request.form['username'], request.form['password'])
                ######### 14-08-2024 obtener variables globales a partir de la entrada login
                username = request.form['username']
                session['username'] = username
                ##########
                logged_user = ModelUser.login(db, user)
                if logged_user != None:
                    if logged_user.password:
                    #print(logged_user.fecha_expira.date())
                    #print(datetime.datetime.now())
                        if logged_user.fecha_expira is None or logged_user.fecha_expira >= datetime.datetime.now():
                            login_user(logged_user)
                            ### Registra LOG ###
                            id_accion = 'ta01' #ingreso APP
                            id_reporte =''
                            inserta_LOG(id_accion, id_reporte,'')
                            return redirect(url_for('index'))
                        else:
                            flash("Usuario expirado, comuniquese con contacto@biservice.cl")
                            return render_template('auth/login.html')
                    else:
                        flash("Invalid password...")
                        return render_template('auth/login.html')
                else:
                    flash("User not found...")
                    return render_template('auth/login.html')

    else:
        return render_template('auth/login.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/protected')
@login_required
def protected():
    return "<h1>Esta es una vista protegida, solo para usuarios autenticados.</h1>"

def status_401(error):
    return redirect(url_for('login')) # redirecciona a pagina login

def status_404(error):
    return "<h1>Página no encontrada</h1>", 404

#######################################################################
# Load configuration
app.config.from_object('config.BaseConfig')


@app.route('/index')
def index():
    #Returns a static HTML page
    # Filtra mantenedores según tipo de usuario solo se visualizara para Perfil= p1:Administradores
    id_usuario =session.get('username')
    cur = database.cursor()
    cur.execute("SELECT id_perfil FROM usuarios WHERE id_usuario = %s", (id_usuario,))
    usuario = cur.fetchone()
    cur.close()
 
    tipo_perfil = usuario[0] if usuario else None
    #print('tipo perfil: ',tipo_perfil )
    mostrar_listado = False
    if tipo_perfil == 'p1':  # Administrador (Puedes ajustar el valor según tu lógica)
        mostrar_listado = True
 
    ## 11-09-2024 Deshabilitar la caché del navegador para recursos específicos
    #response = make_response(render_template('index.html'))
    response = make_response(render_template('index.html',mostrar_listado=mostrar_listado))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'    
    response.headers['Pragma'] = 'no-cache'    
    response.headers['Expires'] = '0'
    
    #return render_template('index.html',mostrar_listado=mostrar_listado)
    return response    



@app.route('/getembedinfo', methods=['GET'])
def get_embed_info():
    '''Returns report embed configuration'''
    config_result = Utils.check_config(app)
    if config_result is not None:
        return json.dumps({'errorMsg': config_result}), 500

    try:
        embed_info = PbiEmbedService().get_embed_params_for_single_report(app.config['WORKSPACE_ID'], app.config['REPORT_ID'])
        
        return embed_info
    except Exception as ex:
        return json.dumps({'errorMsg': str(ex)}), 500

@app.route('/getEmbedParams', methods=['POST'])
def get_embed_params():
    '''Returns embed parameters for multiple reports'''
    data = request.get_json()
    workspace_id = data.get('workspace_id')
    report_ids = data.get('report_ids')
    additional_dataset_ids = data.get('additional_dataset_ids', None)

    if not workspace_id or not report_ids:
        return jsonify({'errorMsg': 'workspace_id and report_ids are required'}), 400

    try:
        embed_info = PbiEmbedService().get_embed_params_for_multiple_reports(workspace_id, report_ids, additional_dataset_ids)
        return embed_info
    except Exception as ex:
        return jsonify({'errorMsg': str(ex)}), 500

@app.route('/favicon.ico', methods=['GET'])
def getfavicon():
    '''Returns path of the favicon to be rendered'''
    return send_from_directory(os.path.join(app.root_path, 'static'), 'img/favicon.ico', mimetype='image/vnd.microsoft.icon')
    


@app.route('/reports', methods=['GET', 'POST'])
def get_reports():
    '''Retorna la lista de reportes en el Workspace'''
    try:

       user_name =session.get('username')
       cursor = database.cursor()
       
       sql = """
            SELECT distinct r.report_id, r.reporte 
            FROM grupo_reporte gr 
            LEFT JOIN grupo_usuario gu on gr.id_grupo = gu.id_grupo 
            LEFT JOIN grupos g on gr.id_grupo= g.id_grupo 
            LEFT JOIN workspace w on gr.id_workspace = w.id_workspace 
            LEFT JOIN reportes r on gr.id_reporte = r.id_reporte 
            LEFT JOIN usuarios u on gu.id_usuario = u.id_usuario 
            WHERE r.reporte <> "" AND u.id_usuario=%s;
        """
       
       #sql = "SELECT distinct r.report_id, r.reporte FROM bd_appweb.reportes r"
       data = (user_name,)
       cursor.execute(sql, data)
       #cursor.execute(sql)
       myresult = cursor.fetchall()
       reports_info = [{'reportId': record[0], 'reportName': record[1]} for record in myresult]
       cursor.close()

       return jsonify(reports_info)
    except Exception as ex:
        return jsonify({'errorMsg': str(ex)}), 500


@app.route('/viewreport/<report_id>', methods=['GET'])
def view_report(report_id):
    '''Returns embed parameters for the selected report'''
    
    try:
        embed_info = PbiEmbedService().get_embed_params_for_single_report(app.config['WORKSPACE_ID'], report_id)
        ### Registra LOG ###
       
        id_accion = 'ta02' #ingreso APP
        id_reporte = report_id
        inserta_LOG(id_accion, id_reporte, '')

        return jsonify(json.loads(embed_info))
          
    except Exception as ex:

        return jsonify({'errorMsg': str(ex)}), 500

#################################################################################
###### 15-08-2024 enlace a mantenedores ########

########## MANTENEDOR GRUPO #######################################

#Rutas de la aplicación
@app.route('/hgrupo')
def hgrupo():
    cursor = database.cursor()
    cursor.execute("SELECT id, id_grupo, grupo, estado FROM grupos")
    myresult = cursor.fetchall()
    #Convertir los datos a diccionario
    insertObject = []
    columnNames = [column[0] for column in cursor.description]
    for record in myresult:
        insertObject.append(dict(zip(columnNames, record)))
    cursor.close()
    #print(insertObject)
        
    ### Registra LOG ###
    id_accion = 'mgi' #ingreso APP
    id_reporte = 'grupo'
    detalle = 'ingreso a grupo'
    inserta_LOG(id_accion, id_reporte, detalle)

    return render_template('Grupo.html', data=insertObject)

#Ruta para guardar grupos en la bdd
@app.route('/addGrupo', methods=['POST'])
@csrf.exempt
def addGrupo():
    #print("POST request received at /addGroup")
    #print("Form data:", request.form)
    #print(request.form.get('csrf_token'))
    id_grupo = request.form['id_grupo']
    grupo = request.form['grupo']
    estado = request.form['estado']
    #print("Received data - ID Grupo:", id_grupo, "Grupo:", grupo, "Estado:", estado)


    if id_grupo and grupo and estado:
        cursor = database.cursor()
        sql = "INSERT INTO grupos (id_grupo, grupo, estado) VALUES (%s, %s, %s)"
        data = (id_grupo, grupo, estado)
        cursor.execute(sql, data)
        database.commit()
    
    ### Registra LOG ###
    id_accion = 'mga' #ingreso APP
    id_reporte = 'Grupo: ' + id_grupo
    detalle = 'Agrego Grupo ' + id_grupo + ' ' + grupo + ' ' + estado
    inserta_LOG(id_accion, id_reporte, detalle)

    return redirect(url_for('hgrupo'))

@app.route('/deleteGrupo/<string:id>',methods=['POST'])
@csrf.exempt
def deleteGrupo(id):
    #### Obtengo datos a eliminar ###
    cursor = database.cursor()
    cursor.execute("SELECT grupo FROM grupos WHERE id = %s",(id,))
    reg = cursor.fetchone()
    result= reg[0]
    cursor.close()

    ###################################
    
    cursor = database.cursor()
    sql = "DELETE FROM grupos WHERE id=%s"
    data = (id,)
    cursor.execute(sql, data)
    database.commit()

    ### Registra LOG ###
    id_accion = 'mgb' #ingreso APP
    id_reporte = 'Grupo' 
    detalle = 'Elimino Grupo: ' + id  + ' ' + result
    inserta_LOG(id_accion, id_reporte, detalle)

    return redirect(url_for('hgrupo'))

@app.route('/editGrupo/<string:id>', methods=['POST'])
@csrf.exempt
def editGrupo(id):
    #print(f"POST request received at /editGrupo/{id}")
    #print("Form data:", request.form)
    #print(request.form.get('csrf_token'))
    id_grupo = request.form['id_grupo']
    grupo = request.form['grupo']
    estado = request.form['estado']
    #print(f"Updating group {id} - New ID Grupo: {id_grupo}, Grupo: {grupo}, Estado: {estado}")

    if id_grupo and grupo and estado:
        cursor = database.cursor()
        sql = "UPDATE grupos SET id_grupo = %s, grupo = %s, estado = %s WHERE id = %s"
        data = (id_grupo, grupo, estado, id)
        cursor.execute(sql, data)
        database.commit()

    ### Registra LOG ###
    id_accion = 'mge' #ingreso APP
    id_reporte = 'Grupo' 
    detalle = 'Edito Grupo: ' + id_grupo + ' ' + grupo
    inserta_LOG(id_accion, id_reporte, detalle)

    return redirect(url_for('hgrupo'))


#################### MANTENEDOR Usuario #######################################

#Rutas de la aplicación

#### MUESTRA USUARIO  #############
@app.route('/hUsuario')
def hUsuario():
    cursor = database.cursor()
    cursor.execute("SELECT id, id_usuario, usuario, password, rut, telefono, email, estado, fecha_creacion  FROM usuarios")
    myresult = cursor.fetchall()
    #Convertir los datos a diccionario
    insertObject = []
    columnNames = [column[0] for column in cursor.description]
    for record in myresult:
        formatted_record = {
            'id': record[0],
            'id_usuario': record[1],
            'usuario': record[2],
            # Password should not be displayed
            'password': record[3], 
            'rut': record[4],  # Assuming 'rut' is the column index
            'telefono': record[5],  # Assuming 'telefono' is the column index
            'email': record[6],
            'estado': record[7],
            'fecha_creacion': record[8],
        }

        insertObject.append(formatted_record)
        #insertObject.append(dict(zip(columnNames, formatted_record)))
    cursor.close()
    ### Registra LOG ###
    id_accion = 'mui' #ingreso APP
    id_reporte = 'Usuario' 
    detalle = 'ingreso a modulo Usuario '
    inserta_LOG(id_accion, id_reporte, detalle)

    return render_template('Usuario.html', data=insertObject)

#### AGREGA USUARIO #############

#Ruta para guardar usuarios en la bdd
@app.route('/addUser', methods=['POST'])
@csrf.exempt
def addUser():
    id_usuario = request.form['id_usuario']
    usuario = request.form['usuario']
    #password = request.form['password']
    password = generate_password_hash(request.form['password'])
    rut = request.form['rut']
    telefono = request.form['telefono']
    email = request.form['email']
    estado = request.form['estado']
    #fecha_creacion = request.form['fecha_creacion']
    fecha_creacion = datetime.datetime.now()
    fecha_expira = datetime.datetime.now() + datetime.timedelta(days=30)
   
    if id_usuario and usuario and password:
        cursor = database.cursor()
        sql = "INSERT INTO usuarios (id_usuario, usuario, password, rut, telefono,email, estado, fecha_creacion, fecha_expira ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s,%s)"
        data = (id_usuario, usuario, password, rut, telefono, email, estado, fecha_creacion, fecha_expira )
        cursor.execute(sql, data)
        database.commit()
    
    ### Registra LOG ###
    id_accion = 'mua' #ingreso APP
    id_reporte = 'Usuario' 
    detalle = 'Agrega Usuario: ' + id_usuario + ' ' + usuario
    inserta_LOG(id_accion, id_reporte, detalle)

    return redirect(url_for('hUsuario'))

#### ELIMINA USUARIO #############
@app.route('/deleteUser/<string:id>',methods=['POST'])
@csrf.exempt
def deleteUser(id):
    #### Obtengo datos a eliminar ###
    cursor = database.cursor()
    cursor.execute("SELECT usuario FROM usuarios WHERE id = %s",(id,))
    reg = cursor.fetchone()
    result= reg[0]
    cursor.close()

    ###############
    cursor = database.cursor()
    sql = "DELETE FROM usuarios WHERE id=%s"
    data = (id,)
    cursor.execute(sql, data)
    database.commit()
    
    ### Registra LOG ###
    id_accion = 'mub' #ingreso APP
    id_reporte = 'Usuario' 
    detalle = 'Borra Usuario: ' + id + ' ' + result
    inserta_LOG(id_accion, id_reporte, detalle)    
    return redirect(url_for('hUsuario'))

#### EDITA USUARIO #############
@app.route('/editUser/<string:id>', methods=['POST'])
@csrf.exempt
def editUser(id):
    #### Obtengo PSW ID A EDITAR ###
    cursor = database.cursor()
    cursor.execute("SELECT Password FROM usuarios WHERE id = %s",(id,))
    reg = cursor.fetchone()
    pasw_ant= reg[0]
    cursor.close()
    ###############
    
    id_usuario = request.form['id_usuario']
    usuario = request.form['usuario']
    #password = request.form['password']
    if pasw_ant  !=  request.form['password'] and request.form['password'] !='******':
        password = generate_password_hash(request.form['password'])
    else:
        password = pasw_ant
        
    #print (password)
    rut = request.form['rut']
    telefono = request.form['telefono']
    email = request.form['email']
    estado = request.form['estado']
    #fecha_creacion = datetime.datetime.now() # request.form['fecha_creacion']

    if id_usuario and usuario and password:
        cursor = database.cursor()
        sql = "UPDATE usuarios SET id_usuario = %s, usuario = %s, password = %s, rut = %s, telefono = %s, email = %s, estado = %s WHERE id = %s"
        data = (id_usuario, usuario, password, rut, telefono, email, estado,  id )
        cursor.execute(sql, data)
        database.commit()

        ### Registra LOG ###
        id_accion = 'mue' #ingreso APP
        id_reporte = 'Usuario' 
        detalle = 'Edita Usuario: ' + id_usuario + ' ' +  usuario
        inserta_LOG(id_accion, id_reporte, detalle)    
        return redirect(url_for('hUsuario'))        


################# MANTENEDOR REPORTE #######################################

#Rutas de la aplicación
@app.route('/hReporte')
def hReporte():
    cursor = database.cursor()
    cursor.execute("SELECT id, id_reporte, id_workspace, report_id, reporte, reporte_pbix, estado FROM reportes")
    myresult = cursor.fetchall()
    #Convertir los datos a diccionario
    insertObject = []
    columnNames = [column[0] for column in cursor.description]
    for record in myresult:
        insertObject.append(dict(zip(columnNames, record)))
    cursor.close()
    ### Registra LOG ###
    id_accion = 'mri' #ingreso APP
    id_reporte = 'Reporte' 
    detalle = 'ingreso a modulo Reporte'
    inserta_LOG(id_accion, id_reporte, detalle)
    return render_template('Reporte.html', data=insertObject)

#Ruta para guardar usuarios en la bdd
@app.route('/addReporte', methods=['POST'])
@csrf.exempt
def addReporte():
    id_reporte = request.form['id_reporte']
    id_workspace = request.form['id_workspace']
    report_id = request.form['report_id']
    reporte = request.form['reporte']
    reporte_pbix = request.form['reporte_pbix']
    estado = request.form['estado']
   
    if id_reporte and id_workspace and report_id and reporte and reporte_pbix and estado:
        cursor = database.cursor()
        sql = "INSERT INTO reportes (id_reporte, id_workspace, report_id, reporte, reporte_pbix, estado ) VALUES (%s, %s, %s, %s, %s, %s)"
        data = (id_reporte, id_workspace, report_id, reporte, reporte_pbix, estado)
        cursor.execute(sql, data)
        database.commit()
        ### Registra LOG ###
        id_accion = 'mra' #ingreso APP
        id_reporte = 'Reportes' 
        detalle = 'Agrega reporte: ' + id_reporte + ' ' + reporte
        inserta_LOG(id_accion, id_reporte, detalle)    

    return redirect(url_for('hReporte'))

@app.route('/deleteReporte/<string:id>',methods=['POST'])
@csrf.exempt
def deleteReporte(id):
    #### Obtengo datos a eliminar ###
    cursor = database.cursor()
    cursor.execute("SELECT reporte FROM reportes WHERE id = %s",(id,))
    reg = cursor.fetchone()
    result= reg[0]
    cursor.close()
    ###################################    
    cursor = database.cursor()
    sql = "DELETE FROM reportes WHERE id=%s"
    data = (id,)
    cursor.execute(sql, data)
    database.commit()
    ### Registra LOG ###
    id_accion = 'mrb' #ingreso APP
    id_reporte = 'Reportes' 
    detalle = 'Borra reporte: ' + id + ' ' + result
    inserta_LOG(id_accion, id_reporte, detalle)    

    return redirect(url_for('hReporte'))

@app.route('/editReporte/<string:id>', methods=['POST'])
@csrf.exempt
def editReporte(id):
    id_reporte = request.form['id_reporte']
    id_workspace = request.form['id_workspace']
    report_id = request.form['report_id']
    reporte = request.form['reporte']
    reporte_pbix = request.form['reporte_pbix']
    estado = request.form['estado']

    if id_reporte and id_workspace and report_id and reporte and reporte_pbix and estado:
        cursor = database.cursor()
        sql = "UPDATE reportes SET id_reporte = %s, id_workspace = %s, report_id = %s, reporte = %s, reporte_pbix = %s, estado = %s WHERE id = %s"
        data = (id_reporte, id_workspace, report_id, reporte, reporte_pbix, estado, id)
        cursor.execute(sql, data)
        database.commit()
        ### Registra LOG ###
        id_accion = 'mre' #ingreso APP
        id_reporte = 'Reportes' 
        detalle = 'Edita reporte: ' + id + ' ' + reporte
        inserta_LOG(id_accion, id_reporte, detalle)    

    return redirect(url_for('hReporte'))


########## MANTENEDOR Grupo usuario #######################################

#Rutas de la aplicación
@app.route('/hGrupoUsuario')
def hGrupoUsuario():
    cursor = database.cursor()
    cursor.execute("SELECT id, id_grupo, id_usuario FROM grupo_usuario")
    myresult = cursor.fetchall()
    #Convertir los datos a diccionario
    insertObject = []
    columnNames = [column[0] for column in cursor.description]
    for record in myresult:
        insertObject.append(dict(zip(columnNames, record)))
    cursor.close()
    ### Registra LOG ###
    id_accion = 'mgui' #ingreso APP
    id_reporte = 'Grupo Usuario' 
    detalle = 'ingreso a modulo Grupo Usuario '
    inserta_LOG(id_accion, id_reporte, detalle)
    return render_template('GrupoUsuario.html', data=insertObject)

#Ruta para guardar grupos en la bdd
@app.route('/addGrupoUsuario', methods=['POST'])
@csrf.exempt
def addGrupoUsuario():
    id_grupo = request.form['id_grupo']
    id_usuario = request.form['id_usuario']
       
    if id_grupo and id_usuario:
        cursor = database.cursor()
        sql = "INSERT INTO grupo_usuario (id_grupo, id_usuario) VALUES (%s, %s)"
        data = (id_grupo, id_usuario)
        cursor.execute(sql, data)
        database.commit()
        ### Registra LOG ###
        id_accion = 'mgua' #ingreso APP
        id_reporte = 'Grupo Usuario' 
        detalle = 'Agrega Grupo Usuario: ' + id_grupo + ' ' + id_usuario
        inserta_LOG(id_accion, id_reporte, detalle)    

    return redirect(url_for('hGrupoUsuario'))

@app.route('/deleteGrupoUsuario/<string:id>',methods=['POST'])
@csrf.exempt
def deleteGrupoUsuario(id):
    #### Obtengo datos a eliminar ###
    cursor = database.cursor()
    cursor.execute("SELECT concat(id_grupo , ' ', id_usuario) res FROM grupo_usuario WHERE id = %s",(id,))
    reg = cursor.fetchone()
    result= reg[0]
    cursor.close()
    ###################################        
    cursor = database.cursor()
    sql = "DELETE FROM grupo_usuario WHERE id=%s"
    data = (id,)
    cursor.execute(sql, data)
    database.commit()
    ### Registra LOG ###
    id_accion = 'mgub' #ingreso APP
    id_reporte = 'Grupo Usuario' 
    detalle = 'Borra Grupo Usuario: ' + id + ' ' + result
    inserta_LOG(id_accion, id_reporte, detalle)    

    return redirect(url_for('hGrupoUsuario'))

@app.route('/editGrupoUsuario/<string:id>', methods=['POST'])
@csrf.exempt
def editGrupoUsuario(id):
    id_grupo = request.form['id_grupo']
    id_usuario = request.form['id_usuario']

    if id_grupo and id_usuario:
        cursor = database.cursor()
        sql = "UPDATE grupo_usuario SET id_grupo = %s, id_usuario = %s WHERE id = %s"
        data = (id_grupo, id_usuario, id)
        cursor.execute(sql, data)
        database.commit()
        ### Registra LOG ###
        id_accion = 'mgue' #ingreso APP
        id_reporte = 'Grupo Usuario' 
        detalle = 'Edita Grupo Usuario: ' + id_grupo + ' ' + id_usuario
        inserta_LOG(id_accion, id_reporte, detalle)            
    return redirect(url_for('hGrupoUsuario'))

########## MANTENEDOR Grupo reporte  #######################################

#Rutas de la aplicación
@app.route('/hGrupoReporte')
def hGrupoReporte():
    cursor = database.cursor()
    cursor.execute("SELECT id, id_grupo, id_reporte, id_workspace FROM grupo_reporte")
    myresult = cursor.fetchall()
    #Convertir los datos a diccionario
    insertObject = []
    columnNames = [column[0] for column in cursor.description]
    for record in myresult:
        insertObject.append(dict(zip(columnNames, record)))
    cursor.close()
    ### Registra LOG ###
    id_accion = 'mgri' #ingreso APP
    id_reporte = 'Grupo Reporte' 
    detalle = 'ingreso a modulo Grupo Reporte '
    inserta_LOG(id_accion, id_reporte, detalle)
    
    return render_template('GrupoReporte.html', data=insertObject)

#Ruta para guardar grupos en la bdd
@app.route('/addGrupoReporte', methods=['POST'])
@csrf.exempt
def addGrupoReporte():
    id_grupo = request.form['id_grupo']
    id_reporte = request.form['id_reporte']
    id_workspace = request.form['id_workspace']
       
    if id_grupo and id_reporte and id_workspace:
        cursor = database.cursor()
        sql = "INSERT INTO grupo_reporte (id_grupo, id_reporte, id_workspace) VALUES (%s, %s, %s)"
        data = (id_grupo, id_reporte, id_workspace)
        cursor.execute(sql, data)
        database.commit()
        ### Registra LOG ###
        id_accion = 'mgua' #ingreso APP
        id_reporte = 'Grupo Reporte' 
        detalle = 'Agrega Grupo Reporte: ' + id_grupo + ' ' + id_reporte + ' ' + id_workspace
        inserta_LOG(id_accion, id_reporte, detalle)    

    return redirect(url_for('hGrupoReporte'))

@app.route('/deleteGrupoReporte/<string:id>',methods=['POST'])
@csrf.exempt
def deleteGrupoReporte(id):
    #### Obtengo datos a eliminar ###
    cursor = database.cursor()
    cursor.execute("SELECT concat(id_grupo , ' ', id_reporte, ' ', id_workspace) res FROM grupo_reporte WHERE id = %s",(id,))
    reg = cursor.fetchone()
    result= reg[0]
    cursor.close()
    ###################################          
    cursor = database.cursor()
    sql = "DELETE FROM grupo_reporte WHERE id=%s"
    data = (id,)
    cursor.execute(sql, data)
    database.commit()
    ### Registra LOG ###
    id_accion = 'mgub' #ingreso APP
    id_reporte = 'Grupo Reporte' 
    detalle = 'Borra Grupo Reporte: ' + id + ' ' + result
    inserta_LOG(id_accion, id_reporte, detalle)    
    return redirect(url_for('hGrupoReporte'))

@app.route('/editGrupoReporte/<string:id>', methods=['POST'])
@csrf.exempt
def editGrupoReporte(id):
    id_grupo = request.form['id_grupo']
    id_reporte = request.form['id_reporte']
    id_workspace = request.form['id_workspace']
  
    if id_grupo and id_reporte and id_workspace:
        cursor = database.cursor()
        sql = "UPDATE grupo_reporte SET id_grupo = %s, id_reporte = %s, id_workspace = %s WHERE id = %s"
        data = (id_grupo, id_reporte, id_workspace, id)
        cursor.execute(sql, data)
        database.commit()
        ### Registra LOG ###
        id_accion = 'mgre' #ingreso APP
        id_reporte = 'Grupo Reporte' 
        detalle = 'Edita Grupo Reporte: ' + id_grupo + ' ' + id_reporte + ' ' + id_workspace
        inserta_LOG(id_accion, id_reporte, detalle)             
    return redirect(url_for('hGrupoReporte'))


########## MANTENEDOR Perfiles #######################################

#Rutas de la aplicación
@app.route('/hPerfil')
def hPerfil():
    cursor = database.cursor()
    cursor.execute("SELECT id, id_perfil, perfil FROM perfiles")
    myresult = cursor.fetchall()
    #Convertir los datos a diccionario
    insertObject = []
    columnNames = [column[0] for column in cursor.description]
    for record in myresult:
        insertObject.append(dict(zip(columnNames, record)))
    cursor.close()
    ### Registra LOG ###
    id_accion = 'mpi' #ingreso APP
    id_reporte = 'Perfil' 
    detalle = 'ingreso a modulo Perfil '
    inserta_LOG(id_accion, id_reporte, detalle)
    return render_template('Perfil.html', data=insertObject)

#Ruta para guardar grupos en la bdd
@app.route('/addPerfil', methods=['POST'])
@csrf.exempt
def addPerfil():
    id_perfil = request.form['id_perfil']
    perfil = request.form['perfil']
       
    if id_perfil and perfil:
        cursor = database.cursor()
        sql = "INSERT INTO perfiles (id_perfil, perfil) VALUES (%s, %s)"
        data = (id_perfil, perfil)
        cursor.execute(sql, data)
        database.commit()
        ### Registra LOG ###
        id_accion = 'mpa' #ingreso APP
        id_reporte = 'perfil' 
        detalle = 'Agrega perfil: ' + id_perfil + ' ' + perfil 
        inserta_LOG(id_accion, id_reporte, detalle)            
    return redirect(url_for('hPerfil'))

@app.route('/deletePerfil/<string:id>',methods=['POST'])
@csrf.exempt
def deletePerfil(id):
    #### Obtengo datos a eliminar ###
    cursor = database.cursor()
    cursor.execute("SELECT concat(id_perfil , ' ', perfil) res FROM perfiles WHERE id = %s",(id,))
    reg = cursor.fetchone()
    result= reg[0]
    cursor.close()
    ###################################         
    cursor = database.cursor()
    sql = "DELETE FROM perfiles WHERE id=%s"
    data = (id,)
    cursor.execute(sql, data)
    database.commit()
    ### Registra LOG ###
    id_accion = 'mpb' #ingreso APP
    id_reporte = 'Perfiles' 
    detalle = 'Borra Perfil: ' + id + ' ' + result
    inserta_LOG(id_accion, id_reporte, detalle)    
    return redirect(url_for('hPerfil'))

@app.route('/editPerfil/<string:id>', methods=['POST'])
@csrf.exempt
def editPerfil(id):
    id_perfil = request.form['id_perfil']
    perfil = request.form['perfil']

    if id_perfil and perfil:
        cursor = database.cursor()
        sql = "UPDATE perfiles SET id_perfil = %s, perfil = %s WHERE id = %s"
        data = (id_perfil, perfil, id)
        cursor.execute(sql, data)
        database.commit()
        ### Registra LOG ###
        id_accion = 'mpe' #ingreso APP
        id_reporte = 'perfil' 
        detalle = 'Edita perfil: ' + id_perfil + ' ' + perfil 
        inserta_LOG(id_accion, id_reporte, detalle)                    
    return redirect(url_for('hPerfil'))

########## MANTENEDOR Workspace #######################################

#Rutas de la aplicación
@app.route('/hWorkspace')
def hWorkspace():
    cursor = database.cursor()
    cursor.execute("SELECT id, id_workspace, workspace_id, workspace, estado FROM workspace")
    myresult = cursor.fetchall()
    #Convertir los datos a diccionario
    insertObject = []
    columnNames = [column[0] for column in cursor.description]
    for record in myresult:
        insertObject.append(dict(zip(columnNames, record)))
    cursor.close()
    ### Registra LOG ###
    id_accion = 'mwsi' #ingreso APP
    id_reporte = 'Workspace' 
    detalle = 'Ingresa modulo Workspace '
    inserta_LOG(id_accion, id_reporte, detalle)      
    return render_template('Workspace.html', data=insertObject)

#Ruta para guardar grupos en la bdd
@app.route('/addWorkspace', methods=['POST'])
@csrf.exempt
def addWorkspace():
    id_workspace = request.form['id_workspace']
    workspace_id = request.form['workspace_id']
    workspace = request.form['workspace']
    estado = request.form['estado']
       
    if id_workspace and workspace_id and workspace and estado:
        cursor = database.cursor()
        sql = "INSERT INTO workspace (id_workspace, workspace_id, workspace, estado) VALUES (%s, %s, %s, %s)"
        data = (id_workspace, workspace_id, workspace, estado)
        cursor.execute(sql, data)
        database.commit()
        ### Registra LOG ###
        id_accion = 'mwsa' #ingreso APP
        id_reporte = 'Workspace' 
        detalle = 'Agrega Workspace: ' + id_workspace + ' ' + workspace 
        inserta_LOG(id_accion, id_reporte, detalle)  
    return redirect(url_for('hWorkspace'))

@app.route('/deleteWorkspace/<string:id>',methods=['POST'])
@csrf.exempt
def deleteWorkspace(id):
    #### Obtengo datos a eliminar ###
    cursor = database.cursor()
    cursor.execute("SELECT concat(id_workspace , ' ', workspace, ' ' ,workspace_id) res FROM workspace WHERE id = %s",(id,))
    reg = cursor.fetchone()
    result= reg[0]
    cursor.close()
    ###################################        
    cursor = database.cursor()
    sql = "DELETE FROM workspace WHERE id=%s"
    data = (id,)
    cursor.execute(sql, data)
    database.commit()
    ### Registra LOG ################
    id_accion = 'mwsb' #ingreso APP
    id_reporte = 'Workspace' 
    detalle = 'Borra Workspace: ' + id + ' ' + result
    inserta_LOG(id_accion, id_reporte, detalle)        
    return redirect(url_for('hWorkspace'))

@app.route('/editWorkspace/<string:id>', methods=['POST'])
@csrf.exempt
def editWorkspace(id):
    id_workspace = request.form['id_workspace']
    workspace_id = request.form['workspace_id']
    workspace = request.form['workspace']
    estado = request.form['estado']
   
    if id_workspace and workspace_id and workspace and estado:
        cursor = database.cursor()
        sql = "UPDATE workspace SET id_workspace = %s, workspace_id = %s, workspace = %s, estado = %s WHERE id = %s"
        data = (id_workspace, workspace_id, workspace, estado, id)
        cursor.execute(sql, data)
        database.commit()
        ### Registra LOG ###
        id_accion = 'mwse' #ingreso APP
        id_reporte = 'Workspace' 
        detalle = 'Edita Workspace: ' + id_workspace + ' ' + workspace 
        inserta_LOG(id_accion, id_reporte, detalle)          
    return redirect(url_for('hWorkspace'))

#################################################################################

def inserta_LOG( id_accion, id_reporte, detalle):
    fechor = datetime.datetime.now()
    id_usuario =session['username']
    ip = '' # get_ip()
    cursor = database.cursor()
    sql = "INSERT INTO log (fechor, id_usuario, id_accion, id_reporte, ip, detalle) VALUES (%s,%s, %s, %s, %s, %s)"
    data = (fechor, id_usuario, id_accion, id_reporte, ip, detalle)
    cursor.execute(sql, data)
    database.commit()


#################################################################################

### MRC 28-08-2024 Grupos por usuario que inicio sesión ###
@app.route('/get_grupo')
def get_grupo():
    '''Retorna la lista de grupos que tiene el usuario que inicio sesión'''
    try:
       logged_in_user =session.get('username')
       #print(logged_in_user)
       cursorgrp = database1.cursor()
       sql = """
            SELECT g.id_grupo, g.grupo
            FROM grupos g
            LEFT JOIN grupo_usuario gu ON gu.id_grupo = g.id_grupo
            WHERE g.estado = 1 AND gu.id_usuario = %s
 
            UNION ALL
 
            SELECT '0000', 'Todos'
            order by 1
            """
       datag = (logged_in_user,)
       cursorgrp.execute(sql, datag)
       myresultg = cursorgrp.fetchall()
       #print(myresultg)
       group_data = [{'id_grupo': record[0], 'grupo': record[1]} for record in myresultg]
       cursorgrp.close()
       #print(group_data)
       return jsonify(group_data)
    except Exception as ex:
        return jsonify({'errorMsg': str(ex)}), 500
 
@app.route('/get_reportg/<id_grupo>', methods=['GET', 'POST'])
def get_reportg(id_grupo):
    '''Retorna la lista de reportes del usuario'''
    try:
       user_name =session.get('username')
       cursorrep = database.cursor()
       #print('id_grupo en app.py:  ',id_grupo)
       if id_grupo == "0000":
        sql = """
            SELECT distinct r.report_id, r.reporte
            FROM reportes r
            INNER JOIN grupo_reporte gr ON r.id_reporte = gr.id_reporte
            INNER JOIN grupo_usuario gu ON gr.id_grupo = gu.id_grupo
            WHERE gu.id_usuario = %s
            ;
        """
        data = (user_name,)
       else:
        sql = """
            SELECT distinct r.report_id, r.reporte
            FROM reportes r
            INNER JOIN grupo_reporte gr ON r.id_reporte = gr.id_reporte
            INNER JOIN grupo_usuario gu ON gr.id_grupo = gu.id_grupo
            WHERE gu.id_usuario = %s
              AND gr.id_grupo = %s;
        """
        data = (user_name, id_grupo)          
 
       cursorrep.execute(sql , data)
       myresult = cursorrep.fetchall()
       reports_info = [{'reportId': record[0], 'reportName': record[1]} for record in myresult]
       cursorrep.close()
       #print('reports_info en app.py:  ',reports_info)
 
       return jsonify(reports_info)
    except Exception as ex:
        return jsonify({'errorMsg': str(ex)}), 500
 

#################################################################################
#################################################################################

@app.route('/shutdown', methods=['POST'])
@csrf.exempt  # Exentar de CSRF

def shutdown():
    """Cierra el servidor Flask cuando se recibe la solicitud POST"""
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        return jsonify({"message": "No se puede apagar el servidor"}), 500
    func()
    return jsonify({"message": "Servidor cerrado"}), 200

def shutdown_server():
    """Función para detener el servidor Flask"""
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('No se puede apagar el servidor')
    func()

def open_browser():
    """Función para abrir el navegador automáticamente"""
    webbrowser.open_new('http://127.0.0.1:5000/')
    #webbrowser.open_new('http://demo.biservice.cl:5000/')
    

###################################################################################
def add_host_entry(hostname, ip_address='127.0.0.1'):
    try:
        hosts_path = 'C:\\Windows\\System32\\drivers\\etc\\hosts'
    # Verifica si la entrada ya existe
        with open(hosts_path, 'r+') as file:
            lines = file.readlines()
            if any(f"{ip_address} {hostname}" in line for line in lines):
                #print(f"La entrada '{hostname}' ya existe en el archivo hosts.")
                return
            
            # Si no existe, agrega la nueva entrada
            file.write(f"{ip_address} {hostname}\n")
            #print(f"La entrada '{hostname}' ha sido añadida al archivo hosts.")
    
    except Exception as Ex:
        print("Ejecute aplicación como administrador") 

################################################################################
###############################################################################


if __name__ == '__main__':
    ##### 12-08-2024 #########
    app.config.from_object(config['development'])
    csrf.init_app(app) ##### impedia actualizar perdiendo el csrf en otras paginas
    app.register_error_handler(401, status_401)
    app.register_error_handler(404, status_404)
    ##### 12-08-2024 #########
    #app.run(debug = True) # debug = True = permite actualizar y levantar servicio automatico
    #app.run(host='0.0.0.0', port=8000) # debug = True = permite actualizar y levantar servicio automatico

    # registrar una nueva entrada en el archivo hosts de Windows
    add_host_entry('demo.biservice.cl')

    # Solo abre el navegador si el servidor no está reiniciando
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        Timer(1, open_browser).start()

    app.run()
