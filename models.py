# models for StraightGinAPI
# AFTER TESTING, CHANGE HAND_SIZE

import constants
from utils import dealHand
from datetime import date
from protorpc import messages
from google.appengine.ext import ndb

# - - - - - Objects - - - - -

class User(ndb.Model):
    """User profile"""
    name = ndb.StringProperty(required=True)
    email = ndb.StringProperty(required=True)
    wins = ndb.IntegerProperty(default=0)
    totalPlayed = ndb.IntegerProperty(default=0)

    @property
    def winPercentage(self):
        if self.totalPlayed > 0:
            return float(self.wins)/float(self.totalPlayed)
        else:
            return 0.0

    def userToForm(self):
        return UserForm(name=self.name,
                        email=self.email,
                        wins=self.wins,
                        totalPlayed=self.totalPlayed,
                        winPercentage=self.winPercentage)

    def addWin(self):
        """Add a win"""
        self.wins += 1
        self.totalPlayed += 1
        self.put()

    def addLoss(self):
        """Add a loss"""
        self.totalPlayed += 1
        self.put()


class Game(ndb.Model):
    """Game object"""
    deck = ndb.PickleProperty(required=True)
    userA = ndb.KeyProperty(required=True, kind='User')
    userB = ndb.KeyProperty(required=True, kind='User')
    userAHand = ndb.PickleProperty(required=True)
    userBHand = ndb.PickleProperty(required=True)
    active = ndb.KeyProperty(required=True) # The User whose turn it is
    faceUpCard = ndb.PickleProperty(required=True) # Draw card showing
    midMove = ndb.BooleanProperty(required=True, default=False)
    instructions = ndb.StringProperty()
    gameOver = ndb.BooleanProperty(required=True, default=False)
    winner = ndb.KeyProperty()
    penaltyA = ndb.IntegerProperty()
    penaltyB = ndb.IntegerProperty()
    history = ndb.PickleProperty(required=True)

    @classmethod
    def newGame(cls, userA, userB):
        """Creates and returns a new game"""
        game = Game(userA=userA,
                    userB=userB,
                    active=userA)

        # Prepare deck, hands, faceUpCard
        deck = constants.FULL_DECK
        userAHand, deck = dealHand(constants.HAND_SIZE, deck)
        userBHand, deck = dealHand(constants.HAND_SIZE, deck)
        faceUpCard, deck = dealHand(1, deck)

        # Set Game card values
        game.deck = deck
        game.userAHand = userAHand
        game.userBHand = userBHand
        game.faceUpCard = faceUpCard

        # set up history
        textMove = 'starts'

        game.history = []
        game.history.append((userA.get().name, textMove))

        game.put()
        return game

    def gameToForm(self):
        """Returns a GameForm representation of the Game"""
        # convert faceUpCard to string
        stringCard = ' '.join(self.faceUpCard)

        form = GameForm(urlsafe_key=self.key.urlsafe(),
                        userA=self.userA.get().name,
                        userB=self.userB.get().name,
                        active=self.active.get().name,
                        faceUpCard=stringCard,
                        midMove=self.midMove,
                        gameOver=self.gameOver)
        if self.winner:
            form.winner = self.winner.get().name
        return form

    def handToForm(self):
        """Returns a HandForm representation active user's hand"""
        # If game is over, return history instead
        if self.gameOver:
            return self.gameHistorytoForm()
        else:
            # retrieve correct hand
            user = self.active
            if user == self.userA:
                hand = self.userAHand
            else:
                hand = self.userBHand

            # sort hand and convert to string
            sortHand = sorted(hand)
            stringHand = ' '.join(str(card) for card in sortHand)

            # convert faceUpCard to string
            stringCard = ' '.join(self.faceUpCard)

            # return proper instructions
            if self.midMove:
                instructions = 'Enter your discard. If you are ready to go out, also type OUT. Example: D-K OUT'
            else:
                instructions = 'Enter 1 to take face up card or 2 to draw from pile.'

            form = HandForm(urlsafe_key=self.key.urlsafe(),
                            midMove=self.midMove,
                            active=self.active.get().name,
                            hand=stringHand,
                            faceUpCard=stringCard,
                            instructions=instructions)
            return form

    def endGame(self, winner):
        """Ends the game"""
        self.winner = winner
        self.gameOver = True
        self.put()
        loser = self.userB if winner == self.userA else self.userA
        # Add the game to the score 'board'
        score = Score(date=date.today(), winner=winner, loser=loser)
        score.put()

        # Update the user models
        winner.get().addWin()
        loser.get().addLoss()

    def gameHistorytoForm(self):
        """
        Returns a GameHistoryForm representation of completed Game
        Assistance with list[tuples]->list[str]:
        http://stackoverflow.com/questions/11696078/python-converting-a-list-of-tuples-to-a-list-of-strings
        """
        historyList = ['%s %s' % x for x in self.history]
        history = '; '.join(str(move) for move in historyList)

        form = GameHistoryForm(urlsafe_key=self.key.urlsafe(),
                        userA=self.userA.get().name,
                        userB=self.userB.get().name,
                        gameOver=self.gameOver,
                        history=history)
        if self.winner:
            form.winner = self.winner.get().name
            form.penaltyA=self.penaltyA
            form.penaltyB=self.penaltyB
        return form


class Score(ndb.Model):
    """Score object"""
    date = ndb.DateProperty(required=True)
    winner = ndb.KeyProperty(required=True)
    loser = ndb.KeyProperty(required=True)

    def scoreToForm(self):
        return ScoreForm(date=str(self.date),
                         winner=self.winner.get().name,
                         loser=self.loser.get().name)


# - - - - - Forms - - - - -

class UserForm(messages.Message):
    """User Form"""
    name = messages.StringField(1, required=True)
    email = messages.StringField(2)
    wins = messages.IntegerField(3, required=True)
    totalPlayed = messages.IntegerField(4, required=True)
    winPercentage = messages.FloatField(5, required=True)

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
    active = messages.StringField(4, required=True)
    faceUpCard = messages.StringField(5, required=True)
    midMove = messages.BooleanField(6, required=True)
    gameOver = messages.BooleanField(7, required=True)
    winner = messages.StringField(8)

class GameForms(messages.Message):
    """Container for multiple GameForm"""
    items = messages.MessageField(GameForm, 1, repeated=True)

class HandForm(messages.Message):
    """HandForm for outbound game state information"""
    urlsafe_key = messages.StringField(1, required=True)
    midMove = messages.BooleanField(2, required=True)
    active = messages.StringField(3, required=True)
    hand = messages.StringField(4, required=True)
    faceUpCard = messages.StringField(5, required=True)
    instructions = messages.StringField(6, required=True)

class GameHistoryForm(messages.Message):
    """GameRecordForm for completed game information"""
    urlsafe_key = messages.StringField(1, required=True)
    userA = messages.StringField(2, required=True)
    userB = messages.StringField(3, required=True)
    gameOver = messages.BooleanField(4, required=True)
    winner = messages.StringField(5)
    penaltyA = messages.IntegerField(6)
    penaltyB = messages.IntegerField(7)
    history = messages.StringField(8)


class MoveForm(messages.Message):
    """Used to start a move in an existing game"""
    userName = messages.StringField(1, required=True)
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
