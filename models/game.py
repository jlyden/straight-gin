# Full Stack Nanodegree Project 4 - Straight Gin
# Built by jennifer lyden on provided Tic-Tac-Toe template
#
# Game model and forms for Straight_Gin_API

import logging
import constants
from utils import deal_hand, test_hand
from datetime import date
from score import Score, ScoreForm, ScoreForms
from protorpc import messages
from google.appengine.ext import ndb

class Game(ndb.Model):
    """ Game object """
    player_one = ndb.KeyProperty(required=True, kind='User')
    player_two = ndb.KeyProperty(required=True, kind='User')
    deck = ndb.PickleProperty(required=True)
    hand_one = ndb.PickleProperty(required=True)
    hand_two = ndb.PickleProperty(required=True)
    draw_card = ndb.PickleProperty(required=True)   # Visible draw card
    active_player = ndb.KeyProperty(required=True)  # User whose turn it is
    instructions = ndb.StringProperty()
    mid_move = ndb.BooleanProperty(required=True, default=False)
    game_over = ndb.BooleanProperty(required=True, default=False)
    history = ndb.PickleProperty(required=True)

    @classmethod
    def new_game(cls, player_one, player_two):
        """ Return a new game """
        game = Game(player_one=player_one,
                    player_two=player_two,
                    active_player=player_one)

        # Prepare deck, hands, draw_card
        # Note that deck is transformed and returned with each hand/card dealt
        deck = constants.FULL_DECK
        game.hand_one, deck = deal_hand(constants.HAND_SIZE, deck)
        game.hand_two, deck = deal_hand(constants.HAND_SIZE, deck)
        game.draw_card, game.deck = deal_hand(1, deck)

        # set up history
        text_move = 'goes first'
        game.history = []
        game.history.append((player_one.get().name, text_move))

        game.put()
        return game

    def game_to_form(self):
        """ Return GameForm representation of Game """
        # convert draw_card to string
        string_card = ' '.join(self.draw_card)

        form = GameForm(urlsafe_key=self.key.urlsafe(),
                        player_one=self.player_one.get().name,
                        player_two=self.player_two.get().name,
                        draw_card=string_card,
                        mid_move=self.mid_move,
                        game_over=self.game_over)
        if not self.game_over:
            form.active_player=self.active_player.get().name
        return form

    def hand_to_form(self, player):
        """ Return HandForm representation of player's hand """
        # retrieve correct hand
        if player == self.player_one.get().name:
            hand = self.hand_one
        elif player == self.player_two.get().name:
            hand = self.hand_two
        elif player == "not_given":
            if self.active_player == self.player_one:
                hand = self.hand_one
            else:
                hand = self.hand_two

        # convert hand (sorted) & draw_card to strings
        sorted_hand = sorted(hand)
        string_hand = ' '.join(str(card) for card in sorted_hand)
        string_card = ' '.join(self.draw_card)

        # return proper instructions
        if self.game_over:
            instructions = 'Sorry, game over! No more moves.'
        elif self.mid_move:
            instructions = 'Enter your discard. If you are ready to go' \
                           ' out, also type OUT. Example: D-K OUT'
        else:
            instructions = 'Enter 1 to take visible card or 2 to draw' \
                           ' from pile.'

        form = HandForm(urlsafe_key=self.key.urlsafe(),
                        mid_move=self.mid_move,
                        active_player=self.active_player.get().name,
                        hand=string_hand,
                        draw_card=string_card,
                        instructions=instructions)
        return form

    def end_game(self, chosen=False):
        """
        End game and determine winner -
        chosen: boolean representing if active player chose to go "OUT"
        """
        # check both players' hands
        penalty_one = test_hand(self.hand_one)
        penalty_two = test_hand(self.hand_two)

        # if game ended because no more cards to draw
        if not chosen:
            # winner is player with lower penalty
            if penalty_one < penalty_two:
                score_game(self.player_one, penalty_one, penalty_two)
            elif penalty_two < penalty_one:
                score_game(self.player_two, penalty_two, penalty_one)
            # and penalty tie goes to active player
            else:
                score_game(self.active_player, penalty_one, penalty_two)

        # if game ended because active player signaled "OUT"
        # active player needs penalty of 0 to win
        else:
            if self.active_player == self.player_one:
                if penalty_one == 0:
                    self.score_game(self.player_one, penalty_one, penalty_two)
                else:
                    self.score_game(self.player_two, penalty_two, penalty_one)
            else:
                if penalty_two == 0:
                    self.score_game(self.player_two, penalty_two, penalty_one)
                else:
                    self.score_game(self.player_one, penalty_one, penalty_two)

        self.mid_move = False
        self.game_over = True
        self.put()
        return

    def score_game(self, winner, penalty_winner, penalty_loser):
        """ Set up Score for Game """
        if winner == self.player_one:
            loser = self.player_two
        else:
            loser = self.player_one
        # Add the game to the score 'board'
        score = Score(date=date.today(),
                      game=self.key,
                      winner=winner,
                      loser=loser,
                      penalty_winner=penalty_winner,
                      penalty_loser=penalty_loser)
        score.put()

        # Update the user models
        winner.get().add_win()
        loser.get().add_loss()
        return

    def history_to_form(self):
        """
        Return GameHistoryForm representation of Game
        Assistance with list[tuples]->list[str]:
        http://stackoverflow.com/questions/11696078/python-converting-a-list-of-tuples-to-a-list-of-strings
        """
        history_list = ['%s %s' % x for x in self.history]
        history = '; '.join(str(move) for move in history_list)

        history_form = GameHistoryForm(urlsafe_key=self.key.urlsafe(),
                               player_one=self.player_one.get().name,
                               player_two=self.player_two.get().name,
                               game_over=self.game_over,
                               history=history)
        return history_form


class NewGameForm(messages.Message):
    """ Used to create a new game """
    player_one = messages.StringField(1, required=True)
    player_two = messages.StringField(2, required=True)


class GameForm(messages.Message):
    """ GameForm for outbound game state information """
    urlsafe_key = messages.StringField(1, required=True)
    player_one = messages.StringField(2, required=True)
    player_two = messages.StringField(3, required=True)
    active_player = messages.StringField(4)
    draw_card = messages.StringField(5, required=True)
    mid_move = messages.BooleanField(6, required=True)
    game_over = messages.BooleanField(7, required=True)


class GameForms(messages.Message):
    """Container for multiple GameForm"""
    items = messages.MessageField(GameForm, 1, repeated=True)


class HandForm(messages.Message):
    """ HandForm for outbound hand state information """
    urlsafe_key = messages.StringField(1, required=True)
    mid_move = messages.BooleanField(2, required=True)
    active_player = messages.StringField(3, required=True)
    hand = messages.StringField(4, required=True)
    draw_card = messages.StringField(5, required=True)
    instructions = messages.StringField(6, required=True)


class GameHistoryForm(messages.Message):
    """ GameHistoryForm for detailed game information """
    urlsafe_key = messages.StringField(1, required=True)
    player_one = messages.StringField(2, required=True)
    player_two = messages.StringField(3, required=True)
    game_over = messages.BooleanField(4, required=True)
    history = messages.StringField(5)


class MoveForm(messages.Message):
    """ Used to make a move in an existing game """
    user_name = messages.StringField(1, required=True)
    move = messages.StringField(2, required=True)


class StringMessage(messages.Message):
    """ StringMessage -- outbound (single) string message """
    message = messages.StringField(1, required=True)
