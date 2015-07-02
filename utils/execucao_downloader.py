#!/usr/bin/env python
# coding: utf-8

''' Downloads execucao data. If no 'year' is passed, download all.

Usage: execucao_downloader [options] [<year>...]

Options:
-h, --help                        Show this message.
-o, --outfolder <outfolder>       Folder where to place files.
                                  Can be relative.
                                  [default: current folder]

Exemples:

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
import pyexcel
from pyexcel.ext import ods3, xls


def normalize_spreedsheet(sheet):
    # Normalize column names to lower case
    # (it changed from mixed to upper at some point in History)
    sheet.colnames = [i.lower() for i in sheet.colnames]

    # Remove empty column, if exists
    try:
        del sheet.column['']
    except ValueError:
        pass
    # if sheet.colnames[-1] == '':
    #     last_column = len(sheet.colnames) - 1
    #     del sheet.column[last_column]

    # Remove last row when it is empty
    if sheet.column[0][-1] == '':
        last_row = len(sheet.column[0]) - 1
        del sheet.row[last_row]

    # Convert float years to int
    for colname in ["cd_anoexecucao", "cd_exercicio"]:
        try:
            index = sheet.colnames.index(colname)
            sheet.column.format(index, int)
        except ValueError:
            pass

    # Nomalize dates
    def norm_date(value):
        if not (isinstance(value, datetime.date) or
                isinstance(value, datetime.datetime)):
            value = datetime.datetime.strptime(value, "%d/%m/%Y %H:%M:%S")
        return datetime.datetime.strftime(value, "%Y-%m-%d")
    for colname in ["datainicial", "datafinal"]:
        try:
            index = sheet.colnames.index(colname)
            sheet.column.format(index, norm_date)
        except ValueError:
            pass

def convert_spreedsheet(in_file, out_file):
    # To allow ODS and XLS need these libs imported:
    ods3 and xls

    sheet = pyexcel.get_sheet(file_name=in_file, name_columns_by_row=0)
    normalize_spreedsheet(sheet)
    sheet.save_as(out_file)


def download_year(year, outpath):
    """Download a year to 'outpath'.
    'year' should be a string."""
    baseurl = "http://orcamento.prefeitura.sp.gov.br/orcamento/uploads/"
    url = baseurl + "{year}/basedadosexecucao{year}.ods".format(year=year)
    outfilepath = os.path.join(outpath, "%s.ods" % year)
    # Try to get ODS
    try:
        _, r = urlretrieve(url, outfilepath)
        # Probably 404 - Only needed in Python 2
        if int(r['content-length']) < 1000:
            os.remove(outfilepath)
            raise
    except:
        # Try to get XLS
        url = baseurl + "{year}/basedadosexecucao{year}.xls".format(year=year)
        outfilepath = os.path.join(outpath, "%s.xls" % year)
        urlretrieve(url, outfilepath)
    # Convert to CSV
    convert_spreedsheet(outfilepath, os.path.join(outpath, "%s.csv" % year))
    print(year + " done")


def download_all(outpath):
    """Download all years to 'outpath'."""
    first_year = 2003
    current_year = datetime.date.today().year
    for year in range(first_year, current_year+1):
        download_year(str(year), outpath)


if __name__ == '__main__':
    arguments = docopt(__doc__)
    out_folder = arguments['--outfolder']
    years = arguments['<year>']
    if out_folder == "current folder":
        out_folder = os.getcwd()
    if not years:
        download_all(out_folder)
    else:
        for year in years:
            download_year(year, out_folder)
    # download_all(out_folder)
