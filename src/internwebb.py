import requests
import csv

from .config import BASE_URL

class InternwebbReader:
    def __init__(self, username, password):
        res = requests.post(BASE_URL, data={'action': 'login', 'name': username, 'password': password})
        if res.status_code != 200:
            raise RuntimeError('Failed to log in to internwebb!')
        self.cookies = res.history[0].cookies

    def get_page(self, location, **kwargs):
        return requests.get(BASE_URL + location, cookies=self.cookies, **kwargs)

    def get_all_users(self):
        res = self.get_page('matrikel?action=search&searchtext=&searchfield=all&groupop=or&sortfield=lastnamefirstname&type=radata')
        users = csv.DictReader(res.text.splitlines(), dialect="excel-tab")
        return users
