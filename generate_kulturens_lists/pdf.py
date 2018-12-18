
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

import os


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

class PdfGenerator:
    def __init__(self, config):
        self.config = config
        pdf_template_filename = os.path.join(os.path.dirname(__file__), 'narvarolista_tom.pdf')
        self.template = MyTemplate(pdf_template_filename)
        self.pdf_report = None

    def drawPage(self, attendance, attendees, leader1):
        self.pdf_report.saveState()
        self.pdf_report.setFont("Helvetica", 10)
        self.pdf_report.drawString(220, 765, self.config.CHOIR_NAME)
        self.pdf_report.setFont("Times-Roman", 9)
        self.pdf_report.drawString(357, 730, leader1.fullname)
        self.pdf_report.drawString(357, 712, leader1.member.address1)
        self.pdf_report.drawString(357, 703, leader1.member.address2)

        self.pdf_report.setFont("Times-Italic", 8)
        self.pdf_report.drawString(61, 663, attendance.get_start_date().strftime('%d/%m'))
        self.pdf_report.drawString(111, 663, self.config.MEETING_TIME)
        self.pdf_report.drawString(181, 663, self.config.MEETING_DAY)
        self.pdf_report.drawString(249, 663, self.config.CHOIR_NAME)

        self.pdf_report.drawString(96, 640, self.config.MEETING_ADDRESS1)
        self.pdf_report.drawString(96, 631, self.config.MEETING_ADDRESS2)

        for i, e in enumerate(attendance.events):
            self.addEvent(i, e)

        for i, a in enumerate(attendees):
            self.addPerson(i, a)

        self.pdf_report.restoreState()

    def addPerson(self, pos, attendee, **kwargs):
        self.pdf_report.saveState()

        y = 602 - (pos * 26.28)

        if attendee.is_leader:
            self.pdf_report.setFont("Times-Bold", 10)
        else:
            self.pdf_report.setFont("Times-Roman", 10)

        self.pdf_report.drawString(96, y, attendee.firstname + " " + attendee.lastname)

        addrLine = attendee.member.address1 + ", " + attendee.member.address2
        while self.pdf_report.stringWidth(addrLine, "Times-Roman", 10) > 170:
            addrLine = addrLine[:-1]
        self.pdf_report.drawString(96, y-10, addrLine)

        def filter_phone(phone):
            return "".join(filter(lambda c: c in "01234567890+-", phone))

        if attendee.member.homePhone:
            self.pdf_report.drawString(268, y, "B {}".format(filter_phone(attendee.member.homePhone)))

        if attendee.member.mobile:
            self.pdf_report.drawString(268, y-9, "M {}".format(filter_phone(attendee.member.mobile)))

        pnr = attendee.pnr
        if pnr:
            self.pdf_report.setFont("Times-Roman", 6.6)
            self.pdf_report.drawString(50, y-11, pnr)

            #Kryss för kvinna
            if attendee.is_female:
                self.pdf_report.setFont("Times-Bold", 10)
                self.pdf_report.drawString(62, y, "X")

        self.addAttendance(y, attendee.attendance)
        self.pdf_report.restoreState()

    def addEvent(self, pos, event):
        self.pdf_report.saveState()

        x = 347 + pos * 11.3

        self.pdf_report.setFont("Helvetica", 7)

        self.pdf_report.drawString(x, 665, str(event[0].day))
        self.pdf_report.drawString(x, 642, str(event[0].month))
        self.pdf_report.drawString(x, 200, str(event[3]))
        #self.pdf_report.drawString(x, 175, "3")

        # Add time if different from regular time. Rotate so adjacent entries don't overlap
        if event[1] and event[1] != self.config.MEETING_TIME:
            self.pdf_report.saveState()
            self.pdf_report.translate(x, 615)
            self.pdf_report.rotate( 45 )
            self.pdf_report.drawString(0, 0, str(event[1]))
            self.pdf_report.restoreState()

        self.pdf_report.restoreState()


    def addAttendance(self, y, attendance):
        self.pdf_report.saveState()

        for i, a in enumerate(attendance):
            x = 349 + i * 11.3

            self.pdf_report.setFont("Helvetica", 13)
            #self.pdf_report.setFillColorRGB(0.2, 0.2, 0.2)

            if a:
                self.pdf_report.drawString(x, y-3, "/")
            else:
                self.pdf_report.drawString(x, y-3, "-")

        self.pdf_report.restoreState()

    def create_pdf(self, filename, attendance):
        """Create the pdf, with all the contents"""
        self.pdf_report = canvas.Canvas(filename, pagesize=A4)

        leader1 = attendance.getLeader1()
        attendees = attendance.getAttendees()

        for page in range(0, len(attendees), 15):
            a2 = attendance
            while True:
                a1, a2 = a2.split(20)

                self.template.beforeDrawPage(self.pdf_report)
                self.drawPage(a1, a1.attendees[page:page+15], leader1)
                self.pdf_report.showPage()

                if len(a2.events) == 0:
                    break

        self.pdf_report.save()
        self.pdf_report = None