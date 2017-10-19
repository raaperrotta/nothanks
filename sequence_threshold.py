import nothanks

import logging
from sortedcontainers import SortedSet

logger = logging.getLogger(__name__)


class Player(nothanks.Player):

    def __init__(self, threshold=10):
        self.threshold = threshold
        self.cards = SortedSet()

    def play(self, card, pot):
        """Take card if resulting change in score is below the threshold."""
        logger.debug('PLAY: Player {} thinks he has {} and is being offered {} and {} coin{}.'.format(self, list(self.cards), card, pot, "s"[pot==1:]))
        return self.get_net_score(card) - pot <= self.threshold

    def update(self, player_id, card, _, action):
        """If this player took a card, record it."""
        if player_id == id(self) and action:
            self.cards.add(card)
            logger.debug('UPDATE: Player {} records taking {} and now has {}.'.format(self, card, list(self.cards)))

    def prepare_for_new_game(self, _):
        """Reset card property."""
        self.cards = SortedSet()

    def get_net_score(self, card):
        """Calculate the change in score from cards from taking this card."""
        assert card not in self.cards, ("Cannot add card {} because this player already has it! " +
                                        "({} has {})").format(card, self, list(self.cards))
        if_take = SortedSet(self.cards)
        if_take.add(card)
        return get_score(if_take) - get_score(self.cards)

    def __str__(self):
        return '<Sequence-Threshold {} player>'.format(self.threshold)


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
