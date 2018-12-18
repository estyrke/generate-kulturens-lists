from appJar import gui
import logging
import sys

from .internwebb import InternwebbReader
from .googlesheets import AttendanceReader
from .pdf import PdfGenerator

from .config import Config

config = Config('config.json')

def generate(app, url, username, password):
    try:
        internwebb = InternwebbReader(config.BASE_URL, username.get(), password.get())
        attendance = AttendanceReader(url.get())
        pdf_generator = PdfGenerator(config)

        output_filename = '{}.pdf'.format(attendance.get_title())
        output_filename = app.saveBox('Välj destination', fileName=output_filename, fileExt='.pdf')
        print(output_filename)

        leaders = [l.strip() for l in config.LEADERS.split(',')]
        pdf_generator.create_pdf(output_filename, attendance.get_attendance(internwebb.get_all_users(), leaders))
    except Exception as e:
        app.errorBox('Ett fel inträffade', e)
        raise e
    app.infoBox('Klart!', 'Genereringen är klar!')


config_field_map = {
    'URL till internwebben': 'BASE_URL',
    'Körens namn': 'CHOIR_NAME',
    'Körens adress': 'MEETING_ADDRESS1',
    'Körens postadress': 'MEETING_ADDRESS2',
    'Dag för sammankomster': 'MEETING_DAY',
    'Tid för sammankomster': 'MEETING_TIME',
    'Ledare (separera med kommatecken)': 'LEADERS'
}


def config_save(app):
    for label, config_key in config_field_map.items():
        value = app.getEntry(label)
        config.set(config_key, value)
    
    config.save()


def config_load(app):
    for label, config_key in config_field_map.items():
        app.addLabelEntry(label)
        app.setEntry(label, getattr(config, config_key, ''))


def main():
    logging.basicConfig()

    with gui('Generate Kulturens Lists') as app:
        with app.tabbedFrame('Test'):
            with app.tab('Konfigurering'):
                config_load(app)
                app.addButton("Spara", lambda x: config_save(app))
            with app.tab('Generering'):
                url = app.addLabelEntry('URL till närvarorapporten')
                username = app.addLabelEntry('Användarnamn till internwebben')
                password = app.addLabelSecretEntry('Lösenord till internwebben')
                app.addButton("Generera", lambda: generate(app, url, username, password))
        app.addButton("Avsluta", lambda: sys.exit(0))

        app.go()


if __name__ == '__main__':
    main()
