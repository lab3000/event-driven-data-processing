import sys
import json
import toml
import os
import urllib.parse
import urllib.request
from os.path import expanduser as eu

prefect_settings = toml.load(eu('~/.prefect/client/https-api.prefect.io-graphql/settings.toml')) 
PREFECT__CLOUD__API = 'https://api.prefect.io/'
PREFECT__CLOUD__AUTH_TOKEN = prefect_settings['api_token'] 
PREFECT__FLOW_ID = sys.argv[1]

def api_call():
    create_mutation = """
    mutation($input: createFlowRunInput!){
        createFlowRun(input: $input){
            flow_run{
                id
            }
        }
    }
    """

    inputs = dict(flowId=PREFECT__FLOW_ID)

    variables = dict(input=inputs)
    data = json.dumps(
        dict(query=create_mutation, variables=json.dumps(variables))
    ).encode("utf-8")

    ## prep the request
    req = urllib.request.Request(PREFECT__CLOUD__API, data=data)
    req.add_header("Content-Type", "application/json")
    req.add_header(
        "Authorization", "Bearer {}".format(PREFECT__CLOUD__AUTH_TOKEN)
    )

    resp = urllib.request.urlopen(req)
    return json.loads(resp.read().decode())

if __name__=='__main__':
    response = api_call()
    print(response)