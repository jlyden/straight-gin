# Full Stack Nanodegree Project 4 - Straight Gin
# Built by jennifer lyden on provided Tic-Tac-Toe template
#
# Score model and forms for Straight_Gin_API

import logging
from datetime import date
from protorpc import messages
from google.appengine.ext import ndb


class Score(ndb.Model):
    """ Score object """
    date = ndb.DateProperty(required=True)
    game = ndb.KeyProperty(required=True, kind="Game")
    winner = ndb.KeyProperty(required=True, kind="User")
    loser = ndb.KeyProperty(required=True, kind="User")
    penalty_winner = ndb.IntegerProperty(required=True)
    penalty_loser = ndb.IntegerProperty(required=True)

    def score_to_form(self):
        return ScoreForm(date=str(self.date),
                         winner=self.winner.get().name,
                         loser=self.loser.get().name,
                         penalty_winner=self.penalty_winner,
                         penalty_loser=self.penalty_loser)


class ScoreForm(messages.Message):
    """ ScoreForm for outbound Score information """
    date = messages.StringField(1, required=True)
    winner = messages.StringField(2, required=True)
    loser = messages.StringField(3, required=True)
    penalty_winner = messages.IntegerField(4, required=True)
    penalty_loser = messages.IntegerField(5, required=True)


class ScoreForms(messages.Message):
    """ Return multiple ScoreForms """
    items = messages.MessageField(ScoreForm, 1, repeated=True)


class StringMessage(messages.Message):
    """ StringMessage -- outbound (single) string message """
    message = messages.StringField(1, required=True)
