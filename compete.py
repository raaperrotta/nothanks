import nothanks
import pandas as pd
from random import sample  # use choices for sampling with replacement
import threshold


# The contenders
strategies = [threshold.Player(n) for n in [5, 8, 11, 14, 17]]

game_sizes = [2, 3]

# A dictionary of scores
results = {}
for num_players in game_sizes:
    results[num_players] = {}
    for strategy in strategies:
        results[num_players][strategy] = 0

for num_players in game_sizes:
    for n in range(1000):

        selected_strategies = sample(strategies, num_players)
        winners, scores = nothanks.Game(selected_strategies).run()

        for strategy in selected_strategies:
            results[num_players][strategy] -= 60 // num_players
        for winner in winners:
            results[num_players][winner] += 60 // len(winners)

results = pd.DataFrame(results)
results['combined'] = results.sum(axis=1)
results.loc['total', :] = results.sum(axis=0)
print(results)
