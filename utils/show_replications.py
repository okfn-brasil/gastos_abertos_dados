# -*- coding: utf-8 -*-

''' Read a CSV and write to another CSV the replicated (date,code) lines.

Usage:
    ./import_revenue [FILE]
    ./import_revenue (-h | --help)

Options:
    -h --help   Show this message.
'''
import csv
from datetime import datetime, timedelta
import calendar
import pandas as pd
from docopt import docopt


def parse_money(money_string):
    if money_string[0] == '-':
        return -float(money_string[3:].replace('.', '').replace(',', '.'))
    else:
        return float(money_string[3:].replace('.', '').replace(',', '.'))


def parse_date(date_string):
    year_month = datetime.strptime(date_string, '%Y-%m')
    date = year_month + timedelta(
        days=calendar.monthrange(
            year_month.year, year_month.month
        )[1] - 1)
    return date


def parse_code(code_string):
    return [int(i) for i in code_string.split('.')]


def analise_all(csv_file='../data/receitas_min.csv', lines_per_insert=100):
    data = pd.read_csv(csv_file, encoding='utf8')

    cache = {}
    codes = {}
    replicated_lines = {}

    for row_i, row in data.iterrows():
        print(row_i)

        r = {}

        code = row['codigo']
        date = row['data']
        r['original_code'] = row['codigo']
        try:
            r['description'] = unicode(row['descricao']).encode('utf8')
        except:
            r['description'] = unicode(row[u'Descrição_Sub_Alínea_Código']).encode('utf8')
            
        r['date'] = parse_date(row['data'])
        r['monthly_outcome'] = parse_money(row['realizado_mensal'])
        r['monthly_predicted'] = parse_money(row['previsto_mensal'])

        # Check line replication
        if (date, code) not in cache:
            cache[(date, code)] = r
        else:
            lista = replicated_lines.get((date, code))
            if not lista:
                lista = [cache[(date, code)]]
            lista.append(r)
            replicated_lines[(date, code)] = lista

        # Check code replication
        descrips = codes.get(code, set())
        descrips.add(r['description'])
        codes[code] = descrips

    # Store replicated lines
    w = csv.DictWriter(open("lines_replicated.csv", 'wb'),
                       ['original_code', 'description', 'date',
                        'monthly_predicted', 'monthly_outcome'])
    w.writeheader()
    for k, l in replicated_lines.items():
        for i in l:
            w.writerow(i)

    # Store replicated codes
    w = csv.writer(open("codes_replicated.csv", 'wb'))
    w.writerow(["codigo", "descricao"])
    for k, l in codes.items():
        if len(l) > 1:
            orde = sorted(list(l))
            # restantes = []
            if len(orde) == 2:
                if orde[1].find(orde[0]) != -1:
                    continue
            for i in orde:
                w.writerow([k, i])
            w.writerow(["", ""])
            #     if orde[-1].find(i) == -1:
            #         restantes.append(i)
            # if len(restantes) > 1:
            #     for i in restantes:
            #         w.writerow([k, i])

if __name__ == '__main__':
    arguments = docopt(__doc__)
    args = {}
    csv_file = arguments['FILE']
    if csv_file:
        args['csv_file'] = csv_file
    analise_all(**args)
