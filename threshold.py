import nothanks.Player


class Player(nothanks.Player):
    def __init__(self, threshold):
        self.threshold = threshold
    def run(self, card, pot, *args):
        return card - pot <= self.threshold
