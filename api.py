# Full Stack Nanodegree Project 4 - Straight Gin
# Built by jennifer lyden on provided Tic-Tac-Toe template
#
# API & basic game logic for Straight_Gin_API

import logging
import endpoints
import random
from protorpc import remote, messages
from google.appengine.api import memcache
from google.appengine.api import taskqueue
from google.appengine.ext import ndb

from models import User, Game, Score
from models import UserForm, UserForms, NewGameForm, GameForm, GameForms, \
    HandForm, GameHistoryForm, MoveForm, ScoreForm, ScoreForms, StringMessage
from utils import get_by_urlsafe, deal_hand

NEW_GAME_REQUEST = endpoints.ResourceContainer(NewGameForm)
GET_GAME_REQUEST = endpoints.ResourceContainer(
    urlsafe_game_key=messages.StringField(1))
HIGH_SCORES_REQUEST = endpoints.ResourceContainer(
    number_of_results=messages.StringField(1, required=False))
MOVE_REQUEST = endpoints.ResourceContainer(
    MoveForm,
    urlsafe_game_key=messages.StringField(1),)
USER_GAME_REQUEST = endpoints.ResourceContainer(
    user_name=messages.StringField(1))
USER_REQUEST = endpoints.ResourceContainer(
    user_name=messages.StringField(1),
    email=messages.StringField(2))


@endpoints.api(name='gin', version='v1')
class StraightGinAPI(remote.Service):
    """ Game API """
    @endpoints.method(request_message=USER_REQUEST,
                      response_message=StringMessage,
                      path='user',
                      name='create_user',
                      http_method='POST')
    def create_user(self, request):
        """ Create User with unique user_name """
        # Check that user_name isn't already taken
        if User.query(User.name == request.user_name).get():
            raise endpoints.ConflictException(
                    'User with that name already exists!')
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
        """ Create new Game """
        # Make sure two players submitted in request exist
        player_one = User.query(User.name == request.player_one).get()
        player_two = User.query(User.name == request.player_two).get()
        if not player_one or not player_two:
            raise endpoints.NotFoundException(
                    'One of those users does not exist!')
        # Call new_game method
        game = Game.new_game(player_one.key, player_two.key)
        return game.game_to_form()

    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=StringMessage,
                      path='game/{urlsafe_game_key}/cancel',
                      name='cancel_game',
                      http_method='DELETE')
    def cancel_game(self, request):
        """ Delete game-in-progress """
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if not game:
            raise endpoints.NotFoundException('Game not found!')
        else:
            if game.game_over:
                raise endpoints.BadRequestException('Game already over!')
            else:
                game.key.delete()
                return StringMessage(message='Game deleted!')

    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=GameForm,
                      path='game/{urlsafe_game_key}',
                      name='get_game',
                      http_method='GET')
    def get_game(self, request):
        """ Return the current Game state without revealing player hands """
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game:
            return game.game_to_form()
        else:
            raise endpoints.NotFoundException('Game not found!')

    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=HandForm,
                      path='game/{urlsafe_game_key}/hand',
                      name='get_hand',
                      http_method='GET')
    def get_hand(self, request):
        """ Return hand of active player (whose turn it is) """
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if not game:
            raise endpoints.NotFoundException('Game not found!')
        else:
            return game.hand_to_form()

    @endpoints.method(request_message=MOVE_REQUEST,
                      response_message=HandForm,
                      path='game/{urlsafe_game_key}/start-move',
                      name='start_move',
                      http_method='PUT')
    def start_move(self, request):
        """ Return mid_move game state """
        # authorization check before proceeding
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if not game:
            raise endpoints.NotFoundException('Game not found')
        if game.game_over:
            raise endpoints.NotFoundException('Game already over')
        if game.mid_move:
            raise endpoints.BadRequestException("""Game is mid-move. \
                        "Get Hand", select discard, then "End Move".""")
        user = User.query(User.name == request.user_name).get()
        if user.key != game.active:
            raise endpoints.BadRequestException('Not your turn!')

        # get hand of current player
        if game.active == game.player_one:
            hand = game.hand_one
        else:
            hand = game.hand_two
        # add requested card to player's hand & update deck (if needed)
        move = request.move.strip()
        text_move = ''
        # if player takes visible draw_card, deck isn't affected
        if move == '1':
            hand += game.draw_card
            text_move = 'took visible card ' + ''.join(game.draw_card)
            game.history.append((user.name, text_move))
            game.draw_card = ['']
        # if player takes hidden card from deck, draw_card isn't affected
        elif move == '2':
            hidden_card, deck = deal_hand(1, game.deck)
            # if there are still cards left in deck, play continues
            if hidden_card is not None:
                hand += hidden_card
                text_move = 'took hidden card ' + ''.join(hidden_card)
                game.history.append((user.name, text_move))
                game.deck = deck
            # but if out of cards, game automatically ends
            else:
                game.end_game(self)
        # Handle bad input from user
        else:
            raise endpoints.BadRequestException('Invalid move! Enter 1 to \
                                take visible card or 2 to draw from pile.')
        # reset flag
        if not game.game_over:
            game.mid_move = True
            game.put()
        return game.hand_to_form()

    @endpoints.method(request_message=MOVE_REQUEST,
                      response_message=GameForm,
                      path='game/{urlsafe_game_key}/end-move',
                      name='end_move',
                      http_method='PUT')
    def end_move(self, request):
        """ Return game state """
        # authorization check before proceeding
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if not game:
            raise endpoints.NotFoundException('Game not found')
        if game.game_over:
            raise endpoints.NotFoundException('Game already over')
        if not game.mid_move:
            raise endpoints.BadRequestException("""You must "Start Move" \
                            before you end it! Try "Get Hand" to see active \
                            hand and instructions for next move.""")
        user = User.query(User.name == request.user_name).get()
        if user.key != game.active:
            raise endpoints.BadRequestException('Not your turn!')

        # get hand of current player
        if game.active == game.player_one:
            hand = game.hand_one
        else:
            hand = game.hand_two
        move = request.move.split()
        # verify user input
        if not move[0] in hand:
            raise endpoints.BadRequestException('That card is not in your \
                                hand! Enter your discard. If you are ready \
                                to go out, also type OUT. Example: D-K OUT')
        # remove discard from hand and set as draw_card
        else:
            hand.remove(move[0])
            game.draw_card = []
            game.draw_card.append(''.join(move[0]))
            text_move = 'discards %s' % move[0]
            game.history.append((user.name, text_move))

            # if player chooses to go "OUT", end game
            if len(move) == 2:
                if move[1] == 'OUT' or move[1] == 'out':
                    game.end_game(True)
            # other input from user is ignored

            # reset flags
            if not game.game_over:
                if game.active == game.player_one:
                    game.active = game.player_two
                elif game.active == game.player_two:
                    game.active = game.player_one
                game.mid_move = False
                game.put()
            return game.game_to_form()

    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=GameHistoryForm,
                      path='game/{urlsafe_game_key}/history',
                      name='get_game_history',
                      http_method='GET')
    def get_game_history(self, request):
        """ Return history of a game """
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game:
            return game.history_to_form()
        else:
            raise endpoints.NotFoundException('Game not found!')

    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=ScoreForm,
                      path='game/{urlsafe_game_key}/score',
                      name='get_game_score',
                      http_method='GET')
    def get_game_score(self, request):
        """ Return the ScoreForm for Score associated with a Game """
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game:
            score = Score.query(Score.game == game.key).get()
            return score.score_to_form()
        else:
            raise endpoints.NotFoundException('Game not found!')

    @endpoints.method(request_message=USER_GAME_REQUEST,
                      response_message=GameForms,
                      path='user/games',
                      name='get_user_games',
                      http_method='GET')
    def get_user_games(self, request):
        """ Return all of an individual User's games """
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException(
                    'User with that name does not exist!')
        # Get all games, then order with NOT game_over first
        q = user.all_games()
        games = q.order(Game.game_over)
        return GameForms(items=[game.game_to_form() for game in games])

    @endpoints.method(response_message=ScoreForms,
                      path='scores',
                      name='get_scores',
                      http_method='GET')
    def get_scores(self, request):
        """ Return all Scores in database """
        return ScoreForms(items=[score.score_to_form()
                          for score in Score.query()])

    @endpoints.method(request_message=USER_GAME_REQUEST,
                      response_message=ScoreForms,
                      path='scores/user/{user_name}',
                      name='get_user_scores',
                      http_method='GET')
    def get_user_scores(self, request):
        """ Return all of an individual User's scores """
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException(
                    'User with that name does not exist!')
        scores = user.all_scores()
#        scores = Score.query(ndb.OR(Score.winner == user.key,
#                                    Score.loser == user.key))
        return ScoreForms(items=[score.score_to_form() for score in scores])

    @endpoints.method(response_message=UserForms,
                      path='user/ranking/win_rate',
                      name='get_user_rankings',
                      http_method='GET')
    def get_user_rankings(self, request):
        """ Return UserForms ranked by win_rate """
        q = User.query()
#        users = q.order(User.win_rate)
        return UserForms(items=[user.user_to_form() for user in users])

    @endpoints.method(request_message=HIGH_SCORES_REQUEST,
                      response_message=ScoreForms,
                      path='scores/high_scores',
                      name='get_high_scores',
                      http_method='GET')
    def get_high_scores(self, request):
        """ Return ScoreForms ranked by lowest winner penalty """
        q = Score.query()
        scores = q.order(Score.penalty_winner)
        return ScoreForms(items=[score.score_to_form() for score in scores])

api = endpoints.api_server([StraightGinAPI])
