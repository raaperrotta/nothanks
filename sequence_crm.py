import crm

class Strategy(crm.Strategy):

    def prehash(self, state):
        """Reduce the game state to a hashable, abstract representation."""
        # Return the card in play, an enumeration for the pot size, and - for
        # each player - flags to indicate posession of either card, two cards on
        # either side of the card in play.
        card = state.card_in_play
        pot = state.pot

        if pot < 2:
            pot_enum = pot
        elif pot < 5:
            pot_enum = 3
        elif pot < 10:
            pot_enum = 4
        else:
            pot_enum = 5

        player_data = []
        for player in state.players:
            card_data = []
            for other_card in [card-2, card-1, card+1, card+2]:
                card_data.append(other_card in player.cards)
            player_data.append(tuple(card_data))

        return (card, pot_enum, *player_data)
