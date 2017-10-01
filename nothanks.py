from random import shuffle
from itertools import cycle


class Player():

    def __init__(self, strategy):

        self.tokens = 11
        self.cards = []

        self.strategy = strategy.run

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

    def __init__(self, players):

        # A list of Player objects (3-5)
        assert 3 <= len(players) <= 5
        for player in players:
            assert isinstance(player, Player)
        self.players = players
        shuffle(self.players)  # randomize play order

        # A list of game actions
        self.history = []

        # The deck of cards (shuffle then discard first 9)
        self.deck = list(range(3, 36))
        shuffle(self.deck)
        self.deck = self.deck[9:]

    def run(self):

        # Play until out of cards
        while self.deck:

            # Deal a card
            card = self.deck.pop()
            pot = 0

            for player in cycle(self.players):
                playerinfo = [player.get_info() for player in self.players]
                # If current player is out of tokens, they must take it;
                # otherwise, ask if current player wants it
                if player.tokens == 0 or player.strategy(card, pot, playerinfo,
                                                         self.history):
                    player.cards.append(card)
                    player.tokens += pot
                    pot = 0
                    break
                else:
                    player.tokens -= 1
                    pot += 1

        scores = [player.get_score() for player in self.players]
        winning_score = min(scores)

        winner = []
        for player, score in zip(self.players, scores):
            if score == winning_score:
                winner.append(player)

        return winner, scores
