__author__ = 'emil'

from reportlab.pdfgen import canvas

def main():
    c = canvas.Canvas("hello.pdf")
    c.drawString(100, 100, "Hello World")
    c.showPage()
    c.save()


if __name__=="__main__":
    main()