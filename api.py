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
    ScoreForms, GameForms, UserForm, UserForms, HandForm, GameHistoryForm
from utils import get_by_urlsafe, dealHand, testHand

NEW_GAME_REQUEST = endpoints.ResourceContainer(NewGameForm)
GET_GAME_REQUEST = endpoints.ResourceContainer(
        urlsafe_game_key=messages.StringField(1),)
MOVE_REQUEST = endpoints.ResourceContainer(
    MoveForm,
    urlsafe_game_key=messages.StringField(1),)
USER_REQUEST = endpoints.ResourceContainer(userName=messages.StringField(1),
                                           email=messages.StringField(2))


@endpoints.api(name='straightGin', version='v1')
class StraightGinAPI(remote.Service):
    """Game API"""

    @endpoints.method(request_message=USER_REQUEST,
                      response_message=StringMessage,
                      path='user',
                      name='createUser',
                      http_method='POST')
    def createUser(self, request):
        """Create User with unique username"""
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
        """Create new Game"""
        userA = User.query(User.name == request.userA).get()
        userB = User.query(User.name == request.userB).get()
        if not userA and userB:
            raise endpoints.NotFoundException(
                    'One of those users does not exist!')

        game = Game.newGame(userA.key, userB.key)
        return game.gameToForm()


    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=GameForm,
                      path='game/{urlsafe_game_key}',
                      name='getGame',
                      http_method='GET')
    def getGame(self, request):
        """
        Return the current Game state -
        without player hands for privacy purposes
        """
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game:
            return game.gameToForm()
        else:
            raise endpoints.NotFoundException('Game not found!')


    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=StringMessage,
                      path='game/{urlsafe_game_key}',
                      name='cancelGame',
                      http_method='DELETE')
    def cancelGame(self, request):
        """
        Deletes in-progress game.
        If the game is already completed, error thrown.
        """
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if not game:
            raise endpoints.NotFoundException('Game not found!')
        else:
            if game.gameOver == True:
                raise endpoints.BadRequestException('Game already over!')
            else:
                game.key.delete()
        return StringMessage(message='Game deleted!')


    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=HandForm,
                      path='game/{urlsafe_game_key}/hand',
                      name='getHand',
                      http_method='GET')
    def getHand(self, request):
        """Return the hand of active player"""
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
        """First half of move; return mid-move state of hand"""
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
            faceUpCard = game.faceUpCard
            hand += faceUpCard
            textMove = 'took FaceUpCard ' + str(game.faceUpCard)
            game.faceUpCard = ['']
        elif move == '2':
            drawCard, deck = dealHand(1, game.deck)
            # if there are still cards left in deck
            if drawCard != None:
                hand += drawCard
                textMove = 'took DrawCard ' + str(drawCard)
                game.deck = deck
            # but if out of cards, game automatically ends
            else:
                # check both players' hands
                penaltyA = testHand(game.userAHand)
                game.penaltyA = penaltyA
                penaltyB = testHand(game.userBHand)
                game.penaltyB = penaltyB
                if penaltyA < penaltyB:
                    game.end_game(game.userA)
                    if game.active == game.userA:
                        textMove = 'won with score of ' + str(penaltyA)
                    else:
                        textMove = 'lost with score of ' + str(penaltyA)
                elif penaltyB < penaltyA:
                    game.end_game(game.userB)
                    if game.active == game.userB:
                        textMove = 'won with score of ' + str(penaltyB)
                    else:
                        textMove = 'lost with score of ' + str(penaltyB)
                # tie goes to active player
                else:
                    game.end_game(game.active)
                    textMove = 'won with score of ' + str(penaltyA)
        else:
            raise endpoints.BadRequestException('Invalid move! Enter 1 to take '
                                        'face up card or 2 to draw from pile.')

        # Append move to the history
        game.history.append((user.name, textMove))

        if game.gameOver == False:
            game.midMove = True
            game.put()
            return game.handToForm()
        else:
            return game.gameToForm()


    @endpoints.method(request_message=MOVE_REQUEST,
                      response_message=GameForm,
                      path='game/{urlsafe_game_key}/endMove',
                      name='EndMove',
                      http_method='PUT')
    def endMove(self, request):
        """Second half of move"""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if not game:
            raise endpoints.NotFoundException('Game not found')
        if game.gameOver:
            raise endpoints.NotFoundException('Game already over')

        user = User.query(User.name == request.userName).get()
        if user.key != game.active:
            raise endpoints.BadRequestException('It\'s not your turn!')

        # get hand of current player
        active = ''
        if game.active == game.userA:
            hand = game.userAHand
            active = 'A'
        else:
            hand = game.userBHand
            active = 'B'

        move = request.move.split()

        # remove discard from hand and set as faceUpCard
        if not move[0] in hand:
            raise endpoints.BadRequestException('That card isn\'t in your hand! Enter your discard. If you are ready to go out, also type OUT. Example: D-K OUT')
        else:
            hand.remove(move[0])
            if game.faceUpCard != []:
                game.faceUpCard = []
            game.faceUpCard.append(''.join(move[0]))
            textMove = 'discards %s' % move[0]

            game.history.append((user.name, textMove))

            # reset flags
            if game.active == game.userA:
                game.active = game.userB
            elif game.active == game.userB:
                game.active = game.userA
            game.midMove = False

            # if player is going out
            if len(move) == 2:
                if move[1] == 'OUT':
                    penalty = testHand(hand)
                    # if penalty = 0, active player successfully went out
                    if penalty == 0:
                        game.endGame(game.active)
                        textMove = 'won with score of ' + str(penalty)
                        if active == 'A':
                            game.penaltyA = penalty
                            game.penaltyB = testHand(game.userBHand)
                        else:
                            game.penaltyB = penalty
                            game.penaltyA = testHand(game.userAHand)
                        game.history.append((game.active.get().name, textMove))
                    # otherwise active player UNsuccessfully went out, and automatically loses
                    # figure out who the active player is - other player wins
                    else:
                        if game.active != game.userA:
                            game.endGame(game.userA)
                            textMove = 'lost with score of ' + str(penalty)
                            game.penaltyB = penalty
                            game.penaltyA = testHand(game.userAHand)
                            game.history.append((game.userB.get().name, textMove))
                        else:
                            game.endGame(game.userB)
                            textMove = 'lost with score of ' + str(penalty)
                            game.penaltyA = penalty
                            game.penaltyB = testHand(game.userBHand)
                            game.history.append((game.userA.get().name, textMove))

        game.put()
        return game.gameToForm()


    @endpoints.method(request_message=USER_REQUEST,
                      response_message=GameForms,
                      path='user/games',
                      name='getUserGames',
                      http_method='GET')
    def getUserGames(self, request):
        """Return all of an individual User's active games"""
        user = User.query(User.name == request.userName).get()
        if not user:
            raise endpoints.NotFoundException(
                    'A User with that name does not exist!')
        games = Game.query(ndb.OR(Game.userA == user.key,
                                    Game.UserB == user.key))
        return GameForms(items=[game.gameToForm() for game in games])


    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=GameHistoryForm,
                      path='game/{urlsafe_game_key}/history',
                      name='getGameHistory',
                      http_method='GET')
    def getGameHistory(self, request):
        """Return the history and other details of a game"""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game:
            return game.gameRecordtoForm()
        else:
            raise endpoints.NotFoundException('Game not found!')


    @endpoints.method(response_message=ScoreForms,
                      path='scores',
                      name='getScores',
                      http_method='GET')
    def getScores(self, request):
        """Return all scores"""
        return ScoreForms(items=[score.scoreToForm() for score in Score.query()])


    @endpoints.method(request_message=USER_REQUEST,
                      response_message=ScoreForms,
                      path='scores/user/{userName}',
                      name='getUserScores',
                      http_method='GET')
    def getUserScores(self, request):
        """Return all of an individual User's scores"""
        user = User.query(User.name == request.userName).get()
        if not user:
            raise endpoints.NotFoundException(
                    'A User with that name does not exist!')
        scores = Score.query(ndb.OR(Score.winner == user.key,
                                    Score.loser == user.key))
        return ScoreForms(items=[score.scoreToForm() for score in scores])


    @endpoints.method(response_message=UserForms,
                      path='user/ranking',
                      name='getUserRankings',
                      http_method='GET')
    def getUserRankings(self, request):
        """Return UserForms, ranked by winning percentage"""
        users = User.query().fetch()
#       need to work on ordering ...
#        users.order()
        return UserForms(items=[user.userToForm() for user in users])

api = endpoints.api_server([StraightGinAPI])
