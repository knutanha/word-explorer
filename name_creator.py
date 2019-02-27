import pandas as pd
import random


def generate_names(n: int = 1) -> tuple:
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
        ]
    ).dropna('rows', how='all')

    surnames = pd.read_csv(
        'resources/surnames.csv',
        sep=',',
    )

    female_names = first_names[first_names['gender'].isin(['F', '?F', '1M', '?'])]
    male_names = first_names[first_names['gender'].isin(['M', '?M', '1F', '?'])]
    for _ in range(n):
        gender = random.choice(('F', 'M'))
        yield (
            str.capitalize((female_names if gender == 'F' else male_names).sample().name.values[0].replace('+', ' ')),
            str.capitalize(surnames.sample().name.values[0].replace('+', ' ')),
            gender
        )

print(list(generate_names(10)))