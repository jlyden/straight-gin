#!/usr/bin/env python
""" main.py - Contains handlers called by taskqueue and/or cronjobs. """

import logging
import webapp2
from google.appengine.api import mail, app_identity
from google.appengine.ext import ndb
from api import StraightGinAPI
from utils import get_by_urlsafe

from models import User, Game


class game_reminder_email(webapp2.RequestHandler):
    def get(self):
        """
        Send a reminder email to each User with email address with games
        in progress. Email body includes a count of in-progress games and
        their urlsafe keys
        Called every day using a cron job
        """
        app_id = app_identity.get_application_id()
        users = User.query(User.email != None)

        for user in users:
            q = user.all_games()
            games = q.filter(Game.game_over == False)
            if games.count() > 0:
                subject = 'In Progress game reminder!'
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


class move_alert_email(webapp2.RequestHandler):
    def post(self):
        """
        Send a reminder email to player (if email address on file) each time
        the opponent in a game completes a move. Email body provides
        urlsafe key, player's hand, visible draw_card and instructions.
        Uses appEngine Push Queue
        """
        app_id = app_identity.get_application_id()
        user = get_by_urlsafe(self.request.get('user_key'), User)
        game = get_by_urlsafe(self.request.get('game_key'), Game)

        # Get hand of current player
        if game.active_player == game.player_one:
            hand = game.hand_one
        else:
            hand = game.hand_two

        # Format game data for e-mail
        sorted_hand = sorted(hand)
        string_hand = ' '.join(str(card) for card in sorted_hand)
        string_card = ' '.join(game.draw_card)

        # Prepare e-mail
        subject = 'Your turn!'
        body = "Hello {}: Your opponent just moved, so it's your turn." \
               " Your hand is {}. The visible card is {}." \
               " When you go to start_move, enter 1 to take visible card" \
               " or 2 to draw from pile. The game key is {}.". \
               format(user.name, string_hand, string_card, game.key.urlsafe())
        logging.debug(body)
        # Arguments to send_mail are: from, to, subject, body
        mail.send_mail('noreply@{}.appspotmail.com'.format(
            app_identity.get_application_id()), user.email, subject, body)

app = webapp2.WSGIApplication([
    ('/crons/reminders', game_reminder_email),
    ('/tasks/send_moves', move_alert_email),
], debug=True)
