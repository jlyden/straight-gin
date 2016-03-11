# models for Straight_Gin_API
# AFTER TESTING, CHANGE HAND_SIZE

import constants
from utils import deal_hand, test_hand
from datetime import date
from protorpc import messages
from google.appengine.ext import ndb

# - - - - - Objects - - - - -

class User(ndb.Model):
    """User profile"""
    name = ndb.StringProperty(required=True)
    email = ndb.StringProperty(required=True)
    wins = ndb.IntegerProperty(default=0)
    games = ndb.IntegerProperty(default=0)
    total_penalty = ndb.IntegerProperty(default=0)

    @property
    def win_rate(self):
        if self.games > 0:
            return float(self.wins)/float(self.games)
        else:
            return 0.0

    @property
    def avg_penalty(self):
        if self.games > 0:
            return float(self.total_penalty)/float(self.games)
        else:
            return 0.0

    def user_to_form(self):
        return UserForm(name=self.name,
                        email=self.email,
                        wins=self.wins,
                        games=self.games,
                        win_rate=self.win_rate,
                        avg_penalty=self.avg_penalty)

    def add_win(self):
        """Add a win"""
        self.wins += 1
        self.games += 1
        self.put()

    def add_loss(self):
        """Add a loss"""
        self.games += 1
        self.put()

    def add_penalty(self,penalty):
        """Add to total_penalty"""
        self.total_penalty += penalty
        self.put()


class Game(ndb.Model):
    """Game object"""
    deck = ndb.PickleProperty(required=True)
    player_one = ndb.KeyProperty(required=True, kind='User')
    player_two = ndb.KeyProperty(required=True, kind='User')
    hand_one = ndb.PickleProperty(required=True)
    hand_two = ndb.PickleProperty(required=True)
    active = ndb.KeyProperty(required=True)       # User whose turn it is
    draw_card = ndb.PickleProperty(required=True) # Visible draw card
    mid_move = ndb.BooleanProperty(required=True, default=False)
    instructions = ndb.StringProperty()
    game_over = ndb.BooleanProperty(required=True, default=False)
    winner = ndb.KeyProperty()
    penalty_one = ndb.IntegerProperty()
    penalty_two = ndb.IntegerProperty()
    history = ndb.PickleProperty(required=True)

    @classmethod
    def new_game(cls, player_one, player_two):
        """Creates and returns a new game"""
        game = Game(player_one=player_one,
                    player_two=player_two,
                    active=player_one)

        # Prepare deck, hands, draw_card
        # Note that deck is transformed with each card dealt
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
        """Returns a GameForm representation of the Game"""
        # convert draw_card to string
        string_card = ' '.join(self.draw_card)

        form = GameForm(urlsafe_key=self.key.urlsafe(),
                        player_one=self.player_one.get().name,
                        player_two=self.player_two.get().name,
                        active=self.active.get().name,
                        draw_card=string_card,
                        mid_move=self.mid_move,
                        game_over=self.game_over)
        if self.winner:
            form.winner = self.winner.get().name
        return form

    def hand_to_form(self):
        """Returns a HandForm representation active player's hand"""
        # If game is over, return history instead
        if self.game_over:
            return self.history_to_form()
        else:
            # retrieve correct hand
            if self.active == self.player_one:
                hand = self.hand_one
            else:
                hand = self.hand_two

            # convert sorted hand & draw_card to strings
            sorted_hand = sorted(hand)
            string_hand = ' '.join(str(card) for card in sorted_hand)
            string_card = ' '.join(self.draw_card)

            # return proper instructions
            if self.mid_move:
                instructions = 'Enter your discard. If you are ready to go out, also type OUT. Example: D-K OUT'
            else:
                instructions = 'Enter 1 to take visible card or 2 to draw from pile.'

            form = HandForm(urlsafe_key=self.key.urlsafe(),
                            mid_move=self.mid_move,
                            active=self.active.get().name,
                            hand=string_hand,
                            draw_card=string_card,
                            instructions=instructions)
            return form

    def end_game(self, chosen=False):
        """
        chosen: boolean representing if active player has chosen to go "OUT"
        """
        # check both players' hands and record penalties
        self.penalty_one = test_hand(self.hand_one)
        self.player_one.get().add_penalty(self.penalty_one)
        self.penalty_two = test_hand(self.hand_two)
        self.player_two.get().add_penalty(self.penalty_two)

        # if game ended because no more cards to draw
        if not chosen:
            if self.penalty_one < self.penalty_two:
                self.win_game(self.player_one)
            elif self.penalty_two < self.penalty_one:
                self.win_game(self.player_two)
            # tie goes to active player
            else:
                self.win_game(self.active)

        # if game ended because active player signaled "OUT"
        # active player needs penalty of 0 to win
        else:
            if self.active == self.player_one:
                if self.penalty_one == 0:
                    self.win_game(self.player_one)
                else:
                    self.win_game(self.player_two)
            else:
                if self.penalty_two == 0:
                    self.win_game(self.player_two)
                else:
                    self.win_game(self.player_one)
        self.mid_move = False
        self.put()

    def win_game(self, winner):
        """Sets game winner"""
        self.winner = winner
        self.game_over = True
        self.put()

        loser = self.player_two if winner == self.player_one else self.player_one
        # Add the game to the score 'board'
        score = Score(date=date.today(), winner=winner, loser=loser)
        score.put()

        # Update the user models
        winner.get().add_win()
        loser.get().add_loss()


    def history_to_form(self):
        """
        Returns GameHistoryForm representation of completed Game
        Assistance with list[tuples]->list[str]:
        http://stackoverflow.com/questions/11696078/python-converting-a-list-of-tuples-to-a-list-of-strings
        """
        history_list = ['%s %s' % x for x in self.history]
        history = '; '.join(str(move) for move in history_list)

        form = GameHistoryForm(urlsafe_key=self.key.urlsafe(),
                                player_one=self.player_one.get().name,
                                player_two=self.player_two.get().name,
                                game_over=self.game_over,
                                history=history)
        if self.winner:
            form.winner = self.winner.get().name
            form.penalty_one=self.penalty_one
            form.penalty_two=self.penalty_two
        return form


class Score(ndb.Model):
    """Score object"""
    date = ndb.DateProperty(required=True)
    winner = ndb.KeyProperty(required=True)
    loser = ndb.KeyProperty(required=True)

    def score_to_form(self):
        return ScoreForm(date=str(self.date),
                         winner=self.winner.get().name,
                         loser=self.loser.get().name)


# - - - - - Forms - - - - -

class UserForm(messages.Message):
    """User Form"""
    name = messages.StringField(1, required=True)
    email = messages.StringField(2)
    wins = messages.IntegerField(3)
    games = messages.IntegerField(4, required=True)
    win_rate = messages.FloatField(5)
    avg_penalty = messages.FloatField(6)

class UserForms(messages.Message):
    """Container for multiple User Forms"""
    items = messages.MessageField(UserForm, 1, repeated=True)


class NewGameForm(messages.Message):
    """Used to create a new game"""
    player_one = messages.StringField(1, required=True)
    player_two = messages.StringField(2, required=True)

class GameForm(messages.Message):
    """GameForm for outbound game state information"""
    urlsafe_key = messages.StringField(1, required=True)
    player_one = messages.StringField(2, required=True)
    player_two = messages.StringField(3, required=True)
    active = messages.StringField(4, required=True)
    draw_card = messages.StringField(5, required=True)
    mid_move = messages.BooleanField(6, required=True)
    game_over = messages.BooleanField(7, required=True)
    winner = messages.StringField(8)

class GameForms(messages.Message):
    """Container for multiple GameForm"""
    items = messages.MessageField(GameForm, 1, repeated=True)

class HandForm(messages.Message):
    """HandForm for outbound game state information"""
    urlsafe_key = messages.StringField(1, required=True)
    mid_move = messages.BooleanField(2, required=True)
    active = messages.StringField(3, required=True)
    hand = messages.StringField(4, required=True)
    draw_card = messages.StringField(5, required=True)
    instructions = messages.StringField(6, required=True)

class GameHistoryForm(messages.Message):
    """GameRecordForm for completed game information"""
    urlsafe_key = messages.StringField(1, required=True)
    player_one = messages.StringField(2, required=True)
    player_two = messages.StringField(3, required=True)
    game_over = messages.BooleanField(4, required=True)
    winner = messages.StringField(5)
    penalty_one = messages.IntegerField(6)
    penalty_two = messages.IntegerField(7)
    history = messages.StringField(8)


class MoveForm(messages.Message):
    """Used to start a move in an existing game"""
    user_name = messages.StringField(1, required=True)
    move = messages.StringField(2, required=True)


class ScoreForm(messages.Message):
    """ScoreForm for outbound Score information"""
    date = messages.StringField(1, required=True)
    winner = messages.StringField(2, required=True)
    loser = messages.StringField(3, required=True)

class ScoreForms(messages.Message):
    """Return multiple ScoreForms"""
    items = messages.MessageField(ScoreForm, 1, repeated=True)


class StringMessage(messages.Message):
    """StringMessage-- outbound (single) string message"""
    message = messages.StringField(1, required=True)
