## generate-kulturens-lists
[![FOSSA Status](https://app.fossa.com/api/projects/git%2Bgithub.com%2Festyrke%2Fgenerate-kulturens-lists.svg?type=shield)](https://app.fossa.com/projects/git%2Bgithub.com%2Festyrke%2Fgenerate-kulturens-lists?ref=badge_shield)


Närvarorapportering till Kulturens.

### För att installera
 * Installera Python
 * Installera generate_kulturens_lists: `pip install generate_kulturens_lists-<version>.whl`

### För att skapa ett installationspaket
 * Installera Python och pipenv (`pip install pipenv`)
 * Installera paket: pipenv install
 * Skapa ett "OAuth Client ID" för Google Sheets på https://console.developers.google.com/apis/credentials.
   * Ladda ner den resulterande json-filen och spara i `generate_kulturens_lists/credentials.json`
 * Kör `pipenv run python setup.py bdist_wheel`
 * Paketet finns nu i `dist/generate_kulturens_lists-<version>.whl`


## License
[![FOSSA Status](https://app.fossa.com/api/projects/git%2Bgithub.com%2Festyrke%2Fgenerate-kulturens-lists.svg?type=large)](https://app.fossa.com/projects/git%2Bgithub.com%2Festyrke%2Fgenerate-kulturens-lists?ref=badge_large)