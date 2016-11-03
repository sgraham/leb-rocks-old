import httplib2
import json
from slugify import slugify  # sudo pip install python-slugify
import os
import urllib
from urlparse import urlparse

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage


import argparse
flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()

SCOPES = 'https://www.googleapis.com/auth/spreadsheets.readonly'
CLIENT_SECRET_FILE = 'scratch/client_secret.json'
APPLICATION_NAME = 'Data Exporter'

CATEGORY_LIST_HEADER = '''<script>
var categoryList = [
'''

CATEGORY_TEMPLATE = '''  {{
    name: '{name}',
    title: '{title}',
    image: '/images/{name}.jpg'
  }}'''

CATEGORY_LIST_FOOTER = '''
];
</script>
'''

def GetCredentials():
  """Gets valid user credentials from storage.

  If nothing has been stored, or if the stored credentials are invalid,
  the OAuth2 flow is completed to obtain the new credentials.

  Returns:
      Credentials, the obtained credential.
  """
  home_dir = 'scratch'
  credential_dir = os.path.join(home_dir, '.credentials')
  if not os.path.exists(credential_dir):
    os.makedirs(credential_dir)
  credential_path = os.path.join(credential_dir,
                                 'sheets.googleapis.com-data_exporter.json')

  store = Storage(credential_path)
  credentials = store.get()
  if not credentials or credentials.invalid:
    flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
    flow.user_agent = APPLICATION_NAME
    if flags:
      credentials = tools.run_flow(flow, store, flags)
    else: # Needed only for compatibility with Python 2.6
      credentials = tools.run(flow, store)
    print('Storing credentials to ' + credential_path)
  return credentials


def main():
  credentials = GetCredentials()
  http = credentials.authorize(httplib2.Http())
  discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?'
                  'version=v4')
  service = discovery.build('sheets', 'v4', http=http,
                            discoveryServiceUrl=discoveryUrl)

  spreadsheet_id = '1duWPCxITIkeX7SXNmSQr80wRKN2OXGWU8EjnW8EpS_I'
  sheets_data = service.spreadsheets().get(
      spreadsheetId=spreadsheet_id).execute()
  titles = []
  for sheet in sheets_data.get('sheets', []):
    titles.append(sheet['properties']['title'])
  for title in titles:
    range_name = title
    # FORMULA for image column to get =IMAGE('...')
    # FORMATTED_VALUE for main retrieval.
    result_formatted = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id, range=range_name,
        valueRenderOption='FORMATTED_VALUE').execute()
    values = result_formatted.get('values', [])
    result_formulas = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id, range=range_name,
        valueRenderOption='FORMULA').execute()
    formulas = result_formulas.get('values', [])

    first_row = values[0]
    rest_rows_values = values[1:]
    rest_rows_formulas = formulas[1:]

    def get_at_index(L, index):
      val = L[index:index+1]
      if len(val) == 0:
        return u''
      return val[0]

    def munge_image_formula(formula):
      prefix = '=image("'
      if formula.lower().startswith(prefix):
        url = formula[len(prefix):-2]
        filename = os.path.split(urlparse(url).path)[-1]
        output_name = 'appengine/data/images/' + filename
        if not os.path.exists(output_name):
          urllib.urlretrieve(url, output_name)
        return '/data/images/' + filename
      else:
        # Bail.
        return formula

    title_as_unicode = title.encode('utf-8')
    title_slug = slugify(title_as_unicode)
    columns = [slugify(col) for col in first_row]
    # For each row, pull out and store into an object we'll spit to json.
    sheet_items = []
    for i in range(len(rest_rows_values)):
      data = {}
      for j, col in enumerate(columns):
        if col == 'image':
          value = get_at_index(rest_rows_formulas[i], j)
        else:
          value = get_at_index(rest_rows_values[i], j)
        data[col] = value
      data['title'] = data['name']
      data['name'] = slugify(data['name'])
      if data['price'].startswith('$'):
        data['price'] = data['price'][1:]
      data['price'] = float(data['price'])
      data['category'] = title_slug
      data['image'] = munge_image_formula(data.get('image'))
      data['largeImage'] = data['image']
      sheet_items.append(data)

    with open('appengine/data/' + title_slug + '.json', 'w') as f:
      f.write(json.dumps(sheet_items,
                         sort_keys=True, indent=2, separators=(',', ': ')))

  category_data = []
  for title in titles:
    title_as_unicode = title.encode('utf-8')
    category_data.append(CATEGORY_TEMPLATE.format(
      name=slugify(title_as_unicode), title=title_as_unicode))

  with open('appengine/data/category-list.html', 'w') as f:
    f.write(CATEGORY_LIST_HEADER)
    f.write(',\n'.join(category_data))
    f.write(CATEGORY_LIST_FOOTER)


if __name__ == '__main__':
  main()
