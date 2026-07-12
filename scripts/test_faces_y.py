import urllib.request, json
try:
    req = urllib.request.Request("http://127.0.0.1:8765/api/selection")
    with urllib.request.urlopen(req) as res:
        data = json.loads(res.read().decode())
        print(data)
except Exception as e:
    print(e)
