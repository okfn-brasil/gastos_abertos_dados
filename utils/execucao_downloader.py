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


import os
from datetime import date
# Python 2 and 3...
try:
    from urllib import urlretrieve
except:
    from urllib.request import urlretrieve

from docopt import docopt
import pyexcel
from pyexcel.ext import ods3, xls


def convert_spreedsheet(in_file, out_file):
    # To allow ODS and XLS need these libs imported:
    ods3 and xls

    sheet = pyexcel.get_sheet(file_name=in_file)

    # Remove last column when it is empty
    if sheet.row[0][-1] == '':
        last_column = len(sheet.row[0]) - 1
        del sheet.column[last_column]
    # Remove last row when it is empty
    if sheet.column[0][-1] == '':
        last_row = len(sheet.column[0]) - 1
        del sheet.row[last_row]
    # Normalize column names to lower case
    # (it changed from mixed to upper at some point in History)
    sheet.row[0] = [i.lower() for i in sheet.row[0]]

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
    current_year = date.today().year
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
