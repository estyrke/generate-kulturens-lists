import requests
import csv
from urllib.parse import urljoin

from .errors import GenerateError

class Member(object):
    def __init__(self, fields, is_active):
        self.firstname = fields['firstname']
        self.lastname = fields['lastname']
        self.mobile = fields['phone_cellular'] or None
        self.homePhone = fields['phone_home'] or None
        self.address1 = ", ".join([fields[f] for f in ['address_1', 'address_2', 'address_3'] if len(fields[f]) > 0])
        self.address2 = fields['postal_address']
        self.pnr = fields['personal_number'] or None
        self.fields = fields
        self.is_active = is_active

def parse_matrikel(matrikel, active):
    members = []
    for row in matrikel:
        member = Member(row, is_active=row in active)
        members.append(member)

    return members

class InternwebbReader:
    def __init__(self, base_url, username, password):
        self.base_url = base_url

        if not base_url.lower().startswith('https'):
            raise RuntimeError('BASE_URL in config.py must start with https')
            
        res = requests.post(base_url, data={'action': 'login', 'name': username, 'password': password})
        if res.status_code != 200:
            raise GenerateError('Kunde inte logga in till internwebben! (http status {} vid inloggning)'.format(res.status_code))
        
        self.cookies = res.cookies
        for h in res.history:
            self.cookies.update(h.cookies)

    def get_page(self, location, **kwargs):
        return requests.get(urljoin(self.base_url, location), cookies=self.cookies, **kwargs)

    def get_all_users(self):
        # Fetch all members
        res = self.get_page('matrikel?action=search&searchtext=&searchfield=all&groupop=or&sortfield=lastnamefirstname&type=radata')
        if res.status_code != 200 or not res.headers['content-type'].startswith('text/plain'):
            # Probably an error page
            raise GenerateError('Kunde inte hämta matrikeldata (alla)!')

        users = list(csv.DictReader(res.text.splitlines(), dialect="excel-tab"))

        # Fetch active members
        res = self.get_page('matrikel?action=search&searchtext=&searchfield=all&groups%5B%5D=1057&groupop=or&sortfield=lastnamefirstname&type=radata')
        if res.status_code != 200 or not res.headers['content-type'].startswith('text/plain'):
            # Probably an error page
            raise GenerateError('Kunde inte hämta matrikeldata (aktiva)!')

        active_users = list(csv.DictReader(res.text.splitlines(), dialect="excel-tab"))
        return parse_matrikel(users, active_users)
