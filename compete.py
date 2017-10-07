import nothanks
import pandas as pd
from random import choices
import threshold


# The contenders
strategies = {}
for n in range(1, 6):
    strategies['threshold_{:02d}'.format(n)] = threshold.Player(n)

game_sizes = [2, 3]

# A dictionary of scores
results = {}
for num_players in game_sizes:
    results[num_players] = {}
    for strategy in strategies:
        results[num_players][strategy] = 0

for num_players in game_sizes:
    for n in range(1000):

        competitors = choices(list(strategies.keys()), k=num_players)

        players = [nothanks.Player(x, strategies[x]) for x in competitors]
        game = nothanks.Game(players, starting_tokens=3,
                             low_card=2, high_card=7, discard=2)
        winners, scores = game.run()

        for strategy in competitors:
            results[num_players][strategy] -= 60 // num_players
        for winner in winners:
            results[num_players][winner.strategy_name] += 60 // len(winners)

results = pd.DataFrame(results)
results['combined'] = results.sum(axis=1)
results.loc['total', :] = results.sum(axis=0)
print(results)
