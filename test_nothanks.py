import nothanks
import always_pass, always_take, coin_toss


def test_player_score():

    player = nothanks.Player('always_pass', always_pass.run)

    player.cards = []
    player.tokens = 0
    assert player.get_score() == 0

    player.cards = []
    player.tokens = 55
    assert player.get_score() == -55

    player.cards = list(range(3, 36))
    player.tokens = 0
    assert player.get_score() == 3

    player.cards = [10, 11, 12, 14, 16, 17]
    player.tokens = 8
    assert player.get_score() == 10 + 14 + 16 - 8


def test_simple_game():

    strategies = {'always_pass': always_pass.run,
                  'always_take': always_take.run,
                  'coin_toss': coin_toss.run}
    players = [nothanks.Player(x, strategies[x]) for x in strategies]
    game = nothanks.Game(players)

    winner = game.run()
