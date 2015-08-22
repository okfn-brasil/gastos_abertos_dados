#!/usr/bin/env python
# coding: utf-8

''' Downloads, converts and normalize execucao data. If no 'year' is passed,
download all.

Usage: execucao_downloader [options] [<year>...]

Options:
-h, --help                        Show this message.
-o, --outfolder <outfolder>       Folder where to place files.
                                  Can be relative.
                                  [default: current folder]

Examples:

execucao_downloader 2014
(downloads year 2014)

execucao_downloader -o nice/path/
(downloads all years to folder 'nice/path/')
'''


from __future__ import unicode_literals  # unicode by default
import os
import datetime
# Python 2 and 3...
try:
    from urllib import urlretrieve
except:
    from urllib.request import urlretrieve

from docopt import docopt
import pandas as pd
import pyexcel
from pyexcel.ext import ods3, xls
# To allow ODS and XLS need these libs imported:
ods3 and xls
# (yes, I know, the above line seems useless, but it avoids 'imported but
# unused' warnings in my Python linter [*genious*] =P )


def convert_codes_to_int(table):
    '''Convert float years/codes to int'''
    non_monetary_series = [col for name, col in table.iteritems()
                           if name[:3] != 'vl_' and name[:4] != 'sld_']
    # code_series = []
    for col in non_monetary_series:
        # Checks if column has only integers
        try:
            table[col.name] = col.apply(int)
            # code_series.append(col)
        except ValueError:
            pass
    return non_monetary_series
    # return code_series


def normalize_csv(csv_path):
    '''Tries to normalize small differences between csvs.'''

    table = pd.read_csv(csv_path)

    # Normalize column names to lower case
    # (it changed from mixed to upper at some point in History)
    table.columns = [c.lower() for c in table.columns]
    # Remove empty column, if exists
    table = table.select(lambda x: x.find('unnamed'), axis=1)

    # Remove last row when it is empty
    last_line = table.iloc[-1]
    if len(last_line) == last_line.isnull().values.sum():
        table.drop(table.index[-1], inplace=True)

    non_monetary_series = convert_codes_to_int(table)

    # Nomalize dates
    def norm_date(value):
        if not (isinstance(value, datetime.date) or
                isinstance(value, datetime.datetime)):
            try:
                value = datetime.datetime.strptime(value, '%d/%m/%Y %H:%M:%S')
            except ValueError:
                try:
                    value = datetime.datetime.strptime(value,
                                                       '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    value = datetime.datetime.strptime(value, '%Y-%m-%d')
        return datetime.datetime.strftime(value, '%Y-%m-%d')
    for colname in ['datainicial', 'datafinal']:
        if colname in table.columns:
            table[colname] = table[colname].apply(norm_date)

    # Attempt to sum lines that have different monetary values but all the
    # other columns are equal. This happens in old years and unable PKs.
    non_monetary_names = [col.name for col in non_monetary_series]
    num_duplicated_rows = table[non_monetary_names].duplicated().sum()
    if num_duplicated_rows:
        table = table.groupby(non_monetary_names, as_index=False).sum()
        print('%s rows had all non monetary values repeated and were summed.' %
              num_duplicated_rows)

    code_series = [col for name, col in table.iteritems()
                   if name[:3].lower() == 'cd_']
    # this column doesn't start with 'cd_' but is a code
    code_series.append(table['projetoatividade'])
    # create table of codes
    code_table = pd.concat(code_series, axis=1)
    # create PK Series
    pks = pd.Series(['.'.join([str(i) for i in i[1][1:]])
                    for i in code_table.iterrows()],
                    name='pk')
    # check pk uniqueness
    if pks.duplicated().values.sum() > 0:
        print('Warning: There are duplicated pks!')

    table.to_csv(csv_path, index=False)


def convert_spreadsheet(in_file, out_file):
    '''Converts from one format of spreadsheet to another.'''
    sheet = pyexcel.get_sheet(file_name=in_file, name_columns_by_row=0)
    sheet.save_as(out_file)


def convert_to_csv(infilepath, outpath):
    '''Convert to CSV.'''
    csv_name = os.path.splitext(os.path.basename(infilepath))[0] + '.csv'
    csv_path = os.path.join(outpath, csv_name)
    print('converting...')
    convert_spreadsheet(infilepath, csv_path)
    print('normalizing...')
    normalize_csv(csv_path)
    return csv_path


def download_year(year, outpath):
    '''Download a year to 'outpath'. Returns te path to the downloaded file.
    'year' should be a string.'''

    print('> ' + year)
    print('downloading...')
    baseurl = 'http://orcamento.prefeitura.sp.gov.br/orcamento/uploads/'
    url = baseurl + '{year}/basedadosexecucao{year}.ods'.format(year=year)
    outfilepath = os.path.join(outpath, '%s.ods' % year)
    # Try to get ODS
    try:
        _, r = urlretrieve(url, outfilepath)
        # Probably 404 - Only needed in Python 2
        if int(r['content-length']) < 1000:
            os.remove(outfilepath)
            raise
    except:
        # Try to get XLS
        url = baseurl + '{year}/basedadosexecucao{year}.xls'.format(year=year)
        outfilepath = os.path.join(outpath, '%s.xls' % year)
        urlretrieve(url, outfilepath)

    return outfilepath


def process_year(year, outpath):
    '''Downloads a year data and converts to CSV.'''
    outfilepath = download_year(str(year), outpath)
    convert_to_csv(outfilepath, outpath)


def process_all(outpath):
    '''Process all years to 'outpath'.'''
    first_year = 2003
    current_year = datetime.date.today().year
    for year in range(first_year, current_year+1):
        process_year(year, outpath)


if __name__ == '__main__':
    arguments = docopt(__doc__)
    out_folder = arguments['--outfolder']
    years = arguments['<year>']
    if out_folder == 'current folder':
        out_folder = os.getcwd()
    if not years:
        process_all(out_folder)
    else:
        for year in years:
            process_year(year, out_folder)
