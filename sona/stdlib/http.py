from . import native_http


def get(url):
    return native_http.http_get(url)


def post(url, data):
    return native_http.http_post(url, data)
