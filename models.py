import random
from datetime import date
from protorpc import messages
from google.appengine.ext import ndb

FULL_DECK = ['H-A','H-2','H-3','H-4','H-5','H-6','H-7',
             'H-8','H-9','H-10','H-J','H-Q','H-K',
             'D-A','D-2','D-3','D-4','D-5','D-6','D-7',
             'D-8','D-9','D-10','D-J','D-Q','D-K',
             'C-A','C-2','C-3','C-4','C-5','C-6','C-7',
             'C-8','C-9','C-10','C-J','C-Q','C-K',
             'S-A','S-2','S-3','S-4','S-5','S-6','S-7',
             'S-8','S-9','S-10','S-J','S-Q','S-K']

# - - - - - Objects - - - - -

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
    nextMove = ndb.KeyProperty(required=True) # The User whose turn it is
    faceUpCard = ndb.StringProperty(required=True) # Draw card showing
    gameOver = ndb.BooleanProperty(required=True, default=False)
    winner = ndb.KeyProperty()
    history = ndb.PickleProperty(required=True)

    @classmethod
    def new_game(cls, userA, userB):
        """Creates and returns a new game"""
        game = Game(userA=userA,
                    userB=userB,
                    nextMove=userA)

        # Prepare deck, hands, faceUpCard
        deck = FULL_DECK
        userAHand, deck = dealHand(10, deck)
        userBHand, deck = dealHand(10, deck)
        faceUpCard = dealHand(1, deck)

        # Set Game card values
        game.deck = deck
        game.userAHand = userAHand
        game.userBHand = userBHand
        game.faceUpCard = faceUpCard

        game.history = []
        game.put()
        return game

    def dealHand(deal, deck):
        """
        Return list of strings of quantity "deal" and remaining strings in "deck"

        deal: positive integer
        deck: list of strings
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

    def to_form(self):
        """Returns a GameForm representation of the Game"""
        form = GameForm(urlsafe_key=self.key.urlsafe(),
                        userA=self.userA.get().name,
                        userB=self.userA.get().name,
                        nextMove=self.next_move.get().name,
                        faceUpCard=self.faceUpCard,
                        gameOver=self.game_over)
        if self.winner:
            form.winner = self.winner.get().name
        return form

    def hand_to_form(self):
        """Returns a HandForm representation nextMove user's hand"""
        # retrieve correct hand as list of ints
        user = self.next_move
        if user == self.userA:
            hand = userAHand
        else:
            hand = userBHand

        # convert sorted hand to string
        sortHand = sorted(hand)
        stringHand = ' '.join(sortHand)

        form = HandForm(urlsafe_key=self.key.urlsafe(),
                        nextMove=self.next_move.get().name,
                        hand=stringHand,
                        faceUpCard=self.faceUpCard)
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


# - - - - - Forms - - - - -

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


class NewGameForm(messages.Message):
    """Used to create a new game"""
    userA = messages.StringField(1, required=True)
    userB = messages.StringField(2, required=True)


class GameForm(messages.Message):
    """GameForm for outbound game state information"""
    urlsafe_key = messages.StringField(1, required=True)
    userA = messages.StringField(2, required=True)
    userB = messages.StringField(3, required=True)
    nextMove = messages.StringField(4, required=True)
    faceUpCard = messages.StringField(5, required=True)
    gameOver = messages.BooleanField(6, required=True)
    winner = messages.StringField(7)


class GameForms(messages.Message):
    """Container for multiple GameForm"""
    items = messages.MessageField(GameForm, 1, repeated=True)


class HandForm(messages.Message):
    """HandForm for outbound game state information"""
    urlsafe_key = messages.StringField(1, required=True)
    nextMove = messages.StringField(2, required=True)
    hand = messages.StringField(3, required=True)
    faceUpCard = messages.StringField(4, required=True)


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
