import nothanks
from sortedcontainers import SortedSet

class Player(nothanks.Player):

    def __init__(self, threshold=10):
        self.threshold = threshold
        self.cards = SortedSet()

    def run(self, card, pot, *args):
        return get_net_score(self, card) - pot <= self.threshold

    def get_net_score(self, card):
        if_take = self.cards.copy()
        if_take.add(card)
        return get_score(if_take) - get_score(self.cards)

    def __str__(self):
        return 'Sequence-Threshold {} player'.format(self.threshold)


def get_score(cards):
    """ Calculate No Thanks game score from cards """
    sort(cards)
    score = 0
    prev = None
    for card in cards:
        if prev is None or card - prev > 1:  # not sequential
            score += card
        prev = card
