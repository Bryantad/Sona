import requests

def http_get(url):
    response = requests.get(url)
    return response.text

def http_post(url, data):  # Renamed from 'post' to 'http_post'
    try:
        response = requests.post(url, json=data)
        return response.text
    except Exception as e:
        return f"[http error] {e}"
