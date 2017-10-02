import nothanks
import pandas as pd
from random import choices


# The contenders
strategies = ['coin_toss', 'threshold']

game_sizes = [3, 4, 5]

# A dictionary of scores
results = {}
for num_players in game_sizes:
    results[num_players] = {}
    for strategy in strategies:
        results[num_players][strategy] = 0

for num_players in game_sizes:
    for n in range(100):

        competitors = choices(strategies, k=num_players)

        players = [nothanks.Player(x) for x in competitors]
        game = nothanks.Game(players)
        winners, scores = game.run()

        for strategy in competitors:
            results[num_players][strategy] -= 60 // num_players
        for winner in winners:
            results[num_players][winner.strategy_name] += 60 // len(winners)

results = pd.DataFrame(results)
results['combined'] = results.sum(axis=1)
results.loc['total', :] = results.sum(axis=0)
print(results)
