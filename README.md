# Full Stack Nanodegree Project 4 - Straight Gin
# Built by jennifer lyden on provided Tic-Tac-Toe template


## Set-Up Instructions:
1. Update the value of application in app.yaml to the app ID you have registered in the App Engine admin console and would like to use to host your instance of this game.
2. Run the app with the devserver using dev_appserver.py DIR, and ensure it's running by visiting your local server's address (by default localhost:8080.)
3. Test API using localhost:8080/_ah/api/explorer 
 

##Game Description:
Straight Gin is a variation of Gin Rummy. In the version implemented in this API, two players oppose each other in a single round. Each player is dealt 10 cards, and takes turns drawing new cards trying to shape his/her hand into acceptable runs and sets, holding all cards in their hands until the end. When all cards have been sorted into a run or set, a player can attempt to go "out." The first player to successfully go out wins. If a player attempts to go out, but the hand fails (not all cards belong to a run or set), the opponent automatically wins. If neither player can go "out" before the deck runs out of cards to draw, whoever has the lowest penalty (cards NOT sorted into runs or sets) in their hand wins.  Basic Gin Rummy instructions are available [here](https://en.wikipedia.org/wiki/Gin_rummy).


##Files Included:
 - api.py: Contains endpoints and game playing logic.
 - app.yaml: App configuration.
 - constants.py: Constants required by game (FULL_DECK & LIBRARY).
 - cron.yaml: Cronjob configuration.
 - main.py: Handler for taskqueue handler.
 - models.py: Entity and message definitions including helper methods.
 - utils.py: Contains helper functions:
    - get_by_urlsafe: retrieves ndb.Models using urlsafe key.
    - dealHand: deals hands and draws single cards from deck.
    - testHand: verifies if all cards in a hand belong to runs or sets, and returns penalty if unused cards remain
    - cleanHand: used by testHand
    - group_consecutives: used by testHand
    - checkSets: used by testHand
    
--- NEED TO EDIT and ADD Endpoints
##Endpoints Included:
 - **createUser**
    - Path: 'user'
    - Method: POST
    - Parameters: user_name
    - Returns: Message confirming creation of the User.
    - Description: Creates a new User. user_name provided must be unique. Will 
    raise a ConflictException if a User with that user_name already exists.
    
 - **new_game**
    - Path: 'game'
    - Method: POST
    - Parameters: user_x, user_y
    - Returns: GameForm with initial game state.
    - Description: Creates a new Game. `user_x` and `user_o` are the names of the
    'X' and 'O' player respectively
     
 - **get_game**
    - Path: 'game/{urlsafe_game_key}'
    - Method: GET
    - Parameters: urlsafe_game_key
    - Returns: GameForm with current game state.
    - Description: Returns the current state of a game.
    
 - **make_move**
    - Path: 'game/{urlsafe_game_key}'
    - Method: PUT
    - Parameters: urlsafe_game_key, user_name, move
    - Returns: GameForm with new game state.
    - Description: Accepts a move and returns the updated state of the game.
    A move is a number from 0 - 8 corresponding to one of the 9 possible
    positions on the board.
    If this causes a game to end, a corresponding Score entity will be created,
    unless the game is tied - in which case the game will be deleted.
    
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
    - Description: Returns all Scores recorded by the provided player (unordered).
    Will raise a NotFoundException if the User does not exist.
    
 - **get_active_game_count**
    NOT IMPLEMENTED
    - Path: 'games/active'
    - Method: GET
    - Parameters: None
    - Returns: StringMessage
    - Description: Gets the average number of attempts remaining for all games
    from a previously cached memcache key.

    ##Additional endpoints
 - **get_user_games**
    - Path: 'user/games'
    - Method: GET
    - Parameters: user_name
    - Returns: GameForms with 1 or more GameForm inside.
    - Description: Returns the current state of all the User's active games.
    
 - **cancel_game**
    - Path: 'game/{urlsafe_game_key}'
    - Method: DELETE
    - Parameters: urlsafe_game_key
    - Returns: StringMessage confirming deletion
    - Description: Deletes the game. If the game is already completed an error
    will be thrown.
    
 - **get_user_rankings**
    - Path: 'user/ranking'
    - Method: GET
    - Parameters: None
    - Returns: UserForms
    - Description: Rank all players that have played at least one game by their
    winning percentage and return.

 - **get_game_history**
    - Path: 'game/{urlsafe_game_key}'
    - Method: GET
    - Parameters: urlsafe_game_key
    - Returns: StringMessage containing history
    - Description: Returns the move history of a game as a stringified list of 
    tuples in the form (square, symbol) eg: [(0, 'X'), (4, 'O')]
--- NEED TO EDIT and ADD Endpoints


##Models Included:
 - **User**
    - Stores unique user_name and (optional) email address.
    - Also keeps track of wins and total_played.
    - Possibly add average penalty?
    
 - **Game**
    - Stores unique game states. Associated with User models via KeyProperties
    userA and userB.
    
 - **Score**
    - Records completed games. Associated with Users model via KeyProperty as
    well.


##Forms Included:
 - **UserForm**
    - Representation of User. Includes winning percentage
 - **UserForms**
    - Container for one or more UserForm.
 - **NewGameForm**
    - Used to create a new game (userA, userB)
 - **GameForm**
    - Representation of a Game's state (urlsafe_key, userA, userB, active - player whose turn it is, gameOver, winner).
 - **GameForms**
    - Container for one or more GameForm.
 - **HandForm**
    - Representation of active player's hand (urlsafe_key, active, hand - of active player, faceUpCard - available to draw, instructions) 
 - **GameRecordForm**
    - Representation of complete Game (urlsafe_key, userA, userB, gameOver, winner, penaltyA, penaltyB, history - record of game moves)
 - **MakeMoveForm**
    - Inbound make move form (user_name, move).
 - **ScoreForm**
    - Representation of a completed game's Score (date, winner, loser).
 - **ScoreForms**
    - Multiple ScoreForm container.
 - **StringMessage**
    - General purpose String container.