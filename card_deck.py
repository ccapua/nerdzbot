import random 

class Deck():

    class Card():

        def __init__(self, suit, value):
            self.suit = suit
            self.value = value

    def __init__(self):
        self._suits = ['♢', '♧', '♤', '♡']
        self._values = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        self.cards = [] # end (self.cards[-1]) is the top
        self.create_deck()
        self.shuffle()
        self.discard = [] # end (self.discard[-1]) is the top

    def create_deck(self):
        self.cards = []
        self.discard = []
        for suit in self._suits:
            for value in self._values:
                self.cards.append(self.Card(suit, value))

    def shuffle(self, grab_discard = False, community_cards = []):
        if grab_discard and len(self.discard) > 0:
            self.cards.append(self.discard)
        if len(community_cards) > 0:
            self.cards.append(community_cards)
        random.shuffle(self.cards)

    def deal(self):
        card = self.cards[-1]
        self.cards.pop(-1)
        return card

    def burn(self, reveal = False):
        self.discard.append(self.cards[-1])
        card = self.cards.pop(-1)
        if reveal:
            return card