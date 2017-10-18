import pytest
import threshold
from sortedcontainers import SortedSet


def test_decision():
    """Test the logic by which the player decides to take or not."""
    player = threshold.Player(threshold=10)

    player.cards = SortedSet()
    assert player.play(20, 11) == True
    assert player.play(20, 10) == True
    assert player.play(20, 9) == False

    player.threshold = 5

    assert player.play(20, 16) == True
    assert player.play(20, 15) == True
    assert player.play(20, 14) == False