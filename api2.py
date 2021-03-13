import requests
import requests_cache
import json
import time
from IPython.core.display import clear_output
import pandas as pd

requests_cache.install_cache()

API_KEY = '2a92fc61b8cbf94eba59fd5c02fbe21a'
USER_AGENT = 'Topher1217'

headers = {
    'user-agent': USER_AGENT
}

payload = {
    'api_key':API_KEY,
    'format':'json',
    'method':'chart.gettopartists'
}

def jprint(obj):
    print(json.dumps(obj, sort_keys=True, indent=4))

def lastfm_get(payload):
    headers = {'user-agent': USER_AGENT}
    payload['format'] = 'json'
    payload['api_key'] = API_KEY
    return requests.get('http://ws.audioscrobbler.com/2.0/', headers=headers, params=payload)

response = lastfm_get({'method': 'chart.gettopartists'})
text = json.dumps(response.json(), sort_keys=True, indent=4)
print(response.status_code)
jprint(response.json()['artists']['@attr'])

responses = []

page = 1
total_pages = 99999

while page < total_pages:
    payload = {
        'method': 'chart.gettopartists',
        'limit': 500,
        'page': page
    }
    print('Requesting page {}/{}'.format(page,total_pages))
    clear_output(wait=True)
    response = lastfm_get(payload)
    if response.status_code!=200:
        print(response.text)
        break
    page = int(response.json()['artists']['@attr']['page'])
    total_pages = int(response.json()['artists']['@attr']['totalPages'])
    responses.append(response)
    if not getattr(response, 'from_cache', False):
        time.sleep(0.25)
    page+=1

frames = [pd.DataFrame(r.json()['artists']['artist']) for r in responses]
artists = pd.concat(frames)
artists = artists.drop('image',axis=1)
artists = artists.drop_duplicates().reset_index(drop=True)
artists.head()
artists.info()
artists.describe()