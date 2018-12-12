# -*- coding: utf-8 -*-

__doc__ = """Skript för att generera närvarolistor till Kulturens.

Indata är en närvarorapport i CSV-format ("1" indikerar närvaro och "-" frånvaro):

       ,         ,      ,         ,Datum        ,2013-09-03   ,2013-09-10   ,[...]
       ,         ,      ,         ,Tid          ,19-21:30     ,19-21:30     ,[...]
       ,         ,      ,Kommentar,Aktivitet    ,Ordinarie rep,Ordinarie rep,[...]
       ,         ,      ,         ,Total närvaro,29           ,30           ,[...]
Förnamn,Efternamn,Stämma,         ,             ,             ,             ,[...]
Hans   ,Lundgren ,dir   ,         ,20           ,1            ,-            ,[...]
[...]

Samt en matrikel i tabbseparerat "CSV"-format. Första raden är rubriker, resterande rader är medlemmar, en per rad.
De intressanta kolumnerna är dessa:

  Kolumn 0: Adressrad 1
  Kolumn 1: Adressrad 2
  Kolumn 2: Adressrad 3
  Kolumn 3-5: ignoreras
  Kolumn 6: Efternamn
  Kolumn 7-8: ignoreras
  Kolumn 9: Förnamn
  Kolumn 10-14: ignoreras
  Kolumn 15: Personnummer
  Kolumn 16: Postadress
  Kolumn 17-23: ignoreras
  Kolumn 24: Hemtelefon
  Kolumn 25: Mobiltelefon

"""

from .config import *
from .internwebb import InternwebbReader

__author__ = 'emil'

import csv
import datetime

from reportlab.platypus import PageTemplate, BaseDocTemplate, Frame
from reportlab.platypus import NextPageTemplate, Paragraph, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.graphics import renderPDF
from reportlab.pdfgen import canvas

from pdfrw import PdfReader
from pdfrw.buildxobj import pagexobj
from pdfrw.toreportlab import makerl

PAGE_WIDTH = A4[0]
PAGE_HEIGHT = A4[1]


class MyTemplate():
    """The kernel of this example, where we use pdfrw to fill in the
    background of a page before writing to it.  This could be used to fill
    in a water mark or similar."""

    def __init__(self, pdf_template_filename, name=None):
        # use first page as template
        page = PdfReader(pdf_template_filename).pages[0]
        self.page_template = pagexobj(page)
        # Scale it to fill the complete page
        self.page_xscale = PAGE_WIDTH/self.page_template.BBox[2]
        self.page_yscale = PAGE_HEIGHT/self.page_template.BBox[3]

    def beforeDrawPage(self, canvas):
        """Draws the background before anything else"""
        canvas.saveState()
        rl_obj = makerl(canvas, self.page_template)
        canvas.scale(self.page_xscale, self.page_yscale)
        canvas.doForm(rl_obj)
        canvas.restoreState()

def drawPage(canvas, members, attendance):
    canvas.saveState()
    canvas.setFont("Helvetica", 10)
    canvas.drawString(220, 765, CHOIR_NAME)
    canvas.setFont("Times-Roman", 9)
    canvas.drawString(357, 730, LEADER_NAME)
    canvas.drawString(357, 712, LEADER_ADDRESS)
    canvas.drawString(357, 703, LEADER_ADDRESS2)

    canvas.setFont("Times-Italic", 8)
    canvas.drawString(61, 663, START_DATE)
    canvas.drawString(111, 663, MEETING_TIME)
    canvas.drawString(181, 663, MEETING_DAY)
    canvas.drawString(249, 663, CHOIR_NAME)

    canvas.drawString(96, 640, MEETING_ADDRESS1)
    canvas.drawString(96, 631, MEETING_ADDRESS2)

    for i, e in enumerate(attendance.events):
        addEvent(canvas, i, e)

    for i, m in enumerate(members):
        att = attendance.getAttendance(m.firstname, m.lastname)
        addPerson(canvas, i, m, att)

    canvas.restoreState()


def addPerson(canv, pos, member, attendance, **kwargs):
    canv.saveState()

    y = 602 - (pos * 26.28)

    if member.leader:
        canv.setFont("Times-Bold", 10)
    else:
        canv.setFont("Times-Roman", 10)

    canv.drawString(96, y, member.firstname + " " + member.lastname)

    addrLine = member.address1.decode("utf-8") + ", " + member.address2.decode("utf-8")
    while canv.stringWidth(addrLine, "Times-Roman", 10) > 170:
        addrLine = addrLine[:-1]
    canv.drawString(96, y-10, addrLine)

    if member.homePhone:
        canv.drawString(268, y, "B %s" % [c for c in member.homePhone if c in "01234567890+-"])

    if member.mobile:
        canv.drawString(268, y-9, "M %s" % [c for c in member.mobile if c in "01234567890+-"])

    if member.pnr:
        canv.setFont("Times-Roman", 7)
        canv.drawString(52, y-11, member.pnr)

        #Kryss för kvinna
        if int(member.pnr[9]) % 2 == 0:
            canv.setFont("Times-Bold", 10)
            canv.drawString(62, y, "X")

    addAttendance(canv, y, attendance)
    canv.restoreState()

def addEvent(canv, pos, event):
    canv.saveState()

    x = 347 + pos * 11.3

    canv.setFont("Helvetica", 7)

    canv.drawString(x, 665, str(event[0].day))
    canv.drawString(x, 642, str(event[0].month))
    canv.drawString(x, 200, str(event[3]))
    #canv.drawString(x, 175, "3")

    # Add time if different from regular time. Rotate so adjacent entries don't overlap
    if event[1] and event[1] != "19-21:30":
        canv.saveState()
        canv.translate(x, 615)
        canv.rotate( 45 )
        canv.drawString(0, 0, str(event[1]))
        canv.restoreState()

    canv.restoreState()


def addAttendance(canv, y, attendance):
    canv.saveState()

    for i, a in enumerate(attendance):
        x = 349 + i * 11.3

        canv.setFont("Helvetica", 13)
        #canv.setFillColorRGB(0.2, 0.2, 0.2)

        if a:
            canv.drawString(x, y-3, "/")
        else:
            canv.drawString(x, y-3, "-")

    canv.restoreState()


def create_pdf(filename, pdf_template_filename, members, attendance):
    """Create the pdf, with all the contents"""
    pdf_report = canvas.Canvas(filename, pagesize=A4)
    template = MyTemplate(pdf_template_filename)

    members.sort(key=lambda m: m.firstname)
    members.sort(key=lambda m: m.lastname)
    members.sort(key=lambda m: not m.leader)

    for a in attendance.attendees:
        found = False
        for m in members:
            if a[0].strip() + " " + a[1].strip() == m.firstname.strip() + " " + m.lastname.strip():
                found = True

        if not found:
            print("Member %s %s not found" % (a[0], a[1]))

    for page in range(0, len(members), 15):
        a2 = attendance
        while True:
            a1, a2 = a2.split(20)

            template.beforeDrawPage(pdf_report)
            drawPage(pdf_report, members[page:page+15], a1)
            pdf_report.showPage()

            if len(a2.events) == 0:
                break

    pdf_report.save()
    #document.addPageTemplates(templates)

    styles = getSampleStyleSheet()
    elements = [NextPageTemplate('background')]

    # Dummy content (hello world x 200)
    #for i in range(200):
    #    elements.append(Paragraph("Hello World" + str(i), styles['Heading1']))

    #document.multiBuild(elements)
    #pdf_report.close()


class Member(object):
    def __init__(self, fields):
        self.firstname = fields[9]
        self.lastname = fields[6]
        self.mobile = fields[25] or None
        self.homePhone = fields[24] or None
        self.address1 = ", ".join([x for x in fields[0:3] if len(x) > 0])
        self.address2 = fields[16]
        self.pnr = fields[15] or None
        self.leader = self.firstname.strip() + " " + self.lastname.strip() in LEADERS


def parse_matrikel(filename):

    with open(filename, 'r') as csvfile:
        reader = csv.reader(csvfile, dialect='excel-tab')
        members = []
        header = next(reader)
        for row in reader:
            member = Member(row)
            members.append(member)

        return members

class Attendance(object):
    def __init__(self):
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
                raise RuntimeError("%s %s registered for %d of %d events" % (firstname, lastname, len(attendance), len(self.events)))
            attendance = attendance[:len(self.events)]

        if sum(attendance) != int(total):
            raise RuntimeError("Attendance mismatch for %s %s: %d vs %d" % (firstname, lastname, sum(attendance), int(total)))
        self.attendees.append((firstname, lastname, comment, int(total), attendance))

    def getAttendance(self, firstname, lastname):
        for i in self.attendees:
            if i[0].strip() == firstname.strip() and i[1].strip() == lastname.strip():
                return i[4]

        print("Attendee %s %s not found" % (firstname, lastname))
        return [False for i in range(len(self.events))]

    def split(self, n):
        a1 = Attendance()
        a2 = Attendance()

        a1.events = self.events[:n]
        a2.events = self.events[n:]

        for a in self.attendees:
            attendance1 = a[4][:n]
            attendance2 = a[4][n:]
            a1.attendees.append((a[0], a[1], a[2], sum(attendance1), attendance1))
            a2.attendees.append((a[0], a[1], a[2], sum(attendance2), attendance2))

        a1.verify()
        a2.verify()

        return a1, a2

    def verify(self):
        for i, e in enumerate(self.events):
            total = sum([a[4][i] for a in self.attendees])
            if total != e[3]:
                raise RuntimeError("Attendance mismatch for %s: %d vs %d" % (e[0], total, e[3]))


def parse_attendance(filename):
    lines = []
    with open(filename.decode('utf-8'), 'rb') as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='"')
        for row in reader:
            lines.append(row)

    attendance = Attendance()
    dates = lines[0][5:]
    times = lines[1][5:]
    comments = lines[2][5:]
    total = lines[3][5:]

    for date, time, comment, total in zip(dates, times, comments, total):
        attendance.addEvent(date, time, comment, total)

    for fields in lines[5:]:
        if len(fields[0]) == 0:
            continue

        attendance.addAttendee(fields[0], fields[1], fields[3], fields[4], fields[5:])

    attendance.verify()
    return attendance


def main():
    matrikel = parse_matrikel(MATRIKEL_FILE)
    attendance = parse_attendance(ATTENDANCE_FILE)
    create_pdf(OUTPUT_FILE, "narvarolista_tom.pdf", matrikel, attendance)


if __name__=="__main__":
    main()