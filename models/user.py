# Full Stack Nanodegree Project 4 - Straight Gin
# Built by jennifer lyden on provided Tic-Tac-Toe template
#
# User model and forms for Straight_Gin_API

import logging
from game import Game
from score import Score, ScoreForm, ScoreForms
from protorpc import messages
from google.appengine.ext import ndb


class User(ndb.Model):
    """ User profile """
    name = ndb.StringProperty(required=True)
    email = ndb.StringProperty()
    total_games = ndb.IntegerProperty(default=0)
    wins = ndb.IntegerProperty(default=0)
    win_rate = ndb.FloatProperty(default=0.0)

    def user_to_form(self):
        """ Populate UserForm """
        return UserForm(name=self.name,
                        email=self.email,
                        total_games=self.total_games,
                        win_rate=self.calc_win_rate())

    def all_games(self):
        """
        Return all user games - in progress and complete
        Reference: http://stackoverflow.com/questions/24392270/many-to-many-relationship-in-ndb
        """
        return Game.query(ndb.OR(Game.player_one == self.key,
                                 Game.player_two == self.key))

    def all_scores(self):
        """ Return all user scores - only from completed games """
        return Score.query(ndb.OR(Score.winner == self.key,
                                  Score.loser == self.key))

    def calc_win_rate(self):
        """ Calculate win rate """
        if self.total_games > 0:
            win_rate = float(self.wins)/float(self.total_games)
        else:
            win_rate = 0.0
        return win_rate

    def add_win(self):
        """ Add a win """
        self.wins += 1
        self.total_games += 1
        self.win_rate = self.calc_win_rate()
        self.put()
        return

    def add_loss(self):
        """ Add a loss """
        self.total_games += 1
        self.win_rate = self.calc_win_rate()
        self.put()
        return


class UserForm(messages.Message):
    """ User Form """
    name = messages.StringField(1, required=True)
    email = messages.StringField(2)
    total_games = messages.IntegerField(3, required=True)
    win_rate = messages.FloatField(4)


class UserForms(messages.Message):
    """ Container for multiple User Forms """
    items = messages.MessageField(UserForm, 1, repeated=True)


class StringMessage(messages.Message):
    """ StringMessage -- outbound (single) string message """
    message = messages.StringField(1, required=True)
