import nothanks
import crm
import sequence_crm
import sequence_threshold

from copy import deepcopy
import logging
import matplotlib.pyplot as plt
import pandas as pd
import pickle
from progress.bar import ChargingBar
import os
import sys

logger = logging.getLogger('crm')
logger.setLevel(level=logging.WARNING)
logger.addHandler(logging.StreamHandler(sys.stdout))
nothanks_log = logging.getLogger('nothanks')
nothanks_log.setLevel(level=logging.WARNING)
nothanks_log.addHandler(logging.StreamHandler(sys.stdout))

def compete_against_naive(trained, naive, num_games=100):
    # Compare competition results between naive players and a trained player
    strategies = [trained] + [naive] * (naive.num_players - 1)
    wins = 0
    for _ in range(num_games):
        players = [crm.Player(s, use_avg=True, num_players=s.num_players,
                              starting_coins=s.starting_coins,
                              low_card=s.low_card,
                              high_card=s.high_card,
                              discard=s.discard)
                   for s in strategies]
        winners, _ = nothanks.Game(players,
                                   starting_coins=naive.starting_coins,
                                   low_card=naive.low_card,
                                   high_card=naive.high_card,
                                   discard=naive.discard).run()
        if id(players[0]) in winners:
            wins += 1 / len(winners)  # ties count as fractional wins
    return wins / num_games

def compete_against_threshold(trained, num_games=100):
    # Compare competition results between naive players and a trained player
    wins = 0
    for _ in range(num_games):
        players = [crm.Player(trained, use_avg=True,
                              num_players=trained.num_players,
                              starting_coins=trained.starting_coins,
                              low_card=trained.low_card,
                              high_card=trained.high_card,
                              discard=trained.discard)]
        players += [sequence_threshold.Player()
                    for _ in range(trained.num_players - 1)]
        winners, _ = nothanks.Game(players,
                                   starting_coins=trained.starting_coins,
                                   low_card=trained.low_card,
                                   high_card=trained.high_card,
                                   discard=trained.discard).run()
        if id(players[0]) in winners:
            wins += 1 / len(winners)  # ties count as fractional wins
    return wins / num_games

class TrainingBar(ChargingBar):
    message = 'Training'
    suffix = '%(percent)d%% (%(elapsed_td)s/%(eta_td)s) (p_win: %(win_fraction)f, n_states: %(num_states)d)'
    def __init__(self):
        self.win_fraction = 0
        self.num_states = 0
        super().__init__()

trained = sequence_crm.Strategy(num_players=3, starting_coins=11,
                                low_card=3, high_card=35, discard=9)

results = {}
length = {}
progressbar = TrainingBar()
prev = 0  # before loop, strategy has been trained over zero rounds
for num_rounds in progressbar.iter(range(0, 501, 1)):
    trained.train(num_rounds - prev, print_progress=False)  # train up to current value
    results[num_rounds] = compete_against_threshold(trained, num_games=1000)
    length[num_rounds] = len([state for state, info in trained.data.items() if info['visits'] > 0])
    progressbar.win_fraction = results[num_rounds]
    progressbar.num_states = length[num_rounds]
    prev = num_rounds  # store rounds trained so far

filename = 'trained_crm.pickle'
suffix = 0
while os.path.exists(filename):
    suffix += 1
    filename = 'trained_crm_{}.pickle'.format(suffix)

pickle.dump(trained, open(filename, 'wb'))

pd.set_option('display.width', 9999)
pd.set_option('display.max_rows', 9999)
print(pd.DataFrame(trained.data).transpose())

fig, axs = plt.subplots(2, sharex=True)

axs[0].plot(list(results.keys()), results.values(), '.')
# axs[0].set_xscale('log')
axs[0].set_ylabel('Fraction won')

axs[1].plot(list(length.keys()), length.values(), '.')
# axs[1].set_xscale('log')
axs[1].set_ylabel('States trained (visits > 0)')

plt.show()
