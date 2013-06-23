# -*- coding: utf-8 -*-

from config import *

__author__ = 'emil'

from reportlab.platypus import PageTemplate, BaseDocTemplate, Frame
from reportlab.platypus import NextPageTemplate, Paragraph, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.rl_config import defaultPageSize
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.graphics import renderPDF

from pdfrw import PdfReader
from pdfrw.buildxobj import pagexobj
from pdfrw.toreportlab import makerl

PAGE_WIDTH = defaultPageSize[0]
PAGE_HEIGHT = defaultPageSize[1]


class MyTemplate(PageTemplate):
    """The kernel of this example, where we use pdfrw to fill in the
    background of a page before writing to it.  This could be used to fill
    in a water mark or similar."""

    def __init__(self, pdf_template_filename, name=None):
        frames = [Frame(
            0.85 * inch,
            0.5 * inch,
            PAGE_WIDTH - 1.15 * inch,
            PAGE_HEIGHT - (1.5 * inch)
            )]
        PageTemplate.__init__(self, name, frames)
        # use first page as template
        page = PdfReader(pdf_template_filename).pages[0]
        self.page_template = pagexobj(page)
        # Scale it to fill the complete page
        self.page_xscale = PAGE_WIDTH/self.page_template.BBox[2]
        self.page_yscale = PAGE_HEIGHT/self.page_template.BBox[3]

    def beforeDrawPage(self, canvas, doc):
        """Draws the background before anything else"""
        canvas.saveState()
        rl_obj = makerl(canvas, self.page_template)
        canvas.scale(self.page_xscale, self.page_yscale)
        canvas.doForm(rl_obj)
        canvas.restoreState()

class MyDocTemplate(BaseDocTemplate):
    """Used to apply heading to table of contents."""

    def beforePage(self):
        self.canv.saveState()
        self.canv.setFont("Helvetica", 10)
        self.canv.drawString(220, 765, CHOIR_NAME)
        self.canv.setFont("Times-Roman", 9)
        self.canv.drawString(357, 730, LEADER_NAME)
        self.canv.drawString(357, 712, LEADER_ADDRESS)
        self.canv.drawString(357, 703, LEADER_ADDRESS2)

        self.canv.setFont("Times-Italic", 8)
        self.canv.drawString(61, 663, START_DATE)
        self.canv.drawString(111, 663, MEETING_TIME)
        self.canv.drawString(181, 663, MEETING_DAY)
        self.canv.drawString(249, 663, CHOIR_NAME)

        self.canv.drawString(96, 640, MEETING_ADDRESS1)
        self.canv.drawString(96, 631, MEETING_ADDRESS2)

        addPerson(self.canv, 1, LEADER_NAME, LEADER_ADDRESS + ", " + LEADER_ADDRESS2, homePhone=LEADER_HOME_PHONE, mobilePhone=LEADER_MOBILE_PHONE, pnr=LEADER_PNR, bold=True)
        addPerson(self.canv, 2, LEADER2_NAME, LEADER2_ADDRESS, mobilePhone=LEADER2_MOBILE_PHONE, pnr=LEADER2_PNR)

        self.canv.restoreState()


def addPerson(canv, pos, name, address, **kwargs):
    canv.saveState()

    y = 628 - (pos * 26)

    if kwargs.get('bold', False):
        canv.setFont("Times-Bold", 10)
    else:
        canv.setFont("Times-Roman", 10)

    canv.drawString(96, y, name)
    canv.drawString(96, y-9, address)

    if 'homePhone' in kwargs:
        canv.drawString(268, y, "B %s" % kwargs['homePhone'])

    if 'mobilePhone' in kwargs:
        canv.drawString(268, y-9, "M %s" % kwargs['mobilePhone'])

    if 'pnr' in kwargs:
        canv.setFont("Times-Roman", 7)
        canv.drawString(52, y-11, kwargs['pnr'])

    canv.restoreState()

def create_pdf(filename, pdf_template_filename):
    """Create the pdf, with all the contents"""
    pdf_report = open(filename, "w")
    document = MyDocTemplate(pdf_report)
    templates = [MyTemplate(pdf_template_filename, name='background')]
    document.addPageTemplates(templates)

    styles = getSampleStyleSheet()
    elements = [NextPageTemplate('background')]

    # Dummy content (hello world x 200)
    #for i in range(200):
    #    elements.append(Paragraph("Hello World" + str(i), styles['Heading1']))

    document.multiBuild(elements)
    pdf_report.close()

def main():
    create_pdf("hello.pdf", "narvarolista_tom.pdf")


if __name__=="__main__":
    print pdfmetrics.standardFonts
    main()