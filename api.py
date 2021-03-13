import requests
import json
from datetime import datetime

response = requests.get("http://api.open-notify.org/astros.json")
text = json.dumps(response.json(), sort_keys=True, indent=4)
print(text)

params = {
    "lat": 40.71,
    "lon": -74
}

response = requests.get("http://api.open-notify.org/iss-pass.json", params=params)
text = json.dumps(response.json(), sort_keys=True, indent=4)
print(text)

pass_times = response.json()['response']
print(pass_times)

risetimes = []

for d in pass_times:
    time = datetime.fromtimestamp(d['risetime']).strftime('%Y-%m-%d %H:%M:%S')
    risetimes.append(time)

print(risetimes)