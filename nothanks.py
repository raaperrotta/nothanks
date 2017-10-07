from random import shuffle
from itertools import cycle
from importlib import import_module
from sortedcontainers import SortedSet


class Player():

    def __init__(self, name, strategy):

        self.id = None  # assigned by the game
        self.tokens = None
        self.cards = SortedSet

        self.strategy_name = name
        self.strategy = strategy

    def get_score(self):

        score = 0
        prev = 0
        self.cards.sort()

        for card in self.cards:
            if card - prev > 1:  # not sequential
                score += card
            prev = card

        score -= self.tokens
        return score

    def get_info(self):
        return({'cards': self.cards, 'tokens': self.tokens})


class Game():

    def __init__(self, players, starting_tokens=11,
                 low_card=3, high_card=35, discard=9):

        # A list of Player objects (3-5)
        self.players = players
        shuffle(self.players)  # randomize play order
        for idx, player in enumerate(players):
            player.id = idx
            player.tokens = starting_tokens

        # A list of game actions
        self.history = []

        # The deck of cards (shuffle then discard first 9)
        self.deck = list(range(low_card, high_card + 1))
        shuffle(self.deck)
        self.deck = self.deck[discard:]

    def run(self):

        card = self.deck.pop()
        pot = 0

        # Play until out of cards
        for player in cycle(self.players):
            playerinfo = [player.get_info() for player in self.players]

            # If current player is out of tokens, they must take it;
            # otherwise, ask if current player wants it
            if player.tokens == 0 or player.strategy(card, pot, playerinfo,
                                                     self.history):
                player.cards.append(card)
                player.tokens += pot
                self.history.append([self.players.index(player),
                                     card, pot, True])
                card = self.deck.pop()
                pot = 0
            else:
                player.tokens -= 1
                self.history.append([self.players.index(player),
                                     card, pot, False])
                pot += 1

            if not self.deck:
                break

        scores = [player.get_score() for player in self.players]
        winning_score = min(scores)

        winner = []
        for player, score in zip(self.players, scores):
            if score == winning_score:
                winner.append(player)

        return winner, scores
