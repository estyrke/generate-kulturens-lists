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

from .internwebb import InternwebbReader
from .googlesheets import AttendanceReader
from .pdf import create_pdf

__author__ = 'emil'

import csv
import datetime
import getpass
import click
import logging

from . import config

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
    output_filename = output_filename or '{}.pdf'.format(attendance.get_title())
    #matrikel = parse_matrikel(MATRIKEL_FILE)
    #attendance = parse_attendance(ATTENDANCE_FILE)
    create_pdf(output_filename, "narvarolista_tom.pdf", attendance.get_attendance(internwebb.get_all_users(), config.LEADERS))


if __name__=="__main__":
    cli()
