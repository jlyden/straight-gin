# Full Stack Nanodegree Project 4 - Straight Gin
# Built by jennifer lyden on provided Tic-Tac-Toe template


## Set-Up Instructions:
1. Update the value of application in app.yaml to the app ID you have registered in the App Engine admin console and would like to use to host your instance of this game.
2. Set up and run the app in Google App Engine Launcher.
3. Test API using localhost:8080/_ah/api/explorer 

## Testing Recommendation:
You can easily change how many cards are dealt in a hand under constants.py. Big Hand = short game (but few players going "out").

##Game Description:
Straight Gin is a variation of Gin Rummy. In the version implemented in this API, two players oppose each other in a single round. Each player is dealt 10 cards, and takes turns drawing new cards trying to shape his/her hand into acceptable runs and sets, holding all cards in their hands until the end. When all 10 cards have been sorted into a run or set, a player can attempt to go "out." The first player to successfully go out wins. If a player attempts to go out, but the hand fails (not all cards belonging to a run or set), the opponent automatically wins. If neither player can go "out" before the deck runs out of cards to draw, whoever has the lowest penalty (cards NOT sorted into runs or sets) in their hand wins.  Basic Gin Rummy instructions are available [here](https://en.wikipedia.org/wiki/Gin_rummy). Note that Aces (A) are LOW in Straight Gin (i.e. A = 1, never 14)


##Files Included:
 - api.py: Contains endpoints and game playing logic.
 - app.yaml: App configuration.
 - constants.py: Constants required by game (FULL_DECK & LIBRARY).
 - cron.yaml: Cronjob configuration.
 - main.py: Handler for taskqueue handler.
 - models.py: Entity and message definitions including helper methods.
 - utils.py: Contains helper functions:
    - get_by_urlsafe: retrieves ndb.Models using urlsafe key.
    - dealHand: deals hands (as many cards as specified); also used to draw single card from deck during gameplay.
    - testHand: verifies if all cards in a hand belong to runs or sets, and returns penalty if unused cards remain
    - cleanHand: used by testHand
    - group_consecutives: used by testHand
    - checkSets: used by testHand
    
--- NEED TO EDIT and ADD Endpoints
##Endpoints Included:
 - **createUser**
    - Path: 'user'
    - Method: POST
    - Parameters: userName
    - Returns: Message confirming creation of the User.
    - Description: Creates a new User. userName provided must be unique. Will 
    raise a ConflictException if a User with that userName already exists.
    
 - **newGame**
    - Path: 'game'
    - Method: POST
    - Parameters: userA, userB
    - Returns: GameForm with neutral game state (no user hand displayed)
    - Description: Creates a new Game between `userA` and `userB`
     
 - **getGame**
    - Path: 'game/{urlsafe_game_key}'
    - Method: GET
    - Parameters: urlsafe_game_key
    - Returns: GameForm with current neutral game state (no user hand displayed)
    - Description: Returns the current state of a game, including active player and faceUpCard, but not active player's hand (in case opponent is looking)
    
 - **getHand**
    - Path: 'game/{urlsafe_game_key}/hand'
    - Method: GET
    - Parameters: urlsafe_game_key
    - Returns: HandForm with active player's hand and game state information
    - Description: Returns the active player's hand, plus current faceUpCard and instructions to startMove - player enters 1 to take faceUpCard or 2 to take hidden card from deck

 - **startMove**
    - Path: 'game/{urlsafe_game_key}/startMove'
    - Method: PUT
    - Parameters: urlsafe_game_key, userName, move
    - Returns: HandForm with new game state.
    - Description: Accepts a move (1 or 2) and returns the updated state of the game as displayed on "HandForm", including updated instructions. Active player must now select/input card to discard from his/her hand, and add "OUT" if ready to go out.
    
 - **endMove**
    - Path: 'game/{urlsafe_game_key}/endMove'
    - Method: PUT
    - Parameters: urlsafe_game_key, userName, move
    - Returns: GameForm with new game state.
    - Description: Accepts a move (discarded card and, optionally, "OUT") and returns the updated state of the game on "GameForm" - new active player and new faceUpCard (that discard).
    
 - **getScores**
    - Path: 'scores'
    - Method: GET
    - Parameters: None
    - Returns: ScoreForms.
    - Description: Returns all Scores in the database (unordered).
    
 - **getUserScores**
    - Path: 'scores/user/{userName}'
    - Method: GET
    - Parameters: userName
    - Returns: ScoreForms. 
    - Description: Returns all Scores recorded by the provided player (unordered).
    Will raise a NotFoundException if the User does not exist.
    

##Additional endpoints
 - **getUserGames**
    - Path: 'user/games'
    - Method: GET
    - Parameters: userName
    - Returns: GameForms with 1 or more GameForm inside.
    - Description: Returns the current state of all the User's active games.
    
 - **cancelGame**
    - Path: 'game/{urlsafe_game_key}'
    - Method: DELETE
    - Parameters: urlsafe_game_key
    - Returns: StringMessage confirming deletion
    - Description: Deletes the game. If the game is already completed an error
    will be thrown.
    
 - **getUserRankings**
    - Path: 'user/ranking'
    - Method: GET
    - Parameters: None
    - Returns: UserForms
    - Description: Rank all players that have played at least one game by their
    winning percentage and return.

 - **getGameHistory**
    - Path: 'game/{urlsafe_game_key}/history'
    - Method: GET
    - Parameters: urlsafe_game_key
    - Returns: GameHistoryForm presenting game history and other details.
    - Description: Returns game history, a stringified list of tuples reporting whether player took faceUpCard or deck card, then what the player discarded), plus completed game details if game is over (winner plus relevent penalties).


##Models Included:
 - **User**
    - Stores unique userName and (optional) email address.
    - Also keeps track of wins and total_played.
    
 - **Game**
    - Stores unique game states. Associated with User models via KeyProperties
    userA and userB.
    
 - **Score**
    - Records completed games. Associated with Users model via KeyProperty.


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
 - **GameHistoryForm**
    - Representation of Game with history, and if completed, winner and penalties (urlsafe_key, userA, userB, gameOver, winner, penaltyA, penaltyB, history - record of game moves)
 - **MakeMoveForm**
    - Inbound make move form (userName, move).
 - **ScoreForm**
    - Representation of a completed game's Score (date, winner, loser).
 - **ScoreForms**
    - Multiple ScoreForm container.
 - **StringMessage**
    - General purpose String container.