import json
import os
from datetime import datetime

DIRECTORY = 'database/winner'


def save(winner):
    winner['date'] = winner['date'].strftime('%Y-%m-%d')
    date = winner['date']
    filename = f'{DIRECTORY}/{date}.json'
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'x') as fp:
        json.dump(winner, fp)


def find_all():
    winners = []
    for filename in os.listdir(DIRECTORY):
        with open(os.path.join(DIRECTORY, filename), 'r') as f:
            winner = map_file_to_winner(f)
            winners.append(winner)

    return winners


def map_file_to_winner(f):
    winner = json.load(f)
    winner['date'] = datetime.strptime(winner['date'], '%Y-%m-%d')
    return winner
