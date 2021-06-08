import json
import toml
import os
import urllib.parse
import urllib.request
from os.path import expanduser as eu

prefect_settings = toml.load(eu('~/.prefect/client/https-api.prefect.io-graphql/settings.toml')) 
PREFECT__CLOUD__API = 'https://api.prefect.io/'
PREFECT__CLOUD__AUTH_TOKEN = prefect_settings['api_token'] 

def api_call():
    query_ = '''
    {
    flow (where: {name: {_eq: "getting-started-example"}}){
        name
        id
  }
}
    '''

    data = json.dumps(dict(query=query_)).encode('utf-8')

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
    print('type(response)',type(response))
    print("response['data']['flow'][0]['id']", response['data']['flow'][0]['id'])
