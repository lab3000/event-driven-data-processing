import json
import os
import urllib.parse
import urllib.request
from os.path import expanduser as eu

prefect_settings = toml.load(eu('~/.prefect/client/https-api.prefect.io-graphql/settings.toml')) 
api_token = prefect_settings['api_token'] 

query_ = '''
query {
    flow { 
        name 
        id
    }
}
'''

data = json.dumps(dict(query=query_)).encode('utf-8')

## prep the request
req = urllib.request.Request(api_token, data=data)
req.add_header("Content-Type", "application/json")
req.add_header(
    "Authorization", "Bearer {}".format(os.getenv("PREFECT__CLOUD__AUTH_TOKEN"))
)
