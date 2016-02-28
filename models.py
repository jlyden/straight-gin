import random
from datetime import date
from protorpc import messages
from google.appengine.ext import ndb

FULL_DECK = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,
            21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,
            38,39,40,41,42,43,44,45,46]


class User(ndb.Model):
    """User profile"""
    name = ndb.StringProperty(required=True)
    email = ndb.StringProperty(required=True)
    wins = ndb.IntegerProperty(default=0)
    total_played = ndb.IntegerProperty(default=0)

    @property
    def win_percentage(self):
        if self.total_played > 0:
            return float(self.wins)/float(self.total_played)
        else:
            return 0

    def to_form(self):
        return UserForm(name=self.name,
                        email=self.email,
                        wins=self.wins,
                        total_played=self.total_played,
                        win_percentage=self.win_percentage)

    def add_win(self):
        """Add a win"""
        self.wins += 1
        self.total_played += 1
        self.put()

    def add_loss(self):
        """Add a loss"""
        self.total_played += 1
        self.put()


class Game(ndb.Model):
    """Game object"""
    deck = ndb.PickleProperty(required=True)
    userA = ndb.KeyProperty(required=True, kind='User')
    userB = ndb.KeyProperty(required=True, kind='User')
    userAHand = ndb.PickleProperty(required=True)
    userBHand = ndb.PickleProperty(required=True)
    userAPoints = ndb.IntegerProperty(required=True, default=0)
    userBPoints = ndb.IntegerProperty(required=True, default=0)
    deal = ndb.IntegerProperty(required=True, default=3) # Round - how many cards dealt
    midDeal = ndb.BooleanProperty(required=True, default=True) # Set to false at end of round
    notDealer = ndb.KeyProperty(required=True) # Goes first in round
    nextMove = ndb.KeyProperty(required=True) # The User whose turn it is
    faceUpCard = ndb.IntegerProperty(required=True) # Draw card showing
    gameOver = ndb.BooleanProperty(required=True, default=False)
    winner = ndb.KeyProperty()
    history = ndb.PickleProperty(required=True)

    @classmethod
    def new_game(cls, userA, userB):
        """Creates and returns a new game"""
        game = Game(userA=userA,
                    userB=userB,
                    deal=deal,
                    notDealer=userA,
                    nextMove=userA)

        # Prepare deck, hands, faceUpCard
        deck = FULL_DECK
        userAHand, deck = dealHand(3, deck)
        userBHand, deck = dealHand(3, deck)
        faceUpCard = turnFaceUpCard()

        # Set Game card values
        game.deck = deck
        game.userAHand = userAHand
        game.userBHand = userBHand
        game.faceUpCard = faceUpCard

        game.history = []
        game.put()
        return game

    def to_form(self):
        """Returns a GameForm representation of the Game"""
        form = GameForm(urlsafe_key=self.key.urlsafe(),
                        userA=self.userA.get().name,
                        userB=self.userA.get().name,
                        nextMove=self.next_move.get().name,
                        faceUpCard=self.faceUpCard,
                        deal=self.deal,
                        midDeal=self.midDeal,
                        userAPoints=self.userAPoints,
                        userBPoints=self.userBPoints,
                        gameOver=self.game_over)
        if self.winner:
            form.winner = self.winner.get().name
        return form

    def end_game(self, winner):
        """Ends the game"""
        self.winner = winner
        self.game_over = True
        self.put()
        loser = self.userB if winner == self.userA else self.userA
        # Add the game to the score 'board'
        score = Score(date=date.today(), winner=winner, loser=loser)
        score.put()

        # Update the user models
        winner.get().add_win()
        loser.get().add_loss()


class Score(ndb.Model):
    """Score object"""
    date = ndb.DateProperty(required=True)
    winner = ndb.KeyProperty(required=True)
    loser = ndb.KeyProperty(required=True)

    def to_form(self):
        return ScoreForm(date=str(self.date),
                         winner=self.winner.get().name,
                         loser=self.loser.get().name)


class GameForm(messages.Message):
    """GameForm for outbound game state information"""
    urlsafe_key = messages.StringField(1, required=True)
    userA = messages.StringField(2, required=True)
    userB = messages.StringField(3, required=True)
    nextMove = messages.StringField(4, required=True)
    faceUpCard = messages.StringField(5, required=True)
    deal = messages.IntegerField(6, required=True)
    midDeal = messages.BooleanField(7, required=True)
    userAPoints = messages.IntegerField(8, required=True)
    userBPoints = messages.IntegerField(9, required=True)
    gameOver = messages.BooleanField(10, required=True)
    winner = messages.StringField(11)


class GameForms(messages.Message):
    """Container for multiple GameForm"""
    items = messages.MessageField(GameForm, 1, repeated=True)

class NewGameForm(messages.Message):
    """Used to create a new game"""
    userA = messages.StringField(1, required=True)
    userB = messages.StringField(2, required=True)


class MakeMoveForm(messages.Message):
    """Used to make a move in an existing game"""
    user_name = messages.StringField(1, required=True)
    move = messages.IntegerField(2, required=True)


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


class UserForm(messages.Message):
    """User Form"""
    name = messages.StringField(1, required=True)
    email = messages.StringField(2)
    wins = messages.IntegerField(3, required=True)
    total_played = messages.IntegerField(4, required=True)
    win_percentage = messages.FloatField(5, required=True)


class UserForms(messages.Message):
    """Container for multiple User Forms"""
    items = messages.MessageField(UserForm, 1, repeated=True)


# move to api.py, then import to models.py
def dealHand(deal, deck):
    """
    Return list of integers of quantity "deal" and remaining integers in "deck"

    deal: positive integer
    deck: list of positive integers
    """
    hand = []
    try:
        for i in range(deal):
            card = random.choice(deck)
            hand.append(card)
            deck.remove(card)
        return hand, deck
    except IndexError:
        return None, [0]
