from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
import re
import datetime
import logging
import copy
import bisect
import os
from functools import total_ordering

from .errors import GenerateError

# If modifying these scopes, delete the file token.json.
SCOPES = 'https://www.googleapis.com/auth/spreadsheets.readonly'

def authenticate():
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    store = file.Storage('token.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets(os.path.join(os.path.dirname(__file__), 'credentials.json'), SCOPES)
        creds = tools.run_flow(flow, store)

    return creds


@total_ordering
class Attendee:
    def __init__(self, firstname, lastname, comment, total, attendance):
        self.firstname = firstname.strip()
        self.lastname = lastname.strip()
        self.comment = comment.strip()
        self.total = total
        self.attendance = attendance
        self.member = None
        self.leader = False
        self._pnr = None

        if sum(attendance) != int(total):
            raise GenerateError("Totalen stämmer inte för {} {}: {} vs {}".format(firstname, lastname, sum(attendance), int(total)))

    def setPersonalData(self, member):
        if self.member:
            if self.member.is_active:
                if not member.is_active:
                    logging.debug('Previous set member is active, use that one')
                    pass
                else:
                    logging.error('Multiple active members with same name!')
                    raise GenerateError('Flera aktiva medlemmar med namnet {} {}!'.format(self.member.firstname, self.member.lastname))
            else:
                if member.is_active:
                    logging.debug('New member is active, replacing.')
                    self.member = member
                else:
                    logging.debug('Both new and previous member inactive, doing nothing.')
                    pass
        else:
            self.member = member

    def setLeader(self, is_leader=True):
        self.leader = is_leader

    @property
    def is_leader(self):
        return self.leader

    @property
    def fullname(self):
        return "{} {}".format(self.firstname, self.lastname)
    
    @property
    def pnr(self):
        if self._pnr is None:
            pnr = self.member.pnr
            if pnr is None:
                self._pnr = None
            elif len(pnr) == 13 and pnr[8] == '-':
                self._pnr = pnr
            elif len(pnr) == 11 and pnr[6] == '-':
                self._pnr = '19{}'.format(pnr)
            elif len(pnr) == 10 and '-' not in pnr:
                self._pnr = '19{}-{}'.format(pnr[:6], pnr[6:])
            elif len(pnr) == 8 and '-' not in pnr:
                logging.warning('{} har ofullständigt personnummer: {}'.format(self.fullname, pnr))
                self._pnr = '{}-xxxx'.format(pnr)
            elif len(pnr) == 6 and '-' not in pnr:
                logging.warning('{} har ofullständigt personnummer: {}'.format(self.fullname, pnr))
                self._pnr = '19{}-xxxx'.format(pnr)
            else:
                raise GenerateError('Ogiltigt personnummer för {}: "{}"'.format(self.fullname, pnr))
        return self._pnr

    @property
    def is_female(self):
        return self.pnr and self.pnr[11].isdigit() and int(self.pnr[11]) % 2 == 0

    def split(self, n):
        attendance1 = self.attendance[:n]
        attendance2 = self.attendance[n:]
        a1 = copy.deepcopy(self)
        a2 = copy.deepcopy(self)
        a1.total, a1.attendance = sum(attendance1), attendance1
        a2.total, a2.attendance = sum(attendance2), attendance2

        assert len(a1.attendance) == n or len(a2.attendance) == 0
        assert a2.member

        return a1, a2

    def __eq__(self, other):
        return self.fullname == other.fullname
        
    def __lt__(self, other):
        return (not self.is_leader, self.lastname, self.firstname) < (not other.is_leader, other.lastname, other.firstname)

    def __str__(self):
        return self.fullname

    def __repr__(self):
        return self.fullname


class Attendance(object):
    def __init__(self, matrikel, leaders):
        self.matrikel = matrikel
        self.leaders = leaders
        self.events = []
        self.attendees = []

    def addEvent(self, date, time, comment, total):
        if len(date) == 0:
            return

        self.events.append((datetime.datetime.strptime(date, "%Y-%m-%d"), time, comment, int(total)))

    def addAttendee(self, firstname, lastname, comment, total, attendance):
        attendance = [a == "1" for a in attendance]

        if len(attendance) > len(self.events):
            if sum(attendance[len(self.events):]) > 0:
                raise GenerateError("{} {} är registrerad på {} av {} sammankomster".format(firstname, lastname, len(attendance), len(self.events)))
            attendance = attendance[:len(self.events)]

        if not any(attendance):
            print('{} {} har aldrig varit närvarande, hoppar över.'.format(firstname, lastname))
            return

        a = Attendee(firstname, lastname, comment, int(total), attendance)
        a.setLeader(a.fullname in self.leaders)

        for m in self.matrikel:
            if a.fullname == m.firstname.strip() + " " + m.lastname.strip():
                a.setPersonalData(m)

        if not a.member:
            print("'{}', '{}' saknas i matrikeln.  Har du stavat rätt?".format(a.lastname, a.firstname))

        bisect.insort(self.attendees, a)

    def getLeader1(self):
        for i in self.attendees:
            if self.leaders[0] == i.fullname:
                return i
        raise IndexError('{} finns inte i närvarorapporten!'.format(self.leaders[0]))

    def getAttendees(self):
        return self.attendees

    def get_start_date(self):
        return self.events[0][0]

    def split(self, n):
        a1 = Attendance(self.matrikel, self.leaders)
        a2 = Attendance(self.matrikel, self.leaders)

        a1.events = self.events[:n]
        a2.events = self.events[n:]

        for a in self.attendees:
            att1, att2 = a.split(n)
            bisect.insort(a1.attendees, att1)
            bisect.insort(a2.attendees, att2)

        a1.verify()
        a2.verify()

        return a1, a2

    def verify(self):
        for i, e in enumerate(self.events):
            total = sum([0 if len(a.attendance) <= i else a.attendance[i] for a in self.attendees])
            if total != e[3]:
                raise RuntimeError("Attendance mismatch for %s: %d vs %d" % (e[0], total, e[3]))

        leaders = [a for a in self.attendees if a.leader]
        if len(leaders) != len(self.leaders):
            print(leaders)
            print(self.leaders)
            raise GenerateError('Hittade {} ledare i kalkylarket, men {} var konfigurerade!'.format(len(leaders), len(self.leaders)))


class AttendanceReader:
    SHEET_ID_RE = re.compile('.*/spreadsheets/d/([^/]+)/.*')

    def __init__(self, sheet_url):
        m = self.SHEET_ID_RE.match(sheet_url)
        if not m:
            raise RuntimeError('Unable to find sheet id from url {}'.format(sheet_url))
        self.sheet_id = m.group(1)

        creds = authenticate()
        self.service = build('sheets', 'v4', http=creds.authorize(Http()), cache_discovery=False)

        # Call the Sheets API
        self.sheet_service = self.service.spreadsheets()
        self.document = self.sheet_service.get(spreadsheetId=self.sheet_id).execute()

    def get_title(self):
        return self.document['properties']['title']

    def get_attendance(self, matrikel, leaders):
        range = "'Närvaro'"
        result = self.sheet_service.values().get(spreadsheetId=self.sheet_id,
                                    range=range).execute()
        values = result.get('values', [])

        return parse_attendance(values, matrikel, leaders)


def parse_attendance(lines, matrikel, leaders):
    attendance = Attendance(matrikel, leaders)
    dates = lines[0][5:]
    times = lines[1][5:]
    comments = lines[2][5:]
    total = lines[3][5:]

    for date, time, comment, total in zip(dates, times, comments, total):
        attendance.addEvent(date, time, comment, total)

    for fields in lines[5:]:
        if len(fields) < 5 or len(fields[0]) == 0:
            continue

        attendance.addAttendee(fields[0], fields[1], fields[3], fields[4], fields[5:])

    attendance.verify()
    return attendance
