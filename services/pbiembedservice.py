from services.aadservice import AadService
from models.reportconfig import ReportConfig
from models.embedtoken import EmbedToken
from models.embedconfig import EmbedConfig
from models.embedtokenrequestbody import EmbedTokenRequestBody
from flask import current_app as app, abort
import requests
import json

class PbiEmbedService:

    def get_embed_params_for_single_report(self, workspace_id, report_id, additional_dataset_id=None):
        report_url = f'https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/reports/{report_id}'   
           
        api_response = requests.get(report_url, headers=self.get_request_header())
        print(api_response)
        if api_response.status_code != 200:
            abort(api_response.status_code, description=f'Error while retrieving Embed URL\n{api_response.reason}:\t{api_response.text}\nRequestId:\t{api_response.headers.get("RequestId")}')

        api_response = json.loads(api_response.text)
        report = ReportConfig(api_response['id'], api_response['name'], api_response['embedUrl'])
        dataset_ids = [api_response['datasetId']]

        # Append additional dataset to the list to achieve dynamic binding later
        if additional_dataset_id is not None:
            dataset_ids.append(additional_dataset_id)

        embed_token = self.get_embed_token_for_single_report_single_workspace(report_id, dataset_ids, workspace_id)
        embed_config = EmbedConfig(embed_token.tokenId, embed_token.token, embed_token.expiration, [report.__dict__])
        return json.dumps(embed_config.__dict__)

  
    def get_embed_token_for_single_report_single_workspace(self, report_id, dataset_ids, target_workspace_id=None):

        request_body = EmbedTokenRequestBody()

        for dataset_id in dataset_ids:
            request_body.datasets.append({'id': dataset_id})

        request_body.reports.append({'id': report_id})

        if target_workspace_id is not None:
            request_body.targetWorkspaces.append({'id': target_workspace_id})

        # Generate Embed token for multiple workspaces, datasets, and reports. Refer https://aka.ms/MultiResourceEmbedToken
        embed_token_api = 'https://api.powerbi.com/v1.0/myorg/GenerateToken'
        api_response = requests.post(embed_token_api, data=json.dumps(request_body.__dict__), headers=self.get_request_header())

        if api_response.status_code != 200:
            abort(api_response.status_code, description=f'Error while retrieving Embed token\n{api_response.reason}:\t{api_response.text}\nRequestId:\t{api_response.headers.get("RequestId")}')

        api_response = json.loads(api_response.text)
        embed_token = EmbedToken(api_response['tokenId'], api_response['token'], api_response['expiration'])
    
        return embed_token


    def get_reports_in_workspace(self, workspace_id):
        reports_url = f'https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/reports'
        api_response = requests.get(reports_url, headers=self.get_request_header())

        if api_response.status_code != 200:
            abort(api_response.status_code, description=f'Error while retrieving reports\n{api_response.reason}:\t{api_response.text}\nRequestId:\t{api_response.headers.get("RequestId")}')

        api_response = json.loads(api_response.text)
        reports = [ReportConfig(report['id'], report['name'], report['embedUrl'], report['datasetId']) for report in api_response['value']]
        return reports
    

    def get_request_header(self):
        '''Get Power BI API request header

        Returns:
            Dict: Request header
        '''

        return {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + AadService.get_access_token()}
