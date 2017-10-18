import nothanks
from sortedcontainers import SortedSet

class Player(nothanks.Player):

    def __init__(self, threshold=10):
        self.threshold = threshold
        self.cards = SortedSet()

    def play(self, card, pot):
        """Take card if resulting change in score is below the threshold."""
        return self.get_net_score(card) - pot <= self.threshold

    def get_net_score(self, card):
        """Calculate the change in score from cards from taking this card."""
        assert card not in self.cards, ("Cannot add card {} because this player already has it! " +
                                        "({} has {})").format(card, self, list(self.cards))
        if_take = self.cards.copy()
        if_take.add(card)
        return get_score(if_take) - get_score(self.cards)

    def __str__(self):
        return 'Sequence-Threshold {} player'.format(self.threshold)


def get_score(cards):
    """ Calculate No Thanks game score from cards.

    Assumes cards are in sorted order.
    """
    score = 0
    prev = None
    for card in cards:
        if prev is None or card - prev > 1:  # not sequential
            score += card
        prev = card
    return score
