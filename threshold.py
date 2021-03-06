import nothanks


class Player(nothanks.Player):

    def __init__(self, threshold=10):
        self.threshold = threshold

    def play(self, card, pot):
        return card - pot <= self.threshold

    def __str__(self):
        return 'Threshold {} player'.format(self.threshold)
