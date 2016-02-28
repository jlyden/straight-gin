# API & game logic for StraightGinAPI

import logging
import endpoints
import random
from protorpc import remote, messages
from google.appengine.api import memcache
from google.appengine.ext import ndb
from google.appengine.api import taskqueue

from models import User, Game, Score
from models import StringMessage, NewGameForm, GameForm, MoveForm,\
    ScoreForms, GameForms, UserForm, UserForms, HandForm
from utils import get_by_urlsafe, dealHand, testHand

NEW_GAME_REQUEST = endpoints.ResourceContainer(NewGameForm)
GET_GAME_REQUEST = endpoints.ResourceContainer(
        urlsafe_game_key=messages.StringField(1),)
MOVE_REQUEST = endpoints.ResourceContainer(
    MoveForm,
    urlsafe_game_key=messages.StringField(1),)
USER_REQUEST = endpoints.ResourceContainer(userName=messages.StringField(1),
                                           email=messages.StringField(2))


@endpoints.api(name='StraightGin', version='v1')
class StraightGinAPI(remote.Service):
    """Game API"""

    @endpoints.method(request_message=USER_REQUEST,
                      response_message=StringMessage,
                      path='user',
                      name='createUser',
                      http_method='POST')
    def createUser(self, request):
        """Create a User. Requires a unique username"""
        if User.query(User.name == request.userName).get():
            raise endpoints.ConflictException(
                    'A User with that name already exists!')
        user = User(name=request.userName, email=request.email)
        user.put()
        return StringMessage(message='User {} created!'.format(
                request.userName))

    @endpoints.method(request_message=NEW_GAME_REQUEST,
                      response_message=GameForm,
                      path='game',
                      name='newGame',
                      http_method='POST')
    def newGame(self, request):
        """Creates new game"""
        userA = User.query(User.name == request.userA).get()
        userB = User.query(User.name == request.userB).get()
        if not userA and userB:
            raise endpoints.NotFoundException(
                    'One of those users does not exist!')

        game = Game.newGame(userA.key, userB.key)
        return game.toForm()

    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=GameForm,
                      path='game/{urlsafe_game_key}',
                      name='getGame',
                      http_method='GET')
    def getGame(self, request):
        """Return the current game state."""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game:
            return game.toForm()
        else:
            raise endpoints.NotFoundException('Game not found!')

    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=HandForm,
                      path='game/{urlsafe_game_key}/hand',
                      name='getHand',
                      http_method='GET')
    def getHand(self, request):
        """Return the hand of player whose turn it is."""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game:
            return game.handToForm()
        else:
            raise endpoints.NotFoundException('Game not found!')

    @endpoints.method(request_message=MOVE_REQUEST,
                      response_message=HandForm,
                      path='game/{urlsafe_game_key}/startMove',
                      name='startMove',
                      http_method='PUT')
    def startMove(self, request):
        """StartMove. Returns mid-move state."""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if not game:
            raise endpoints.NotFoundException('Game not found')
        if game.gameOver:
            raise endpoints.NotFoundException('Game already over')

        user = User.query(User.name == request.userName).get()
        if user.key != game.active:
            raise endpoints.BadRequestException('It\'s not your turn!')

        # get hand of current player
        if game.active == game.userA:
            hand = game.userAHand
        else:
            hand = game.userBHand

        # add card to user's hand & update deck (if needed)
        move = request.move.strip()
        textMove = ''
        if move == '1':
            hand.append(game.faceUpCard)
            game.faceUpCard = None
            textMove = 'FaceUpCard'
        elif move == '2':
            drawCard, deck = game.dealHand(1, game.deck)
            if drawCard != None:
                hand.append(drawCard)
                textMove = 'DrawCard'
                game.deck = deck
            # TODO else out of cards! game over
            else:
                # check both players' hands
                penaltyA = testHand(game.userAHand)
                penaltyB = testHand(game.userBHand)
                if penaltyA = None

        else:
            raise endpoints.BadRequestException('Invalid move! Enter 1 to take '
                                        'face up card or 2 to draw from pile.')

        # Append move to the history
        game.history.append((user.name, textMove))

        game.midMove = True

        game.put()
        return game.handToForm()


    @endpoints.method(request_message=MOVE_REQUEST,
                      response_message=HandForm,
                      path='game/{urlsafe_game_key}/endMove',
                      name='EndMove',
                      http_method='PUT')
    def endMove(self, request):
        """EndMove. Returns HandForm."""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if not game:
            raise endpoints.NotFoundException('Game not found')
        if game.gameOver:
            raise endpoints.NotFoundException('Game already over')

        user = User.query(User.name == request.userName).get()
        if user.key != game.active:
            raise endpoints.BadRequestException('It\'s not your turn!')

        # get hand of current player
        # are these pointers?
        if game.active == game.userA:
            hand = game.userAHand
        else:
            hand = game.userBHand

        move = request.move.split()

        # remove discard from hand and set as faceUpCard
        hand.remove(move[0])
        game.faceUpCard = move[0]
        textMove = 'Discard: %s' % move[0]

        game.history.append((user.name, textMove))

        # reset flags
        if game.active == game.userA:
            game.active == game.userB
        else:
            game.active == game.userA
        game.midMove = False

        # if player is going out
        if move[1]:
            # no clue - fill in logic later
            pass

        game.put()
        return game.Form()

    @endpoints.method(response_message=ScoreForms,
                      path='scores',
                      name='getScores',
                      http_method='GET')
    def getScores(self, request):
        """Return all scores"""
        return ScoreForms(items=[score.toForm() for score in Score.query()])

    @endpoints.method(request_message=USER_REQUEST,
                      response_message=ScoreForms,
                      path='scores/user/{userName}',
                      name='get_user_scores',
                      http_method='GET')
    def getUserScores(self, request):
        """Returns all of an individual User's scores"""
        user = User.query(User.name == request.userName).get()
        if not user:
            raise endpoints.NotFoundException(
                    'A User with that name does not exist!')
        scores = Score.query(ndb.OR(Score.winner == user.key,
                                    Score.loser == user.key))
        return ScoreForms(items=[score.toForm() for score in scores])

api = endpoints.api_server([StraightGinAPI])
