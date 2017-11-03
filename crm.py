"""Define the base class for counterfactual regret minimizing players."""
from collections import defaultdict
import pickle
import logging
import networkx as nx
import pandas as pd
from progress.bar import ChargingBar as ProgressBar
from random import random, shuffle
import sys
from time import time

import nothanks

logger = logging.getLogger(__name__)

class PlayerState():
    """Define a class for tracking the cards and coins each player has."""

    def __init__(self, starting_coins):
        """Create object with no cards and starting coins."""
        self.cards = set()
        self.coins = starting_coins

    def copy(self):
        new_state = PlayerState(self.coins)
        new_state.cards = self.cards.copy()
        return new_state

    def take(self, card, pot):
        """Add card and coins to collection."""
        assert card not in self.cards
        self.cards.add(card)
        self.coins += pot

    def pass_turn(self):
        assert self.coins > 0, "Player can't pass because he has no coins!"
        self.coins -= 1

    def score(self):
        score = -self.coins
        prev = None
        for card in self.cards:
            if prev is None or card - prev > 1:
                score += card
            prev = card
        return score


class GameState():
    """Define a class for tracking the state of the No Thanks game."""

    def __init__(self, num_players, starting_coins,
                 low_card, high_card, discard):
        """Start with no card in play and an empty pot."""
        self.num_players = num_players
        self.starting_coins = starting_coins
        self.low_card = low_card
        self.high_card = high_card
        self.discard = discard

        self.card_in_play = None
        self.pot = 0
        self.players = [PlayerState(starting_coins)
                        for _ in range(num_players)]

    def copy(self):
        new_state = GameState(num_players=self.num_players,
                              starting_coins=self.starting_coins,
                              low_card=self.low_card,
                              high_card=self.high_card,
                              discard=self.discard)
        new_state.players = [p.copy() for p in self.players]
        new_state.pot = self.pot
        new_state.card_in_play = self.card_in_play
        return new_state

    def deal(self, card):
        """Put a card into play"""
        assert self.card_in_play is None, 'Cannot deal a new card; one is already in play!'
        assert self.pot == 0, 'Cannot deal a new card; pot should be zero!'
        self.card_in_play = card

    def take(self):
        """Give card and pot to current player."""
        self.players[0].take(self.card_in_play, self.pot)
        self.card_in_play = None
        self.pot = 0

    def pass_turn(self):
        """Take coin and pass turn to next player."""
        self.players[0].pass_turn()
        self.pot += 1
        # Move first player to back of list
        self.players.append(self.players.pop(0))

    def reset(self):
        self.card_in_play = None
        self.pot = 0
        self.players = [PlayerState(self.starting_coins)
                        for _ in range(self.num_players)]

    def possible_next_cards(self):
        """Return list of cards not already delt."""
        already_delt = set()
        if self.card_in_play:
            already_delt.add(self.card_in_play)
        for player in self.players:
            already_delt = already_delt.union(player.cards)
        return [card for card in range(self.low_card, self.high_card + 1)
                if card not in already_delt]


class Strategy():
    """Define a class for drawing a complete No Thanks game tree."""

    def __init__(self, num_players=2, starting_coins=1,
                 low_card=1, high_card=3, discard=1):
        self.num_players = num_players
        self.starting_coins = starting_coins
        self.low_card = low_card
        self.high_card = high_card
        self.discard = discard

        self.data = defaultdict(self.default)

    def default(self):
        return {'visits': 0, 'regret': [0, 0],
                'strategy': 0.5, 'average_strategy': 0.5}

    def prehash(self, state):
        """Reduce the game state to a hashable, abstract representation."""
        # This base class does not abstract the game state and is therefore not
        # playable in a full size game of No Thanks.
        return (state.card_in_play, state.pot,
                *((tuple(p.cards), p.coins) for p in state.players))

    def get_prob_take(self, state, use_average):
        """Return the mixed-strategy probability of taking."""
        key = 'average_strategy' if use_average else 'strategy'
        state_hash = self.prehash(state)
        return self.data[state_hash][key]

    def run_partial_game(self, state):
        """Set up a mid-play game of No Thanks."""
        players = [Player(self.data, num_players=self.num_players,
                            starting_coins=self.starting_coins,
                            low_card=self.low_card,
                            high_card=self.high_card,
                            discard=self.discard)
                    for _ in range(self.num_players)]
        # Set each player state to current game state
        for idx, player in enumerate(players):
            player.state = state.copy()
        # Create a fresh No Thanks game with these players
        game = nothanks.Game(players,
                             starting_coins=self.starting_coins,
                             low_card=self.low_card,
                             high_card=self.high_card,
                             discard=self.discard)
        # Update internal game state to match
        game.card = state.card_in_play
        game.pot = state.pot
        for player, info in zip(players, state.players):
            game.state[id(player)] = {'cards': info.cards, 'coins':info.coins}
        game.deck = state.possible_next_cards()
        shuffle(game.deck)
        # Let game proceed from this point until it is done
        game.play()
        winners, _ = game.get_results()
        payoff = -1 / self.num_players  # the ante
        if id(players[0]) in winners:
            payoff += 1 / len(winners)
        return payoff

    def get_expected_payoff(self, state, action, num_iter=1000):
        """Return expected payoff for a possible action."""
        new_state = state.copy()
        if action:
            new_state.take()
        else:
            new_state.pass_turn()
        payoff = 0
        for _ in range(num_iter):
            # Create a new game and set it up in the current state
            payoff += self.run_partial_game(new_state)
        return payoff / num_iter

    def train(self, num_games, print_progress=True):
        # Create a set of identical players, each referencing this game tree
        logger.debug('Creating {} players with which to train this CRM strategy.'.format(self.num_players))
        players = [Player(self, num_players=self.num_players,
                          starting_coins=self.starting_coins,
                          low_card=self.low_card,
                          high_card=self.high_card,
                          discard=self.discard)
                   for _ in range(self.num_players)]
        # Simulate self-play
        if print_progress:
            iterable = ProgressBar('Training').iter(range(num_games))
        else:
            iterable = range(num_games)
        for idx in iterable:
            logger.debug('Playing training match {} of {}'.format(idx, num_games))
            winners, _ = nothanks.Game(players,
                                       starting_coins=self.starting_coins,
                                       low_card=self.low_card,
                                       high_card=self.high_card,
                                       discard=self.discard).run()
            # Update all regrets, but not strategies so as not to affect simulated games
            for player in players:
                payoff = -1 / self.num_players
                if id(player) in winners:
                    payoff += 1 / len(winners)
                for state, action in player.history:
                    state_hash = self.prehash(state)
                    state_info = self.data[state_hash]
                    # If the player has no coins, there is no decision to make.
                    if state.players[0].coins == 0:
                        continue
                    # If the expected return from the alternate decision is
                    # higher than the return from this game, the player regrets
                    # not having chosen the alternate decision.
                    alt_payoff = self.get_expected_payoff(state, not action)
                    regret = alt_payoff - payoff
                    # If we have never seen this state before, log it.
                    if state_info['visits'] == 0:
                        logger.debug('LOG: State {} was visited for the first time this game.'.format(state_hash))
                    else:
                        logger.debug('LOG: State {} has been visited {} times including this one.'.format(state_hash, state_info['visits']+1))
                    # Then update node and edge values
                    state_info['visits'] += 1 
                    # Add new regret for the action we DIDN'T take
                    logger.debug('Adding {} regret points for a total of {}.'.format(regret, state_info['regret'][not action] + regret))
                    state_info['regret'][not action] += regret

            # Now update strategies
            for player in players:
                for state, _ in player.history:
                    state_hash = self.prehash(state)
                    state_info = self.data[state_hash]
                    # Update strategy based on new cumulative regret
                    effective_regret = [max(0, r) for r in state_info['regret']]
                    total_regret = sum(effective_regret)
                    if total_regret == 0:
                        state_info['strategy'] = 1/2
                    else:
                        state_info['strategy'] = effective_regret[True] / total_regret
                    # Adjust running average strategy
                    state_info['average_strategy'] *= (state_info['visits'] - 1) / state_info['visits']
                    state_info['average_strategy'] += state_info['strategy'] / state_info['visits']

    def reduce(self, use_average=False):
        """Return a defaultdict of game states and corresponding data."""
        if use_average:
            key = 'average_strategy'
        else:
            key = 'strategy'
        # Use defaultdict so states not reached during training are playable
        output = {} # defaultdict(lambda: 0.5)
        logger.warning('Reducing strategy data into strategy with {} states.'.format(len(self.data)))
        for state_hash, info in self.data.items():
            output[state_hash] = info[key]
        return output

class Player(nothanks.Player):
    
    def __init__(self, strategy, use_avg=False, num_players=2, starting_coins=1,
                 low_card=1, high_card=3, discard=1):
        self.strategy = strategy
        self.use_avg = use_avg
        self.state = GameState(num_players=num_players,
                                starting_coins=starting_coins,
                                low_card=low_card, high_card=high_card,
                                discard=discard)
        self.history = []

    def play(self, card, pot):
        """Take card according to strategy."""
        # If last action was take, card_in_play was set to None
        # and this is our first look at the next card.
        if self.state.card_in_play is None:
            self.state.deal(card)
        prob_take = self.strategy.get_prob_take(self.state, self.use_avg)
        take = random() < prob_take
        self.history.append((self.state.copy(), take))
        return take

    def update(self, player_id, card, pot, action):
        """Update game state."""
        # If last action was take, card_in_play was set to None
        # and this is our first look at the next card.
        if self.state.card_in_play is None:
            self.state.deal(card)
        assert self.state.card_in_play == card, 'Expected card {} but got {}!'.format(self.state.card_in_play, card)
        assert self.state.pot == pot, 'Expected pot size {} but got {}!'.format(self.state.pot, pot)
        if action:
            self.state.take()
        else:
            self.state.pass_turn()

    def prepare_for_new_game(self, _):
        """Reset game state."""
        self.state.reset()
        self.history = []

    def __str__(self):
        return '<CRM player at {}>'.format(id(self))


def main():
    logger = logging.getLogger(__name__)
    logger.setLevel(level=logging.DEBUG)
    logger.addHandler(logging.StreamHandler(sys.stdout))
    nothanks_log = logging.getLogger('nothanks')
    nothanks_log.setLevel(level=logging.DEBUG)
    nothanks_log.addHandler(logging.StreamHandler(sys.stdout))

    naive = Strategy(num_players=2, starting_coins=2,
                     low_card=1, high_card=3, discard=1)
    trained = Strategy(num_players=2, starting_coins=2,
                       low_card=1, high_card=3, discard=1)
    trained.train(2, print_progress=False)

    logger.setLevel(level=logging.WARNING)
    nothanks_log.setLevel(level=logging.WARNING)

    start = time()
    trained.train(100)
    elapsed = time() - start

    # Pandas DataFrame print options
    pd.set_option('display.width', 9999)
    pd.set_option('display.max_rows', 9999)
    print(pd.DataFrame(trained.data).transpose())
    print('Took {} seconds.'.format(elapsed))


if __name__ == "__main__":
    main()
