"""Define the No Thanks multi-game competition."""

from importlib import import_module
from random import choices  # use sample for sampling without replacement
from progress.bar import ChargingBar as ProgressBar
from time import time

import logging
import sys

import pandas as pd

import nothanks


def compete(strategies, num_rounds=1000):
    """Create and run No Thanks competition."""

    # Play 3, 4, and 5 player games
    game_sizes = [3, 4, 5]

    # A dictionary of scores
    results = {}
    for num_players in game_sizes:
        results[num_players] = {}
        for strategy in strategies:
            results[num_players][strategy] = 0

    for num_players in game_sizes:
        for _ in ProgressBar('Playing {}-player games'.format(num_players)).iter(range(num_rounds)):
            selected_strategies = choices(strategies, k=num_players)
            players = [import_module(s).Player() for s in selected_strategies]
            winners, _ = nothanks.Game(players).run()

            for strategy, player in zip(selected_strategies, players):
                results[num_players][strategy] -= 1 / num_players / num_rounds
                if id(player) in winners:
                    results[num_players][strategy] += 1 / len(winners) / num_rounds

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

    start = time()
    results = compete(strategies)
    elapsed = time() - start

    print(results)
    print('Ran in {:.2f} seconds'.format(elapsed))


if __name__ == "__main__":
    # Define a function for main to avoid variable scope confusion
    # (and associated pylint warnings)
    main()
