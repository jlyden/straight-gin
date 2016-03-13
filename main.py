#!/usr/bin/env python
""" main.py - Contains handlers called by taskqueue and/or cronjobs. """
import logging

import webapp2
from google.appengine.api import mail, app_identity
from google.appengine.ext import ndb
from api import StraightGinAPI
from utils import get_by_urlsafe

from models import User, Game


class SendReminderEmail(webapp2.RequestHandler):
    def get(self):
        """
        Send a reminder email to each User with email address with games
        in progress. Email body includes a count of active games and
        their urlsafe keys
        Called every day using a cron job
        """
        app_id = app_identity.get_application_id()
        users = User.query(User.email != None)

        for user in users:
            q = user.all_games()
            games = q.filter(Game.game_over == False)
            if games.count() > 0:
                subject = 'Active game reminder!'
                body = 'Hello {}, you have {} games in progress.' \
                       ' Their keys are: {}'.\
                       format(user.name,
                              games.count(),
                              ', '.join(game.key.urlsafe() for game in games))
                logging.debug(body)
                # Send emails
                # Arguments to send_mail are: from, to, subject, body
                mail.send_mail('noreply@{}.appspotmail.com'.
                               format(app_identity.get_application_id()),
                               user.email,
                               subject,
                               body)

class SendMoveEmail(webapp2.RequestHandler):
    def get(self):
        """
        Send a reminder email to player (if email address on file) each time
        the opponent in a game completes a move. Email body provides
        urlsafe key, player's hand, visible draw_card and instructions.
        Uses appEngine Push Queue
        """
        app_id = app_identity.get_application_id()
        users = User.query(User.email != None)

        for user in users:
            q = user.all_games()
            games = q.filter(Game.game_over == False)
            if games.count() > 0:
                subject = 'Active game reminder!'
                body = 'Hello {}, you have {} games in progress.' \
                       ' Their keys are: {}'.\
                       format(user.name,
                              games.count(),
                              ', '.join(game.key.urlsafe() for game in games))
                logging.debug(body)
                # Send emails
                # Arguments to send_mail are: from, to, subject, body
                mail.send_mail('noreply@{}.appspotmail.com'.
                               format(app_identity.get_application_id()),
                               user.email,
                               subject,
                               body)

app = webapp2.WSGIApplication([
    ('/crons/send_reminder', SendReminderEmail),
#    ('/tasks/send_move_email', SendMoveEmail),
], debug=True)
