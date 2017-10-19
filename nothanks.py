"""Define the No Thanks Game and Player."""

from itertools import cycle
import logging
from random import shuffle
from sortedcontainers import SortedSet

logger = logging.getLogger(__name__)
# It is poor practice to configura a logger in a module, instead, configure it as needed wherever it is used.
# logger.setLevel(level=logging.DEBUG)
# logger.addHandler(logging.StreamHandler(sys.stdout))

class Player():  # pylint: disable=unused-argument
    """Define the base class for No Thanks players.

    More advanced players must be subclasses of Player. This base class
    implements a playable, but poor-performing, strategy of taking cards only
    when out of coins.

    When subclassing Player, the creator (__init__) must be callable with no
    arguments as this is how it will be called during the competition. Use
    default arguments to define a flexible creator that can also accept no
    arguments.
    """

    def update(self, player_id, card, pot, action):
        """Receive action notification from game.

        After every player's turn, all players will be notified of the action
        chosen (take card and pot or pay one and pass).
        player_id: a unique identifier for the player. Will be the same across
                   games for any player instance.
        card: card value
        pot: pot value
        action: True if the player took the card and pot, False otherwise
        """
        pass

    def play(self, card, pot):
        """Return decision to take card and pot or not.

        card: card value
        pot: coins in pot
        """
        return False

    def prepare_for_new_game(self, player_order):
        """Prepare for a new game.

        When the player tracks the game state, use this function to erase prior
        game state and start fresh.
        player_order: a list of player instance ids specifying the order of play
        """
        pass


class Game():
    """Define No Thanks Game.

    Create an instance of this object for each No Thanks game, even when playing
    repeated games with the same players.
    """

    def __init__(self, players, starting_coins=11,
                 low_card=3, high_card=35, discard=9):
        # Too keep track of player states for rule enforcement and scoring
        self.state = {}
        for player in players:
            self.state[id(player)] = {'cards': SortedSet(),
                                      'coins': starting_coins}

        # A list of Player objects
        self.players = players.copy()  # keep a local copy of the player list
        shuffle(self.players)  # randomize play order

        # The deck of cards (create, shuffle, then discard)
        self.deck = list(range(low_card, high_card + 1))
        shuffle(self.deck)
        del self.deck[:discard]

    def deal_card(self):
        """Remove first card from deck and return it."""
        return self.deck.pop(0)

    def run(self):
        """Set-up, play, and score a game of No Thanks."""
        # Have players prepare for new game and tell them the player order
        logger.debug('START: Starting new game with players {}.'.format(self.players))
        player_order = [id(p) for p in self.players]
        for player in self.players:
            player.prepare_for_new_game(player_order)

        # Deal first card
        card = self.deal_card()
        pot = 0

        # Play until out of cards (see break statement below)
        player_cycler = cycle(self.players)
        player = next(player_cycler)
        player_id = id(player)
        player_state = self.state[player_id]
        while True:
            logger.debug(('TURN: Player {} is offered card {} and {} coin{} ' +
                          'and has {} and {} coin{}.').format(player, card, pot, 's'[pot==1:],
                                                     list(player_state['cards']),
                                                     player_state['coins'], 's'[player_state['coins']==1:]))
            # If current player is out of tokens, they must take it;
            # otherwise, ask if current player wants it
            took_card = player_state['coins'] == 0 or player.play(card, pot)

            # Notify all players of action chosen (with card and pot from beginning of turn)
            for p in self.players:
                p.update(player_id, card, pot, took_card)

            if took_card:
                player_state['cards'].add(card)
                player_state['coins'] += pot
                logger.debug(('TAKE: Player {} took them and now ' +
                              'has {} and {} coin{}.').format(player,
                                                        list(player_state['cards']),
                                                        player_state['coins'], 's'[player_state['coins']==1:]))
                if self.deck:
                    card = self.deal_card()
                    pot = 0
                    logger.debug('DEAL: The next card is {}. (Pot reset to 0.)'.format(card))
                else:  # game over
                    logger.debug('END: Game over!')
                    break
            else:
                player_state['coins'] -= 1
                logger.debug(('PASS: Player {} said "No Thanks!" and now ' +
                              'has {} coin{}. The pot now has {} coin{}.').format(player,
                                                       player_state['coins'], 's'[player_state['coins']==1:], pot, 's'[pot==1:]))
                pot += 1
                player = next(player_cycler)
                player_id = id(player)
                player_state = self.state[player_id]

        # Tally final scores
        scores = self.get_scores()
        winning_score = min(scores.values())
        # Check for winners
        winners = []
        for player_id, score in scores.items():
            if score == winning_score:
                winners.append(player_id)
        # Return the list of winners (ids) and all players' scores
        logger.debug('RESULT: {}'.format(scores))
        return winners, scores

    def get_scores(self):
        """Calculate score of game."""
        scores = {}
        for player in self.players:
            player_id = id(player)
            score = 0
            prev = None
            for card in self.state[player_id]['cards']:
                if prev is None or card - prev > 1:  # not sequential
                    score += card
                prev = card
            score -= self.state[player_id]['coins']
            scores[id(player)] = score
        return scores
