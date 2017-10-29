import crm

import pytest

def test_PlayerState():

    starting_coins = 11
    state = crm.PlayerState(starting_coins)
    assert len(state.cards) == 0  # starts with no cards
    assert state.coins == starting_coins  # starts with specified coins
    # on pass, should lose a coin
    state.pass_turn()
    assert state.coins == starting_coins - 1  # lost exactly one coin
    # on take, adds card and pot to collection
    state.take(35, 6)
    assert 35 in state.cards
    assert state.coins == starting_coins - 1 + 6

def test_GameState():

    state = crm.GameState(num_players=3, starting_coins=11,
                          low_card=3, high_card=35, discard=9)
    assert state.card_in_play is None
    assert len(state.players) == 3
    state.deal(35)
    assert state.card_in_play == 35
    assert state.pot == 0

    state.pass_turn()
    assert state.card_in_play == 35
    assert state.pot == 1
    state.pass_turn()
    assert state.pot == 2

    state.take()
    assert state.card_in_play is None
    assert state.pot == 0
    assert 35 in state.players[0].cards
    assert state.players[0].coins == 13

    # After the same player passes, it should move to end of list
    state.deal(3)
    state.pass_turn()
    assert 35 in state.players[-1].cards
    assert state.players[-1].coins == 12

    assert 35 not in state.possible_next_cards()

    state.reset()
    assert state.card_in_play is None
    assert len(state.players) == 3
    for player in state.players:
        assert len(player.cards) == 0
        assert player.coins == 11  # starting coins

def test_Strategy():

    strategy = crm.Strategy(num_players=2, starting_coins=2,
                            low_card=1, high_card=3, discard=1)

    # Getting with a key that isn't in the dictionary should return the defaults
    value1 = strategy.data['not in data']
    assert value1['visits'] == 0
    assert value1['strategy'] == 0.5
    value2 = strategy.data['also not in data']
    assert value1['visits'] == 0
    assert value1['strategy'] == 0.5
    # ensure these are distinct (no side effects)
    value2['visits'] = 1
    assert value1['visits'] == 0