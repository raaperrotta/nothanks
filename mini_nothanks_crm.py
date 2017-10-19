"""In Progress!"""
from collections import defaultdict
from copy import deepcopy
import logging
import networkx as nx
import pandas as pd
from progress.bar import ChargingBar as ProgressBar
from random import random, shuffle
from sortedcontainers import SortedSet
import sys
from time import time

import nothanks

logger = logging.getLogger(__name__)


class player_state():
    """Define a class for tracking the cards and coins each player has."""

    def __init__(self, starting_coins):
        """Create object with no cards and starting coins."""
        self.cards = SortedSet()
        self.coins = starting_coins

    def prehash(self):
        """Convert to tuple to support hashing."""
        return tuple(self.cards), self.coins

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


class game_state():
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
        self.players = [player_state(starting_coins)
                        for _ in range(num_players)]

    def prehash(self):
        """Convert to tuple to support hashing."""
        return (self.card_in_play, self.pot, *(p.prehash() for p in self.players))

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
        self.players = [player_state(self.starting_coins)
                        for _ in range(self.num_players)]

    def possible_next_cards(self):
        """Return list of cards not already delt."""
        already_delt = SortedSet
        if self.card_in_play:
            already_delt.add(self.card_in_play)
        for player in self.players:
            already_delt = already_delt.union(player.cards)
        return [card for card in range(self.low_card, self.high_card + 1)
                if card not in already_delt]

    def get_results(self):
        scores = [p.score() for p in self.players]
        winning_score = min(scores)
        won = [s == winning_score for s in scores]
        num_winners = sum(won)
        lose_pays = -1 / len(self.players)
        win_pays = 1/num_winners + lose_pays
        payoffs = [win_pays if w else lose_pays for w in won]
        return scores, payoffs


class game_tree():
    """Define a class for drawing a complete No Thanks game tree."""

    def __init__(self, num_players=2, starting_coins=1,
                 low_card=1, high_card=3, discard=1):
        self.num_players = num_players
        self.starting_coins = starting_coins
        self.low_card = low_card
        self.high_card = high_card
        self.discard = discard

        self.tree = nx.DiGraph()
        state = game_state(num_players=num_players,
                           starting_coins=starting_coins,
                           low_card=low_card, high_card=high_card,
                           discard=discard)
        self.tree.add_node(state.prehash(), state=state)
        # Start the game by dealing a card
        self.deal_card(state)

    def add_edge(self, start, end, weight):
        """Add this edge to the game tree."""
        end_prehash = end.prehash()
        self.tree.add_edge(start.prehash(), end_prehash,
                           weight=weight, avg_weight=0)
        # Add state object to node with corresponding prehash
        self.tree.nodes[end_prehash]['state'] = end

    def deal_card(self, state):
        """Add tree edges for possible next cards, then continue game."""
        possible_cards = state.possible_next_cards()
        if len(possible_cards) > self.discard:  # otherwise the game is over
            prob = 1/len(possible_cards)
            for card in possible_cards:
                new_state = deepcopy(state)
                new_state.deal(card)
                self.add_edge(state, new_state, weight=prob)
                self.take_turn(new_state)
        else:
            score, payoff = state.get_results()
            self.tree.nodes[state.prehash()]['score'] = score
            self.tree.nodes[state.prehash()]['payoff'] = payoff

    def take_turn(self, state):
        """Add edges for possible player choices, then continue game."""
        can_pass = state.players[0].coins > 0
        node = self.tree.nodes[state.prehash()]
        node['can_pass'] = can_pass

        prob_take = 1/2 if can_pass else 1
        new_state = deepcopy(state)
        new_state.take()
        self.add_edge(state, new_state, prob_take)
        # After taking a card, deal a new one.
        self.deal_card(new_state)

        if can_pass:
            # Since the player has an choice to make, we initialize some fields
            # that will be used to track the startegy learning.
            node['visits'] = 0
            node['regret'] = [0, 0]  # pass, take
            
            new_state = deepcopy(state)
            new_state.pass_turn()
            self.add_edge(state, new_state, 1/2)
            # After passing the turn, next player takes turn.
            self.take_turn(new_state)

    def get_edge_weight(self, start, end):
        """Return weight of associated edge."""
        return self.tree.edges[(start.prehash(), end.prehash())]['weight']

    def get_expected_payoff_take(self, state):
        """Return the expected payoff if player takes in this state."""
        take_state = deepcopy(state)
        take_state.take()
        payoffs = self.get_expected_payoffs(take_state)
        return payoffs[0]  # player is still in first spot after a take

    def get_expected_payoff_pass(self, state):
        """Return the expected payoff if player takes in this state."""
        pass_state = deepcopy(state)
        pass_state.pass_turn()
        payoffs = self.get_expected_payoffs(pass_state)
        return payoffs[-1]  # player is now in last spot after a pass

    def get_expected_payoffs(self, state):
        """Return expected payoffs for each possible action."""
        state_hash = state.prehash()
        successors = list(self.tree.successors(state_hash))
        if successors:
            payoffs = [0] * len(state.players)
            total_prob = 0
            for next_state_hash in successors:
                next_state = self.tree.nodes[next_state_hash]['state']
                prob = self.tree.edges[(state_hash, next_state_hash)]['weight']
                total_prob += prob
                sub_payoffs = self.get_expected_payoffs(next_state)
                # If current card has not changed then players rotated.
                # We need to rotate payoffs backwards to compensate.
                if state.card_in_play == next_state.card_in_play:
                    # pop off last element and instert in front.
                    sub_payoffs.insert(0, sub_payoffs.pop())

                payoffs = [cum + prob * sub for cum, sub
                           in zip(payoffs, sub_payoffs)]
            assert abs(total_prob - 1) < 1e-6, 'Total probability was not 1! (was {})'.format(total_prob)
        else:
            # The game always ends with a player taking a card so no need to
            # check for player rotation.
            payoffs = self.tree.nodes[state_hash]['payoff']
        return payoffs

    def train(self, num_games, print_progress=True):
        # Create a set of identical players, each referencing this game tree
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
        for _ in iterable:
            winners, _ = nothanks.Game(players,
                                       starting_coins=self.starting_coins,
                                       low_card=self.low_card,
                                       high_card=self.high_card,
                                       discard=self.discard).run()
            # Update the shared game tree based on game results.
            for player in players:
                payoff = -1 / self.num_players
                if id(player) in winners:
                    payoff += 1 / len(winners)
                for state_hash, action in player.history.items():
                    node = self.tree.nodes[state_hash]
                    state = node['state']
                    # If the player has no coins, there is no decision to make.
                    if not node['can_pass']:
                        continue
                    # If the expected return from the alternate decision is
                    # higher than the return from this game, the player regrets
                    # not having chosen the alternate decision.
                    take_state = deepcopy(state)
                    take_state.take()
                    take_edge = self.tree.edges[(state_hash, take_state.prehash())]
                    pass_state = deepcopy(state)
                    pass_state.pass_turn()
                    pass_edge = self.tree.edges[(state_hash, pass_state.prehash())]
                    if action:  # took card and pot when in this state
                        alternate = pass_state
                        alt_payoff = self.get_expected_payoff_pass(state)
                    else:  # passed when in this state
                        alternate = take_state
                        alt_payoff = self.get_expected_payoff_take(state)
                    regret = alt_payoff - payoff
                    # If we have never seen this state before, assign defaults.
                    if node['visits'] == 0:
                        logger.debug('LOG: State {} was visited for the first time this game.'.format(state_hash))
                    # Then update node and edge values
                    node['visits'] += 1 
                    # Add new regret for the action we DIDN'T take
                    node['regret'][not action] += regret
                    # Update strategy based on new cumulative regret
                    effective_regret = [max(0, r) for r in node['regret']]
                    total_regret = sum(effective_regret)
                    if total_regret == 0:
                        take_edge['weight'] = 1/2
                        pass_edge['weight'] = 1/2
                    else:
                        take_edge['weight'] = effective_regret[True] / total_regret
                        pass_edge['weight'] = effective_regret[False] / total_regret
                    # Adjust running average strategy
                    take_edge['avg_weight'] *= (node['visits'] - 1) / node['visits']
                    take_edge['avg_weight'] += take_edge['weight'] / node['visits']
                    pass_edge['avg_weight'] *= (node['visits'] - 1) / node['visits']
                    pass_edge['avg_weight'] += pass_edge['weight'] / node['visits']

    def reduce(self):
        """Return a dictionary of player action states and corresponding strategies."""
        output = {}
        for state_hash, node in self.tree.nodes.items():
            state = node['state']
            if state.card_in_play is None:
                continue
            if not node['can_pass']:
                continue
            take_state = deepcopy(state)
            take_state.take()
            take_edge = self.tree.edges[(state_hash, take_state.prehash())]
            weight = take_edge['weight']
            output[state_hash] = {}
            output[state_hash]['visits'] = node['visits']
            output[state_hash]['regret'] = node['regret']
            output[state_hash]['weight'] = take_edge['weight']
            output[state_hash]['avg_weight'] = take_edge['avg_weight']
        return output


class Player(nothanks.Player):
    
    def __init__(self, tree, num_players=2, starting_coins=1,
                 low_card=1, high_card=3, discard=1):
        self.tree = tree
        self.state = game_state(num_players=num_players,
                                starting_coins=starting_coins,
                                low_card=low_card, high_card=high_card,
                                discard=discard)
        self.history = {}

    def play(self, card, pot):
        """Take card according to strategy in game tree."""
        # If last action was take, card_in_play was set to None
        # and this is our first look at the next card.
        if self.state.card_in_play is None:
            self.state.deal(card)
        take_state = deepcopy(self.state)
        take_state.take()
        prob_take = self.tree.get_edge_weight(self.state, take_state)
        take = random() < prob_take
        self.history[self.state.prehash()] = take
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
        self.history = {}

    def __str__(self):
        return '<CRM player at {}>'.format(id(self))


def main():
    logger = logging.getLogger(__name__)
    logger.setLevel(level=logging.DEBUG)
    logger.addHandler(logging.StreamHandler(sys.stdout))
    nothanks_log = logging.getLogger('nothanks')
    nothanks_log.setLevel(level=logging.DEBUG)
    nothanks_log.addHandler(logging.StreamHandler(sys.stdout))

    tree = game_tree(num_players=2, starting_coins=2,
                     low_card=1, high_card=4, discard=1)
    tree.train(10, print_progress=False)

    logger.setLevel(level=logging.WARNING)
    nothanks_log.setLevel(level=logging.WARNING)

    start = time()
    tree.train(10000)
    elapsed = time() - start

    # Pandas DataFrame print options
    pd.set_option('display.width', 9999)
    pd.set_option('display.max_rows', 9999)
    print(pd.DataFrame(tree.reduce()).transpose())
    print('Took {} seconds.'.format(elapsed))


if __name__ == "__main__":
    main()
