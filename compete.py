import nothanks
import always_pass, always_take, coin_toss
from random import choices
import pandas as pd


# The contenders
strategies = ['always_pass', 'always_take', 'coin_toss']

game_sizes = [3, 4, 5]

# A dictionary of scores
results = {}
for num_players in game_sizes:
    results[num_players] = {}
    for strategy in strategies:
        results[num_players][strategy] = 0.0


for num_players in game_sizes:
    for n in range(100):

        competitors = choices(strategies, k=num_players)

        players = [nothanks.Player(x) for x in competitors]
        game = nothanks.Game(players)
        winners, scores = game.run()

        for strategy in strategies:
            results[num_players][strategy] -= 1/num_players
        for winner in winners:
            results[num_players][winner.strategy_name] += 1/len(winners)

print(pd.DataFrame(results))
