import requests

with open('licenses.db', 'rb') as f:
    res = requests.post('https://prodesk-api1.onrender.com/upload_db', files={'file': f}, timeout=20)
    print(res.text)
    print("STATUS CODE:", res.status_code)