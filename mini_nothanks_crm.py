"""In Progress!"""
import networkx as nx
from random import shuffle
from sortedcontainers import SortedSet


class player_state():
    """Define a class for tracking the cards and coins each player has."""

    def __init__(self, starting_coins=1):
        """Create object with no cards and starting coins."""
        self.cards = SortedSet()
        self.coins = starting_coins

    def prehash(self):
        """Convert to tuple to support hashing."""
        return tuple(self.cards), self.pot

    def take(self, card, pot):
        """Add card and coins to collection."""
        assert card not in self.cards
        self.cards.add(card)
        self.pot += pot

    def pass(self):
        assert self.coins > 0, "Player can't pass because he has no coins!"
        self.coins -= 1



class game_state():
    """Define a class for tracking the state of the No Thanks game."""

    def __init__(self, num_players=2, starting_coins=1):
        """Start with no card in play and an empty pot."""
        self.card_in_play = None
        self.pot = 0
        self.players = [player_state(starting_coins)
                        for _ in range(num_players)]

    def prehash(self):
        """Convert to tuple to support hashing."""
        return self.card_in_play, self.pot, *(p.prehash() for p in self.players)

    def deal(self, card):
        """Put a card into play"""
        assert self.card_in_play is None, 'Cannot deal a new card; one is already in play!'
        assert self.pot == 0, 'Cannot deal a new card; pot should be zero!'
        self.card_in_play = card

    def take(self, card, pot):
        """Give card and pot to current player."""
        players[0].take(self.card_in_play, self.pot)
        self.card_in_play = None
        self.pot = 0

    def pass(self):
        """Take coin and pass turn to next player."""
        players[0].pass()
        self.pot += 1
        # Move first player to back of list
        self.players.append(self.players.pop(0))


class game_tree():
    """Define a class for drawing a complete No Thanks game tree."""

    def __init__(self, num_players=2, starting_coins=1,
                 low_card=1, high_card=3, discard=1):
        self.tree = nx.DiGraph()
        self.state = game_state(num_players=num_players,
                                starting_coins=starting_coins)
        self.add_node(self.state)

    def add_node(self, state):
        """Add this game state to the tree."""
