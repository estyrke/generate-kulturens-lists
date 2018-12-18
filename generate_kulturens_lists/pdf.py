
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

from . import config


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

def drawPage(canvas, attendance, attendees, leader1):
    canvas.saveState()
    canvas.setFont("Helvetica", 10)
    canvas.drawString(220, 765, config.CHOIR_NAME)
    canvas.setFont("Times-Roman", 9)
    canvas.drawString(357, 730, leader1.fullname)
    canvas.drawString(357, 712, leader1.member.address1)
    canvas.drawString(357, 703, leader1.member.address2)

    canvas.setFont("Times-Italic", 8)
    canvas.drawString(61, 663, attendance.get_start_date().strftime('%d/%m'))
    canvas.drawString(111, 663, config.MEETING_TIME)
    canvas.drawString(181, 663, config.MEETING_DAY)
    canvas.drawString(249, 663, config.CHOIR_NAME)

    canvas.drawString(96, 640, config.MEETING_ADDRESS1)
    canvas.drawString(96, 631, config.MEETING_ADDRESS2)

    for i, e in enumerate(attendance.events):
        addEvent(canvas, i, e)

    for i, a in enumerate(attendees):
        addPerson(canvas, i, a)

    canvas.restoreState()


def addPerson(canv, pos, attendee, **kwargs):
    canv.saveState()

    y = 602 - (pos * 26.28)

    if attendee.is_leader:
        canv.setFont("Times-Bold", 10)
    else:
        canv.setFont("Times-Roman", 10)

    canv.drawString(96, y, attendee.firstname + " " + attendee.lastname)

    addrLine = attendee.member.address1 + ", " + attendee.member.address2
    while canv.stringWidth(addrLine, "Times-Roman", 10) > 170:
        addrLine = addrLine[:-1]
    canv.drawString(96, y-10, addrLine)

    def filter_phone(phone):
        return "".join(filter(lambda c: c in "01234567890+-", phone))

    if attendee.member.homePhone:
        canv.drawString(268, y, "B {}".format(filter_phone(attendee.member.homePhone)))

    if attendee.member.mobile:
        canv.drawString(268, y-9, "M {}".format(filter_phone(attendee.member.mobile)))

    pnr = attendee.pnr
    if pnr:
        canv.setFont("Times-Roman", 7)
        canv.drawString(52, y-11, pnr)

        #Kryss för kvinna
        if attendee.is_female:
            canv.setFont("Times-Bold", 10)
            canv.drawString(62, y, "X")

    addAttendance(canv, y, attendee.attendance)
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
    if event[1] and event[1] != config.MEETING_TIME:
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

def create_pdf(filename, pdf_template_filename, attendance):
    """Create the pdf, with all the contents"""
    pdf_report = canvas.Canvas(filename, pagesize=A4)
    template = MyTemplate(pdf_template_filename)

    leader1 = attendance.getLeader1()
    attendees = attendance.getAttendees()

    for page in range(0, len(attendees), 15):
        a2 = attendance
        while True:
            a1, a2 = a2.split(20)

            template.beforeDrawPage(pdf_report)
            drawPage(pdf_report, a1, a1.attendees[page:page+15], leader1)
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