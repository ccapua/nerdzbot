import random
from card_deck import Deck
"""
game proceeds in this manner
command sent

"""


class Dealer():
    def __init__(self, channel):
        self._channel = channel
        self.deck = Deck()
        self.dealt_this_phase = False

    #region game
    async def deal_this_phase(self, players, state, round_number, community_cards = []):
        print('Dealing.')
        #region deal
        if state == 'deal':
            # shuffle
            self.deck.shuffle(grab_discard = True, community_cards = community_cards)
            await self._channel.send(
                'Deck shuffled.', 
                delete_after=120
            )
            # alert players of dealing
            await self._channel.send(
                f'Round {round_number}: Dealing to players...', 
                delete_after=120
            )
            # deal, add cards to player hands, and dm them their cards
            for player in players:
                cards = []
                cards.append(self.deck.deal())
                cards.append(self.deck.deal())
                player.hand = cards
                await self._channel.send(
                    f'Dealing cards to {player.user.display_name}...',
                    delete_after = 120
                )
                await player.user.send(
                    content=f'{cards[0].suit}{cards[0].value} {cards[1].suit}{cards[1].value}'
                )
                print('Cards sent.')

            # cleanup
            self.dealt_this_phase = True
            await self._channel.send(
                'Dealt.', 
                delete_after=120
            )
        #endregion deal
        #region flop
        elif state == 'flop':
            # alert players
            await self._channel.send(
                f'Round {round_number}: Revealing the flop...'
            )
            # deal
            cards = []
        
            self.deck.burn() # burn one
            
            for i in range(0, 3):
                card = self.deck.deal()
                cards.append(card)
                community_cards.append(card)
            # reveal to players
            await self._channel.send(' '.join([f'{card.suit}{card.value}' for card in community_cards]))
            # cleanup
            self.dealt_this_phase = True
            return community_cards
        #endregion flop
        #region turn
        elif state == 'turn':
            await self._channel.send(
                f'Round {round_number}: Revealing the turn...'
            )
            self.deck.burn()
            card = self.deck.deal()
            community_cards.append(card)
            await self._channel.send(
                f"{' '.join([card.suit + card.value for card in community_cards])}"
            )
            self.dealt_this_phase = True
            return community_cards
        #endregion turn
        #region river
        elif state == 'river':
            await self._channel.send(
                f'Round {round_number}: Revealing the river...'
            )
            self.deck.burn()
            card = self.deck.deal()
            community_cards.append(card)
            await self._channel.send(
                f"{' '.join([card.suit + card.value for card in community_cards])}"
            )
            self.dealt_this_phase = True
            return community_cards
        #endregion river
        else:
            return

    def move_blinds(self, players):
        small_index = 0
        big_index = 0
        end = len(players) - 1
        
        for i in range(0, len(players)):
            if players[i].is_small_blind:
                small_index = i
                players[i].is_small_blind = False
            elif players[i].is_big_blind:
                big_index = i
                players[i].is_big_blind = False

        if end == small_index:
            small_index = 0
        else:
            small_index = small_index + 1

        if end == big_index:
            big_index = 0
        else:
            big_index = big_index + 1

        players[small_index].is_small_blind = True
        players[big_index].is_big_blind = True
    #endregion game
    #region messaging
    async def send_betting_alert(self, next_bet, call, who_raised = 'Nobody'):
        check = ''
        if call == 0:
            check = "> n!holdem check\n"
        await self._channel.send(
            f"It is your turn, {next_bet.user.display_name}", 
            delete_after=60
        )
        await self._channel.send(
            f"Minimum bet to stay: ${call} ({who_raised} raised)"
            "Your options are:\n" +
            "> n!holdem bet [*a number (no dollar sign)*]\n" + 
            "> n!holdem call\n" +
            f"{check}" +
            "> n!holdem fold", 
            delete_after=60
        )
        await next_bet.user.send(
            f"It is your turn, {next_bet.user.mention}"
        )

    async def send_betting_order(self, betting_order):
        await self._channel.send(
            'The betting order is currently:\n', 
            delete_after=45
        )
        for player in betting_order:
            blind = ''
            if player.is_small_blind:
                blind = ' (small blind)'
            elif player.is_big_blind:
                blind = ' (big blind)'
            await self._channel.send(
                f'{player.user.display_name}{blind}', 
                delete_after=45
            )

    async def send_card_reveal_messages(self):
        pass

    async def send_current_pot(self, pot):
        await self._channel.send(
            f"Current pot is ${pot}.",
            delete_after=120
        )
    #endregion messaging

class Player():
    def __init__(self, user):
        self.user = user
        self.money = 0
        self.hand = []
        self.is_small_blind = False 
        self.is_big_blind = False

class Game():

    def __init__(self, channel):
        self._channel = channel
        self._players = [] # order of this list is the table order

        self.small_blind = 0
        self.big_blind = 0
        self._small_blind_posted = False
        self._big_blind_posted = False

        self._round_number = 1
        
        self._betting_order = []
        self._bets_this_round = []
        self._last_call = 0
        self._call = 0
        self._pot = 0

        
        self._community_cards = []
        # shuffle players and assign blinds
        self.state = 'waiting for player list'

    def _find_player(self, name):
        for player in self._players:
            if player.user.display_name == name:
                return player
        return False

    #region game flow functions
    async def _start_game(self): # this is called after _setup_players()
        # called from set_money()
        if len(self._players) == 0:
            print('No players found.')
            return

        random.shuffle(self._players)
        print('Players shuffled.')
        self._players[0].is_small_blind = True
        self._players[1].is_big_blind = True
        # generate a dealer
        print('Creating dealer.')
        self.dealer = Dealer(self._channel)

        # generate betting order
        await self._generate_betting_order(next_round=True)
        # advance to dealing phase
        print('Starting game.')
        self.state = 'deal'
        await self._continue_round()

    async def _continue_round(self): # decides whether to continue cycling through bets or to change phases
        # this is called at the beginning of the game and after each bet and deal
        async def _send_to_next_phase(self): # this handles everything that happens when it's time to change phases
            print('Sending to next phase.')
            if self.state == 'deal':
                self.state = 'flop'
            elif self.state == 'flop':
                self.state = 'turn'
            elif self.state == 'turn':
                self.state = 'river'
            elif self.state == 'river':
                self.state = 'deal'
                await self._generate_betting_order(next_round=True)
                self.dealer.move_blinds(self._players)   

            self.dealer.dealt_this_phase = False
            await self._continue_round()

        print('Continuing round.')
        # deal if not dealt yet
        if self.dealer.dealt_this_phase == False: 
            # players, state, round_number, community_cards = []
            await self.dealer.deal_this_phase(self._players, self.state, self._round_number, self._community_cards)
            await self._continue_round()

        print(len(self._betting_order))
        if len(self._betting_order) == 0:
            await _send_to_next_phase(self)
        else:
            await self.dealer.send_betting_alert(self._betting_order[0], self._call)          

    async def _generate_betting_order(self, next_round = False): # generates a betting order based on whether it's the next_round
        print('Generating betting order.')
        print(next_round)
        if next_round:
            # if it's the next round, figure out who is first in the blind rotation
            # and generate a betting order based off of table order (self._players)
            self._betting_order = []
            small_index = 0
            big_index = 0
            # find the index of the small blind
            for i in range(0, len(self._players)-1):
                print(len(self._players))
                if self._players[i].is_small_blind:
                    small_index = i
                    break
            # find the index of the big blind
            if small_index != (len(self._players) - 1):
                big_index = small_index + 1
            # add the small blind to the list
            print(small_index)
            print(big_index)
            self._betting_order.append(self._players[small_index])
            print(self._betting_order)
            # go around the table, adding each player until you get back to the small blind
            i = big_index
            while i != small_index:
                self._betting_order.append(self._players[i])
                if i == (len(self._players) - 1):
                    i = 0
                else:
                    i = i + 1
            print(self._betting_order)
        else:
            # otherwise, check whether someone has raised
            # and make a new betting order where the person
            # before them at the table is last
            if self._call > self._last_call:
                self._last_call = self._call
                player_index = self._players.index(self._call_player)
                if player_index == (len(self._players) - 1):
                    i = 0
                else:
                    i = player_index + 1
                while i != player_index:
                    self._betting_order.append(self._players[i])
                    if i == (len(self._players) - 1):
                        i = 0
                    else:
                        i = i + 1
            else:
                return
        await self.dealer.send_betting_order(self._betting_order)


    def _check_win_conditions(self):
        return True 
        # highcard
        #  simple value of the card. lowest: 2 - Highest: Ace
        # pair
        #  two cards with the same value
        # two pairs
        #  two times two cards with the same value
        # three of a kind
        #  three cards with the same value
        # straight
        #  sequence of 5 cards in increasing value (Ace can precede 2 and follow up king)
        # flush
        #  5 cards of the same suit
        # full house
        #  combination of three of a kind and a pair
        # four of a kind
        #  four cards of the same value
        # straight flush
        #  straight of the same suit
        # royal flush
        #  straight flush from 10 to A
    #endregion game flow functions
    #region game setup commands
    async def generate_players(self, users):
        for user in users:
            print(user)
            self._players.append(Player(user))

        self.state = 'waiting for money amount'
        await self._channel.send(
            'Tell me how much money each person starts with.', 
            delete_after=120
        )

    async def set_money(self, num):
        for player in self._players:
            player.money = num

        self.small_blind = num / 100
        self.big_blind = num / 50

        await self._start_game()

    # def end_game(self):
    #     pass  
    #endregion game setup commands
    #region player commands
    async def bet(self, num, name):
        player = self._find_player(name)
        if player:
            if player == self._betting_order[0]:
                if num < player.money and num >= self._call and num > 0:
                    self._pot = self._pot + num 
                    player.money = player.money - num
                    if num > self._call:
                        self._call_player = player
                        self._last_call = self._call
                        self._call = num
                        # change betting order here
                        await self._channel.send(
                            f'{player.user.display_name} raised the bet to ${self._call}. The pot is now ${self._pot}.'
                        )
                    else:
                        await self._channel.send(
                            f'{player.user.display_name} called the bet for ${self._call}. The pot is now ${self._pot}.'
                        )
                    self._betting_order.pop(0)
                    await self._generate_betting_order()
                    await self._continue_round()


    async def call(self, name):
        player = self._find_player(name)
        if player:
            if self._small_blind_posted:
                pass


    async def check(self, name):
        player = self._find_player(name)
        # if player:
        #     if self._call > 0:
        #         await self.dealer.send_betting_options('check')
        #     if self._small_blind_posted and self._big_blind_posted and (self._call == 0 or self._call == self.big_blind):
        #     self._betting_order.pop(0)
        #     self._channel.send(f'{player.user.display_name} checks.')
        # else:
        #     self._channel.send('You cannot check if someone has raised.')

    async def fold(self, name):
        player = self._find_player(name)
        if player:
            for card in player.hand:
                self.dealer.deck.discard.append(card)
            await self._channel.send(f'{player.user.display_name} folds.')
            self._betting_order.pop(self._betting_order.index(player))
    
    # def muck(self, name):
    #     pass

    # def reveal(self, name):
    #     pass
    
    # def leave_table(self, name):
    #     pass
    #endregion player commands
    #region debug commands
    async def deck(self):
        await self._channel.send(
            f"{' '.join([card.suit + card.value for card in self.dealer.deck.cards])}",
            delete_after = 120
        )
    #endregion debug commands