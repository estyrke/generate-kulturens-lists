from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
import re

# If modifying these scopes, delete the file token.json.
SCOPES = 'https://www.googleapis.com/auth/spreadsheets.readonly'

def authenticate():
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    store = file.Storage('token.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('credentials.json', SCOPES)
        creds = tools.run_flow(flow, store)

    return creds

class AttendanceReader:
    SHEET_ID_RE = re.compile('spreadsheets/d/([^/]+)/')

    def __init__(self, sheet_url):
        m = self.SHEET_ID_RE.match(sheet_url).group(1)
        if not m:
            raise RuntimeError('Unable to find sheet id from url {}'.format(sheet_url))
        self.sheet_id = m.group(1)

        creds = authenticate()
        self.service = build('sheets', 'v4', http=creds.authorize(Http()))

    def get_attendance(self):
        # Call the Sheets API
        sheet = self.service.spreadsheets()
        range = 'Class Närvaro!1:100'
        result = sheet.values().get(spreadsheetId=self.sheet_id,
                                    range=range).execute()
        values = result.get('values', [])

        return values
    