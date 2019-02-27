import pandas as pd


def read_csv(csv_file_path: str, sep: str = ','):
    """
    output = collections.defaultdict(list)
    with open(csv_file_path, 'r', encoding='utf-8') as f:
        content = [i.split(sep) for i in f.read().splitlines()]
        first_row = content[0]
        row_len = len(first_row)
        if has_headers:
            headers = first_row
        else:
            headers = list(range(row_len))

        for row_index in range(1 if has_headers else 0, len(content)):
            for col_index in range(row_len):
                output[headers[col_index]].append(content[row_index][col_index])

        return output
    """
    return pd.read_csv(csv_file_path, sep, header=0)


if __name__ == '__main__':
    a = read_csv(r'C:\Dev\Python\word-explorer\word-explorer\resources\firstnames.csv', sep=';')

    a.dropna('rows', how='all', inplace=True, subset=[
        'Great Britain',
        'Ireland',
        'U.S.A.',
        'Germany',
        'Denmark',
        'Norway',
        'Sweden',
    ])
    print(a['name'])
