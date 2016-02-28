import logging
import endpoints
import random
from protorpc import remote, messages
from google.appengine.api import memcache
from google.appengine.ext import ndb
from google.appengine.api import taskqueue

from models import User, Game, Score
from models import StringMessage, NewGameForm, GameForm, MakeMoveForm,\
    ScoreForms, GameForms, UserForm, UserForms
from utils import get_by_urlsafe, check_winner, check_full

NEW_GAME_REQUEST = endpoints.ResourceContainer(NewGameForm)
GET_GAME_REQUEST = endpoints.ResourceContainer(
        urlsafe_game_key=messages.StringField(1),)
MAKE_MOVE_REQUEST = endpoints.ResourceContainer(
    MakeMoveForm,
    urlsafe_game_key=messages.StringField(1),)
USER_REQUEST = endpoints.ResourceContainer(user_name=messages.StringField(1),
                                           email=messages.StringField(2))


@endpoints.api(name='StraightGin', version='v1')
class StraightGinAPI(remote.Service):
    """Game API"""

    @endpoints.method(request_message=USER_REQUEST,
                      response_message=StringMessage,
                      path='user',
                      name='create_user',
                      http_method='POST')
    def create_user(self, request):
        """Create a User. Requires a unique username"""
        if User.query(User.name == request.user_name).get():
            raise endpoints.ConflictException(
                    'A User with that name already exists!')
        user = User(name=request.user_name, email=request.email)
        user.put()
        return StringMessage(message='User {} created!'.format(
                request.user_name))

    @endpoints.method(request_message=NEW_GAME_REQUEST,
                      response_message=GameForm,
                      path='game',
                      name='new_game',
                      http_method='POST')
    def new_game(self, request):
        """Creates new game"""
        userA = User.query(User.name == request.userA).get()
        userB = User.query(User.name == request.userB).get()
        if not userA and userB:
            raise endpoints.NotFoundException(
                    'One of users with that name does not exist!')

        game = Game.new_game(userA.key, userB.key)

        return game.to_form()

    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=GameForm,
                      path='game/{urlsafe_game_key}',
                      name='get_game',
                      http_method='GET')
    def getGame(self, request):
        """Return the current game state."""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game:
            return game.to_form()
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
            return game.hand_to_form()
        else:
            raise endpoints.NotFoundException('Game not found!')

    @endpoints.method(request_message=MAKE_MOVE_REQUEST,
                      response_message=GameForm,
                      path='game/{urlsafe_game_key}',
                      name='make_move',
                      http_method='PUT')
    def make_move(self, request):
        """Makes a move. Returns a game state with message"""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if not game:
            raise endpoints.NotFoundException('Game not found')
        if game.game_over:
            raise endpoints.NotFoundException('Game already over')

        user = User.query(User.name == request.user_name).get()
        if user.key != game.next_move:
            raise endpoints.BadRequestException('It\'s not your turn!')

        # Game logic goes here

        # Just a dummy signifier, what type of symbol is going down
        x = True if user.key == game.user_x else False

        move = request.move
        # Verify move is valid
        if move < 0 or move > 8:
            raise endpoints.BadRequestException('Invalid move! Must be between'
                                                '0 and 8')
        if game.board[move] != '':
            raise endpoints.BadRequestException('Invalid move!')

        game.board[move] = 'X' if x else 'O'
        # Append a move to the history
        game.history.append(('X' if x else 'O', move))
        game.next_move = game.user_o if x else game.user_x
        winner = check_winner(game.board)
        if not winner and check_full(game.board):
            # Just delete the game
            game.key.delete()
            raise endpoints.NotFoundException('Tie game, game deleted!')
        if winner:
           game.end_game(user.key)
        else:
            # Send reminder email
            taskqueue.add(url='/tasks/send_move_email',
                          params={'user_key': game.next_move.urlsafe(),
                                  'game_key': game.key.urlsafe()})
        game.put()
        return game.to_form()

    @endpoints.method(response_message=ScoreForms,
                      path='scores',
                      name='get_scores',
                      http_method='GET')
    def get_scores(self, request):
        """Return all scores"""
        return ScoreForms(items=[score.to_form() for score in Score.query()])

    @endpoints.method(request_message=USER_REQUEST,
                      response_message=ScoreForms,
                      path='scores/user/{user_name}',
                      name='get_user_scores',
                      http_method='GET')
    def get_user_scores(self, request):
        """Returns all of an individual User's scores"""
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException(
                    'A User with that name does not exist!')
        scores = Score.query(ndb.OR(Score.winner == user.key,
                                    Score.loser == user.key))
        return ScoreForms(items=[score.to_form() for score in scores])

api = endpoints.api_server([ThreeThirteenAPI])
