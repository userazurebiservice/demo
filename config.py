# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

class BaseConfig(object):

    # Can be set to 'MasterUser' or 'ServicePrincipal'
    AUTHENTICATION_MODE = 'MasterUser'

    # Workspace Id in which the report is present
    WORKSPACE_ID = '17f32aa0-e011-4d5a-adc0-3c2e729f9882'
    
    # Report Id for which Embed token needs to be generated
    REPORT_ID = ''#'4d697e33-8ddf-4ddc-8892-800b2af3db21'#'73401b0c-214d-4429-baaf-a8652370173a'
    
    # Id of the Azure tenant in which AAD app and Power BI report is hosted. Required only for ServicePrincipal authentication mode.
    TENANT_ID = '60be1b2a-3165-4a98-b9f2-ec90e0147eff'
    
    # Client Id (Application Id) of the AAD app
    #CLIENT_ID = '91e4cf1f-7f27-4ca8-ae6b-21e6031d85a0'
    CLIENT_ID = 'fbbc39e3-28ae-413d-9bc7-24a6e3425c23'

    # Client Secret (App Secret) of the AAD app. Required only for ServicePrincipal authentication mode.
    CLIENT_SECRET = ''
    
    # Scope Base of AAD app. Use the below configuration to use all the permissions provided in the AAD app through Azure portal.
    SCOPE_BASE = ['https://analysis.windows.net/powerbi/api/.default']
    
    # URL used for initiating authorization request
    #AUTHORITY_URL = 'https://login.microsoftonline.com/organizations'
    AUTHORITY_URL = f'https://login.microsoftonline.com/{TENANT_ID}'
    
    # Master user email address. Required only for MasterUser authentication mode.
    #POWER_BI_USER = 'userazure@biservice.cl'
    POWER_BI_USER = 'userpbi1@biservice.cl'
    #POWER_BI_USER = 'mrojas@biservice.cl'

    # Master user email password. Required only for MasterUser authentication mode.
    #POWER_BI_PASS = 'azureuser.2024'
    POWER_BI_PASS = 'USUARIO.0924'
    #POWER_BI_PASS = 'mrojas.2024'

    EMBED_URL = 'https://app.powerbi.com/reportEmbed'

########### 12-08-2024 ########################
class Config:
    SECRET_KEY = 'B!1w8NAt1T^%kvhUI*S^'


class DevelopmentConfig(Config):
    DEBUG = True
    MYSQL_HOST = 'mysqlbiservice.mysql.database.azure.com'
    MYSQL_USER = 'userazuremysql' # encriptar con mismo metodo de password usuario
    MYSQL_PASSWORD = 'admin.2024' 
    MYSQL_DB = 'demo_biservice'

config = {
    'development': DevelopmentConfig
}

