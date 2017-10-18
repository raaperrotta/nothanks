import pytest
import sequence_threshold
from sortedcontainers import SortedSet

def test_get_score():
    """Test the helper function in sequence_threshold that calculates a player's score from cards"""

    assert sequence_threshold.get_score([]) == 0
    assert sequence_threshold.get_score(SortedSet()) == 0
    assert sequence_threshold.get_score(list(range(3, 36))) == 3
    assert sequence_threshold.get_score([10, 11, 12, 14, 16, 17]) == 10 + 14 + 16

def test_net_score():
    """Test the sequence_threshold.Player method for calculating the net score effect from taking a card."""
    player = sequence_threshold.Player()

    player.cards = SortedSet()
    assert player.get_net_score(1) == 1
    assert player.get_net_score(6) == 6
    assert player.get_net_score(35) == 35

    player.cards = SortedSet([2, 7, 36])
    # Taking a card one lower than a card you have decreases your score by one.
    assert player.get_net_score(1) == -1
    assert player.get_net_score(6) == -1
    assert player.get_net_score(35) == -1
    # Taking a card one higher than a card you have does not change your score.
    assert player.get_net_score(3) == 0
    assert player.get_net_score(8) == 0
    assert player.get_net_score(37) == 0
    # You can never take a card you already have. This should cause an error rather than return 0.
    with pytest.raises(Exception):
        player.get_net_score(2)
    with pytest.raises(Exception):
        player.get_net_score(7)
    with pytest.raises(Exception):
        player.get_net_score(36)

    player.cards = SortedSet([2, 4, 27, 29])
    # Completing these sequences with the in-between card decreases your score by the higher card amount.
    assert player.get_net_score(3) == -4
    assert player.get_net_score(28) == -29


def test_decision():
    """Test the logic by which the player decides to take or not."""
    player = sequence_threshold.Player(threshold=10)

    player.cards = SortedSet()
    assert player.play(20, 11) == True
    assert player.play(20, 10) == True
    assert player.play(20, 9) == False

    player.cards = SortedSet([30])
    assert player.play(20, 11) == True
    assert player.play(20, 10) == True
    assert player.play(20, 9) == False
    assert player.play(31, 1) == True
    assert player.play(29, 1) == True
    assert player.play(32, 1) == False
    with pytest.raises(Exception):
        player.play(30, 1)

    player.threshold = 5

    player.cards = SortedSet()
    assert player.play(20, 16) == True
    assert player.play(20, 15) == True
    assert player.play(20, 14) == False

    player.cards = SortedSet([30])
    assert player.play(20, 16) == True
    assert player.play(20, 15) == True
    assert player.play(20, 14) == False
    assert player.play(31, 1) == True
    assert player.play(29, 1) == True
    assert player.play(32, 1) == False
    with pytest.raises(Exception):
        player.play(30, 1)