import requests
import requests_cache
import json
import time
from IPython.core.display import clear_output
import pandas as pd
from tqdm import tqdm

requests_cache.install_cache()
tqdm.pandas()

API_KEY = '2a92fc61b8cbf94eba59fd5c02fbe21a'
USER_AGENT = 'Topher1217'

def lastfm_get(payload):
    headers = {'user-agent': USER_AGENT}
    payload['format'] = 'json'
    payload['api_key'] = API_KEY
    return requests.get('http://ws.audioscrobbler.com/2.0/', headers=headers, params=payload)

def lookup_tags(artist):
    response = lastfm_get({'method': 'artist.getTopTags', 'artist': artist})
    if response.status_code != 200:
        return None
    tags = [t['name'] for t in response.json()['toptags']['tag'][:3]]
    tags_str = ', '.join(tags)
    if not getattr(response,'from_cache',False):
        time.sleep(0.25)
    return tags_str

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

artists['tags'] = artists['name'].progress_apply(lookup_tags)

artists[['playcount', 'listeners']] = artists[['playcount', 'listeners']].astype(int)
artists = artists.sort_values('listeners',ascending=False)

artists.to_csv('artists.csv',index=False)