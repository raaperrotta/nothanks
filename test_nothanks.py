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
    """Ensure exceptions raised in player actions are caught by nothanks.Game."""

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
    # Test that the game captures the errors
    game.run()

def test_player_action():
    """Ensure basic No Thanks game rules are followed."""

    players = [nothanks.Player(), nothanks.Player(), nothanks.Player()]
    game = nothanks.Game(players)
    player = players[0]
    state = game.state[id(player)]

    card = game.deal_card()
    pot = 0
    # Players with no coins MUST take the card and pot
    state['coins'] = 0
    took_card = game.player_action(player, card, pot)
    assert took_card

def test_update_game_take():
    """Ensure basic No Thanks game rules are followed."""

    players = [nothanks.Player(), nothanks.Player(), nothanks.Player()]
    game = nothanks.Game(players)
    player = players[0]
    state = game.state[id(player)]

    # When a player takes a card and pot:
    # See that card and pot are added to player state
    # And that the same player goes again
    # And that a new card is dealt
    prev_coins = state['coins']
    card = game.deal_card()
    pot = 10
    new_player, new_card, new_pot = game.update_game(player, card, pot, True)
    assert card in state['cards']
    assert state['coins'] == prev_coins + pot
    assert new_player is player
    assert new_card is not card
    assert new_pot == 0
    # Trying to take the same card again should raise an exception.
    with pytest.raises(Exception):
        game.update_game(player, card, pot, True)

def test_update_game_pass():
    """Ensure basic No Thanks game rules are followed."""

    players = [nothanks.Player(), nothanks.Player(), nothanks.Player()]
    game = nothanks.Game(players)
    player = players[0]
    state = game.state[id(player)]

    # When a player passes:
    # See that they lose a coin
    # And the pot grows by one
    # And the card does not change
    # And that a different player goes next
    prev_coins = state['coins']
    card = game.deal_card()
    pot = 10
    new_player, new_card, new_pot = game.update_game(player, card, pot, False)
    assert card not in state['cards']
    assert state['coins'] == prev_coins - 1
    assert new_player is not player
    assert new_card == card
    assert new_pot == pot + 1
    # Trying to pass with no coins should raise an exception.
    state['coins'] = 0
    with pytest.raises(Exception):
        game.update_game(player, card, pot, False)
