import urllib.request
from urllib.error import HTTPError

try:
    urllib.request.urlopen('http://localhost:5000/')
except HTTPError as e:
    with open('error.html', 'wb') as f:
        f.write(e.read())
