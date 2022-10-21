# Science Fiction Novel API - Quart Edition
#
# Adapted from "Creating Web APIs with Python and Flask"
# <https://programminghistorian.org/en/lessons/creating-apis-with-python-and-flask>.
#

import collections
import dataclasses
import json
from pickle import FALSE
import sqlite3
import textwrap

import databases
import toml
import random

from quart import Quart, g, request, abort
from quart_schema import QuartSchema, RequestSchemaValidationError, validate_request

app = Quart(__name__)
QuartSchema(app)
app.config.from_file(f"./etc/{__name__}.toml", toml.load)


@dataclasses.dataclass
class Game:
    guesses: int
    wordId: int
    userId: int

async def _get_db():
    db = getattr(g, "_sqlite_db", None)
    if db is None:
        db = g._sqlite_db = databases.Database(app.config["DATABASES"]["URL"])
        await db.connect()
    return db


@app.teardown_appcontext
async def close_connection(exception):
    db = getattr(g, "_sqlite_db", None)
    if db is not None:
        await db.disconnect()

@app.route("/game/create-new-game", methods=["POST"])
async def newGame():
    db = await _get_db()

    body = await request.get_json()
    userId = body.get("userId")

    if not(userId):
        abort(400, "Please provide the user id")

    user = await db.fetch_one("SELECT * FROM userData WHERE id=:userId", values={"userId": userId})

    if not(user):
        abort(404, "Could not find user with this id")

    words = await db.fetch_all("SELECT * FROM correct")
    num = random.randrange(0, len(words), 1)

    data = {"wordId": words[num][0], "userId": user[0]}

    id = await db.execute(
        """
        INSERT INTO game(wordId, userId)
        VALUES(:wordId, :userId)
        """,
        data)

    res = {"gameId": id, "guesses": 6}
    return res, 201

@app.errorhandler(400)
def noUserId(msg):
    return {"error": str(msg).split(':', 1)[1][1:]}, 400

@app.errorhandler(404)
def userNotFound(msg):
    return {"error": str(msg).split(':', 1)[1][1:]}, 404

def getGuessState(guess, secret):
    word = guess
    secretWord = secret

    matched = []
    valid = []

    for i in range(len(secretWord)):
        correct = word[i] == secretWord[i]
        valid.append({"inSecret": correct, "wrongSpot": False, "used": True if correct else False})
        matched.append(correct)

    for i in range(len(secretWord)):
        currentLetter = secretWord[i]
        for j in range(len(secretWord)):
            if i != j:
                if not(matched[i]) and not(valid[j].get("used")):
                    if word[j] == currentLetter:
                        valid[j].update({"inSecret": True, "wrongSpot": True, "used": True})
                        matched[i] = True

    data = []
    index = 0

    for i in word:
        d = {}
        del valid[index]["used"]
        d[i] = valid[index]
        data.append(d)
        index += 1

    return data

async def gameStateToDict(game):
    db = await _get_db()
    secretWord = await db.fetch_one("SELECT word FROM correct WHERE id=:id", values={"id": game[2]})
    secretWord = secretWord[0]

    state = {"guessesLeft": game[3], "finished": game[4], "gussedWords": []}

    timeGuessed = 6 - game[3]
    guessedWords = []

    for i in range(timeGuessed):
        word = game[i + 5]
        wordState = {word: getGuessState(word, secretWord)}
        guessedWords.append(wordState)

    state["gussedWords"] = guessedWords

    return state

async def updateGameState(game, word, db, finished = 0):
    numGuesses = game[3]
    nthGuess = 6 - numGuesses + 1

    sql = "UPDATE game SET guesses=:numGuess, finished=:finished, "
    suffix = "guess" + str(nthGuess) + "=:guess" + " WHERE id=:id"

    gameFinished = finished
    if numGuesses - 1 == 0:
        gameFinished = 1
    await db.execute(sql + suffix, values={"numGuess": numGuesses - 1, "id": game[0], "finished": finished, "guess": word })


@app.route("/game/<int:gameId>/guess", methods=["PATCH"])
async def guess(gameId):
    db = await _get_db()

    body = await request.get_json()

    userId = body.get("userId").lower()
    word = body.get("word")

    if not(userId) or not(word):
        abort(400, "Please provide the user id and the guess word")

    game = await db.fetch_one("SELECT * FROM game WHERE id=:id", values={"id": gameId})

    # Check iff game exists
    if not(game):
        abort(404, "Could not find a game with this id")

    user = await db.fetch_one("SELECT * FROM userData WHERE id=:userId", values={"userId": userId})

    # Check if user exists
    if not(user):
        abort(404, "Could not find this user")

    # Check if game is finished
    if game[4] == 1:
        abort(400, "This game has already ended")

    # Check if word is valid
    if len(word) != 5:
        abort(400, "This is not a valid guess")

    wordIsValid = False

    # check if word is in correct table
    correct = await db.fetch_one("SELECT word FROM correct WHERE word=:word", values={"word": word})

    if not(correct):
        valid = await db.fetch_one("SELECT word FROM valid WHERE word=:word", values={"word": word})
        wordIsValid = valid is not None

    # invalid guess
    if not(wordIsValid) and not(correct):
        abort(400, "Guess word is invalid")

    # Not correct but valid
    secretWord = await db.fetch_one("SELECT word FROM correct WHERE id=:id", values={"id": game[2]})
    secretWord = secretWord[0]

    # guessed correctly
    if word == secretWord:
        await updateGameState(game, word, db, 1)

        return {"word": {"input": word, "valid": True, "correct": True}, 
        "numGuesses": game[3] - 1}

    await updateGameState(game, word, db, 0)

    data = getGuessState(word, secretWord)

    return {"word": {"input": word, "valid": True, "correct": False}, 
        "gussesLeft": game[3] - 1, 
        "data": data}

@app.errorhandler(400)
def noUserId(msg):
    return {"error": str(msg).split(':', 1)[1][1:]}, 400

@app.errorhandler(404)
def userNotFound(msg):
    return {"error": str(msg).split(':', 1)[1][1:]}, 404


@app.route("/user/<int:userId>/games", methods=["GET"])
async def myGames(userId):
    db = await _get_db()
    
    user = await db.fetch_one("SELECT * FROM userData WHERE id=:id", values={"id": userId})

    if not(user):
        return {"message": "Could not find this user"}, 404

    games = await db.fetch_all("SELECT * FROM game WHERE userId=:id", values={"id": userId})

    gamesList = list(map(dict, games))
    res = []

    for game in gamesList:
        res.append({"gameId": game.get("id"), "guesses": game.get("guesses"), "finished": True if game.get("finished") == 1 else False})

    return res

@app.route("/game/<int:gameId>", methods=["GET"])
async def getGame(gameId):
    db = await _get_db()

    game = await db.fetch_one("SELECT * FROM game WHERE id=:id", values={"id": gameId})

    if not(game):
        return {"message": "No game found with this id"}, 404
    
    return await gameStateToDict(game)
    # return {"gameId": game[0], "guesses": game[3], "finished": True if game[4] == 1 else False}

# game
# 0 = id
# 1 = userId
# 2 = wordId
# 3 = guesses
# 4 = finished
# 5 = guess1
# 6 = guess2
# 7 = guess3
# 8 = guess4
# 9 = guess5
# 10 = guess6