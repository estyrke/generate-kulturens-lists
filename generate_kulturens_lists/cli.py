# -*- coding: utf-8 -*-

__doc__ = """Skript för att generera närvarolistor till Kulturens.

Indata är URL till en närvarorapport i Google Sheets med följande innehåll ("1" indikerar närvaro och "-" frånvaro):

       ,         ,      ,         ,Datum        ,2013-09-03   ,2013-09-10   ,[...]
       ,         ,      ,         ,Tid          ,19-21:30     ,19-21:30     ,[...]
       ,         ,      ,Kommentar,Aktivitet    ,Ordinarie rep,Ordinarie rep,[...]
       ,         ,      ,         ,Total närvaro,29           ,30           ,[...]
Förnamn,Efternamn,Stämma,         ,             ,             ,             ,[...]
Hans   ,Lundgren ,dir   ,         ,20           ,1            ,-            ,[...]
[...]

Data ska ligga i ett blad som heter "Närvaro".

Samt en matrikel i tabbseparerat "CSV"-format från internwebben.

"""

from .internwebb import InternwebbReader
from .googlesheets import AttendanceReader
from .pdf import PdfGenerator

__author__ = 'emil'

import csv
import datetime
import getpass
import click
import logging

from .config import Config

config = Config('config.json')

@click.command()
@click.option('--username', prompt='Användarnamn till internwebben', help='Användarnamn till internwebben')
@click.option('--password', prompt='Lösenord till internwebben', help='Lösenord till internwebben', hide_input=True)
@click.option('--url', metavar='URL', prompt='Adress (URL) till närvarorapporten', help='Adress (URL) till närvarorapporten')
@click.option('--output_filename', metavar='PDF', help='Filnamn för utdata')
@click.option('--debug/--no-debug')
def cli(username, password, url, output_filename, debug):
    if debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig()
    internwebb = InternwebbReader(config.BASE_URL, username, password)
    attendance = AttendanceReader(url)
    pdf = PdfGenerator(config)

    leaders = [l.strip() for l in config.LEADERS.split(',')]
    output_filename = output_filename or '{}.pdf'.format(attendance.get_title())

    pdf.create_pdf(output_filename, attendance.get_attendance(internwebb.get_all_users(), leaders))


if __name__=="__main__":
    cli()
