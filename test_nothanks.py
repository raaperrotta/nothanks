import nothanks
from sortedcontainers import SortedSet
import pytest

def test_scoring():
    """Test the method of nothanks.Game that calculates each player's score"""
    player = nothanks.Player()
    game = nothanks.Game([player])

    pid = id(player)
    player_state = game.state[pid]

    player_state['cards'] = SortedSet()
    player_state['coins'] = 0
    assert game.get_scores()[pid] == 0

    player_state['cards'] = SortedSet()
    player_state['coins'] = 55
    assert game.get_scores()[pid] == -55

    player_state['cards'] = SortedSet(range(3, 36))
    player_state['coins'] = 0
    assert game.get_scores()[pid] == 3

    player_state['cards'] = SortedSet([10, 11, 12, 14, 16, 17])
    player_state['coins'] = 8
    assert game.get_scores()[pid] == 10 + 14 + 16 - 8

def test_cards():
    """Ensure all cards are in expected range and expected number was discarded"""
    low_card = 3
    high_card = 35
    discard = 9
    game = nothanks.Game([], low_card=low_card, high_card=high_card,
                         discard=discard)

    num_cards = 0
    while game.deck:
        num_cards += 1
        assert low_card <= game.deal_card() <= high_card

    assert num_cards == high_card + 1 - low_card - discard

    low_card = 1
    high_card = 10
    discard = 2
    game = nothanks.Game([], low_card=low_card, high_card=high_card,
                         discard=discard)

    num_cards = 0
    while game.deck:
        num_cards += 1
        assert low_card <= game.deal_card() <= high_card

    assert num_cards == high_card + 1 - low_card - discard

def test_bad_player():

    class BadPlayer(nothanks.Player):
        def play():  # will raise exception because of bad argument count
            pass
        def update():  # will raise exception because of bad argument count
            pass
        def prepare_for_new_game():  # will raise exception because of bad argument count
            pass

    bad_player = BadPlayer()
    players = [nothanks.Player(), nothanks.Player(), bad_player]
    game = nothanks.Game(players)

    # Double-check that these raise an error
    with pytest.raises(Exception):
        bad_player.play(35, 0)
    with pytest.raises(Exception):
        bad_player.update(id(bad_player), 35, 0, False)
    with pytest.raises(Exception):
        bad_player.prepare_for_new_game([id(p) for p in players])
    # Test that the game captures the error
    game.run()
