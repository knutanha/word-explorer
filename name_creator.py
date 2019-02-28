import pandas as pd
import random


def generate_names(n: int = None) -> tuple:
    # TODO: Use probability

    """
        F female
        1F female if first part of name, otherwise mostly male
        ?F mostly female
        M male
        1M male if first part of name, otherwise mostly female
        ?M mostly male
        ? unisex
    """

    first_names = pd.read_csv(
        'resources/firstnames.csv',
        sep=';',
        usecols=[
            'name',
            'gender',
            'Great Britain',
            'Ireland',
            'U.S.A.',
            'Germany',
            'Denmark',
            'Norway',
            'Sweden'
        ],
        dtype=str
    ).dropna('rows', how='all')

    surnames = pd.read_csv(
        'resources/surnames.csv',
        sep=',',
        dtype=str
    )

    female_names = first_names[first_names['gender'].isin(['F', '?F', '1M', '?'])]
    male_names = first_names[first_names['gender'].isin(['M', '?M', '1F', '?'])]
    while n is None or n > 0:
        gender = random.choice(('F', 'M'))
        first_name_sample, first_name_values, first_name, surname = None, None, None, None
        try:
            first_name_sample = (female_names if gender == 'F' else male_names).sample()
            first_name_values = first_name_sample.name.values
            first_name = first_name_values[0]
            surname = surnames.sample().name.values[0]
            yield (
                str.capitalize(first_name.replace('+', ' ')),
                str.capitalize(surname.replace('+', ' ')),
                gender
            )
        except AttributeError as e:
            print('[generate_names] ERROR:', e)
            # print('[generate_names] ERROR: first_name_sample =', first_name_sample)
            print('[generate_names] ERROR: first_name_values =', first_name_values)
            print('[generate_names] ERROR: first_name =', first_name)
            print('[generate_names] ERROR: surname =', surname)
        if n:
            n -= 1


if __name__ == '__main__':
    print(list(generate_names(10)))
