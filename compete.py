"""Define the No Thanks multi-game competition."""

from importlib import import_module
from random import sample  # use choices for sampling with replacement
from progress.bar import ChargingBar as ProgressBar
from time import time

import logging
import sys

import pandas as pd

import nothanks


def compete(players, num_rounds=1000):
    """Create and run No Thanks competition."""
    assert len(players) >= 3, ("Need at least 3 players to play No Thanks! ",
                               "(only have {})".format(len(players)))
    # Play 3, 4, and 5 player games if there are enough players
    game_sizes = list(range(3, min([6, 1 + len(players)])))

    # A dictionary of scores
    results = {}
    for num_players in game_sizes:
        results[num_players] = {}
        for player in players:
            results[num_players][id(player)] = 0

    for num_players in game_sizes:
        for _ in ProgressBar('Competing').iter(range(num_rounds)):

            selected_players = sample(players, num_players)
            winners, _ = nothanks.Game(selected_players).run()

            for player in selected_players:
                results[num_players][id(player)] -= 1 / num_players / num_rounds
            for winner in winners:
                results[num_players][winner] += 1 / len(winners) / num_rounds

    results = pd.DataFrame(results)
    results['combined'] = results.sum(axis=1)
    results.loc['total', :] = results.sum(axis=0)
    return results


def main():
    """Select strategies for No Thanks competition, run, and print results."""
    strategies = ['nothanks', 'threshold', 'sequence_threshold']

    # Set logging behavior for No Thanks modules
    for name in ['nothanks'] + strategies:
        logger = logging.getLogger(name)
        logger.setLevel(level=logging.WARNING)  # use DEBUG to see verbose output
        logger.addHandler(logging.StreamHandler(sys.stdout))
        
    players = []
    names = {}
    for strategy in strategies:
        new_player = import_module(strategy).Player()
        players.append(new_player)
        names[id(new_player)] = strategy

    start = time()
    results = compete(players).rename(names)
    elapsed = time() - start

    print(results)
    print('Ran in {:.2f} seconds'.format(elapsed))


if __name__ == "__main__":
    # Define a function for main to avoid variable scope confusion
    # (and associated pylint warnings)
    main()
