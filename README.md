# Full Stack Nanodegree Project 4 - Straight Gin
# Built by jennifer lyden on provided Tic-Tac-Toe template

## Synopsis
Back-end for Straight Gin card game with modifications described in Game Description below. Built for Google AppEngine - platform agnostic with support for variety of front-end clients.

##Game Description:
Straight Gin is a variation of the Gin Rummy card game. In the version implemented in this API, two players oppose each other in a single round. Players are dealt 10 cards each (but size of hand can be easily modified for a new game), and take turns drawing new cards trying to shape their hands into acceptable runs and sets, holding all cards in their hands until the end. When all cards in hand have been sorted into a run or set, a player can attempt to go "out." The first player to successfully go out wins. If a player attempts to go out, but the hand fails (not all cards belonging to a run or set), the opponent automatically wins. If neither player can go "out" before the deck runs out of cards to draw, whoever has the lowest penalty (cards NOT sorted into runs or sets) in their hand wins. Note that Aces (A) are LOW in Straight Gin (i.e. A = 1, never 14). Basic Gin Rummy instructions are available [here](https://en.wikipedia.org/wiki/Gin_rummy).

## Set-Up Instructions:
1. Download zip file and extract game files (see Files Included below).
2. Update the value of "application" in app.yaml to the app ID you have registered in the App Engine admin console.
3. Set up and run the app in Google App Engine Launcher.
4. Test API using localhost:8080/_ah/api/explorer (or whatever port # your localhost has available)
5. App is also currently running at http://straightgin-1234.appspot.com/_ah/api/explorer

##Files Included:
 - api.py: Contains endpoints and game play logic.
 - app.yaml: App configuration.
 - constants.py: Constants required by game (FULL_DECK, LIBRARY, HAND_SIZE).
 - cron.yaml: Cronjob configuration.
 - design.txt: Explanation of design decisions.
 - main.py: Handler for cronjobs and taskqueue.
 - models.py: Entity and Message definitions including helper methods.
 - README.md: This file.
 - utils.py: Contains helper functions:
    - get_by_urlsafe: retrieves ndb.Models using urlsafe key.
    - deal_hand: returns (1) "deal" of specified number of cards and (2) deck of remaining cards.
    - test_hand: verifies if all cards in a hand belong to runs or sets, and returns penalty if unused cards remain
    - clean_hand, group_consecutives, check_sets: helper functions for test_hand

## Testing Suggestions:
- You can easily change how many cards are dealt in a hand in constants.py. Big Hand = short game (but few players going "out" by choice).
- "new_game" and "end_move" report GAME status, not hand status (so that each player's hand remains private). Especially at the beginning of a game, each player should run "get_hand" to see cards in hand before running "start_move", so that player_one can make informed decision about taking visible draw_card ("1") or hidden deck card ("2").

##Endpoints Included:
 - **create_user**
    - Path: 'user'
    - Method: POST
    - Parameters: user_name
    - Returns: Message confirming creation of the User.
    - Description: Creates User with unique user_name. Raises ConflictException if User with user_name already exists.

 - **new_game**
    - Path: 'game'
    - Method: POST
    - Parameters: player_one, player_two
    - Returns: GameForm with neutral game state (no user hand displayed)
    - Description: Creates a new Game between player_one and player_two. Raises NotFoundException if either (or both) player does not exist.

 - **get_game**
    - Path: 'game/{urlsafe_game_key}'
    - Method: GET
    - Parameters: urlsafe_game_key
    - Returns: GameForm with current neutral game state (no user hand displayed)
    - Description: Returns the current state of a game, including active player and faceUpCard, but not active player's hand (in case opponent is looking). Raises NotFoundException if game doesn't exist.

 - **start_move**
    - Path: 'game/{urlsafe_game_key}/start-move'
    - Method: PUT
    - Parameters: urlsafe_game_key, user_name, move
    - Returns: HandForm with mid-move game state.
    - Description: Accepts a move (1 or 2) and returns the updated state of the game as displayed on "HandForm", including updated instructions. Active player must now select/input card to discard from his/her hand, and add "OUT" if ready to go out. Raises exceptions if game or user doesn't exist, game is mid-move already, game is already over, if it isn't that user's turn, or if user input is improper.

 - **end_move**
    - Path: 'game/{urlsafe_game_key}/end-move'
    - Method: PUT
    - Parameters: urlsafe_game_key, user_name, move
    - Returns: GameForm with new game state.
    - Description: Accepts a move (discarded card and, optionally, "OUT") and returns the updated state of the game on "GameForm" - new active player and new draw_card (which was just discarded). Raises exceptions if game or user doesn't exist, game is NOT mid-move, game is already over, if it isn't that user's turn, or if user tries to discard a card which doesn't exist in user's hand.

 - **get_scores**
    - Path: 'scores'
    - Method: GET
    - Parameters: None
    - Returns: ScoreForms.
    - Description: Returns all Scores in the database (unordered).

 - **get_user_scores**
    - Path: 'scores/user/{user_name}'
    - Method: GET
    - Parameters: user_name
    - Returns: ScoreForms.
    - Description: Returns all Scores recorded by the provided player (unordered). Raises NotFoundException if User does not exist.


##Additional endpoints
 - **cancel_game**
    - Path: 'game/{urlsafe_game_key}'
    - Method: DELETE
    - Parameters: urlsafe_game_key
    - Returns: StringMessage confirming deletion
    - Description: Deletes game-in-progress. Raises NotFoundException if game doesn't exist, and BadRequestException if the game already completed.

 - **get_hand**
    - Path: 'game/{urlsafe_game_key}/hand'
    - Method: GET
    - Parameters: urlsafe_game_key
    - Returns: HandForm with active player's hand and game state information
    - Description: Returns hand of player by user_name; if no user_name is provided, returns active player's hand. Also gives current draw_card and instructions for active player (whether pre-start_move or pre-end_move). Raises NotFoundException if game doesn't exist.

 - **get_game_history**
    - Path: 'game/{urlsafe_game_key}/history'
    - Method: GET
    - Parameters: urlsafe_game_key
    - Returns: GameHistoryForm presenting game history and other details.
    - Description: Returns game history, a stringified list of tuples reporting whether player took draw_card or deck card, then what the player discarded). Raises NotFoundException if game doesn't exist.

 - **get_game_score**
    - Path: 'game/{urlsafe_game_key}/game'
    - Method: GET
    - Parameters: urlsafe_game_key
    - Returns: ScoreForm associated with a particular game.
    - Description: Returns game score information, including winner and each player's penalties. Raises NotFoundException if game doesn't exist.

 - **get_user_games**
    - Path: 'user/games'
    - Method: GET
    - Parameters: userName
    - Returns: GameForms with 1 or more GameForm inside.
    - Description: Returns the current state of all the User's active games, with active games listed first.  Raises NotFoundException if user doesn't exist.

 - **get_user_rankings**
    - Path: 'user/rankings'
    - Method: GET
    - Parameters: None
    - Returns: UserForms
    - Description: Rank all players that have played at least one game by their winning percentage and return.

 - **get_high_scores**
    - Path: 'scores/high_scores'
    - Method: GET
    - Parameters: number_of_results (optional)
    - Returns: ScoreForms
    - Description: Returns ScoreForms ordered by winner's lowest penalty. If number_of_results provided, that number of results is returned; otherwise, all scores returned in order.


##Models Included:
 - **User**
    - Stores unique userName and (optional) email address.
    - Also keeps track of wins, total_games and win_rate.

 - **Game**
    - Stores unique game states & history.
    - Associated with User models via KeyProperties (player_one & player_two).

 - **Score**
    - Records completed games, including associated penalties.
    - Associated with User model via KeyProperty (winner & loser).
    - Associated with Game model via KeyProperty (game)


##Forms Included:
 - **UserForm**
    - Representation of User. Includes win_rate
 - **UserForms**
    - Container for one or more UserForm.
 - **NewGameForm**
    - Used to create a new game (player_one, player_two)
 - **GameForm**
    - Representation of a Game's state (urlsafe_key, player_one, player_two, active - player whose turn it is, draw_card, mid_move - boolean, game_over - boolean).
 - **GameForms**
    - Container for one or more GameForm.
 - **HandForm**
    - Representation of active player's hand (urlsafe_key, mid_move - boolean, active, hand - of active player, draw_card, instructions)
 - **GameHistoryForm**
    - Representation of Game with history (urlsafe_key, player_one, player_two, game_over, history - record of game moves)
 - **MoveForm**
    - Inbound move form (user_name, move).
 - **ScoreForm**
    - Representation of a completed game's Score (date, winner, loser, penalty_winner, penalty_loser).
 - **ScoreForms**
    - Multiple ScoreForm container.
 - **StringMessage**
    - General purpose String container.
