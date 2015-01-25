''' Convert XML to CSV.

Usage:
    ./convert_xml XML_FILE
    ./convert_xml (-h | --help)

Options:
    -h --help   Show this message.
'''
import pandas as pd
from bs4 import BeautifulSoup
from docopt import docopt

def convert_xml_df(file_in, file_out=None):
    xml_file = open(file_in).read()
    xml = BeautifulSoup(xml_file)
    lines = xml.findAll('linha')

    column_names = set()
    for line in lines:
        for col in line:
            column_names.add(col.name)

    df = pd.DataFrame.from_records([{col.name: col.text for col in line} for line in lines],
                           columns=column_names)

    if not file_out:
        file_out = file_in.replace('.xml', '.csv')

    df.to_csv(file_out, encoding='utf8', index=False)
    return df

if __name__ == '__main__':
    arguments = docopt(__doc__)
    convert_xml_df(arguments['XML_FILE'])
