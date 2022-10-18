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


@app.route("/game/create-new-game", methods=["GET"])
async def newGame():
    db = await _get_db()
    words = await db.fetch_all("SELECT * FROM words")
    num = random.randrange(0, len(words), 1)

    userId = request.args.get("userId").lower()

    user = await db.fetch_one("SELECT * FROM userData WHERE id=:userId", values={"userId": userId})

    if not(user):
        return {"message": "Could not find this user"}, 404

    data = {"wordId": words[num][0], "userId": user[0]}

    id = await db.execute(
        """
        INSERT INTO game( wordId, userId)
        VALUES(:wordId, :userId)
        """,
        data)

    res = {"gameId": id, "guesses": 6}
    return res, 201


@app.route("/game/<int:gameId>/guess", methods=["POST"])
async def guess(gameId):
    db = await _get_db()

    body = await request.get_json()

    game = await db.fetch_one("SELECT * FROM game WHERE id=:id", values={"id": gameId})

    if not(game):
        return {"message": "Could not find a game with this id"}, 404

    userId = body.get("userId").lower()
    word = body.get("word")

    user = await db.fetch_one("SELECT * FROM userData WHERE id=:userId", values={"userId": userId})

    if not(user):
        return {"message": "Could not find this user"}, 404

    # Check if game is finished
    if game[4] == 1:
        return {"message": "Game is finished already"}, 400

    # Check if word is valid
    secretWord = await db.fetch_one("SELECT word FROM words WHERE id=:id", values={"id": game[2]})
    secretWord = secretWord[0]

    wordIsValid = True

    if len(word) != len(secretWord):
        wordIsValid = False

    if not(wordIsValid):
        return {"message": "Word is invalid", "valid": False}, 400

    # If word is valid
    # Check if correct word
    wordIsCorrect = word == secretWord

    # If word is correct
    if wordIsCorrect:
        return {"valid": True, "guess": True, "numGuesses": game[3]}

    # If word is not correct
    # Decrease guess count
    await db.execute("UPDATE game SET guesses=:numGuess, finished=:finished WHERE id=:id", 
        values={"numGuess": game[3] - 1, "id": game[0], "finished": 1 if game[3] - 1 <= 0 else 0})

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

    return {"valid": True, "guess": False, "numGuesses": game[3] - 1, "data": data}


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
    
    return {"gameId": game[0], "guesses": game[3], "finished": True if game[4] == 1 else False}

# game
# 0 = id
# 1 = userId
# 2 = wordId
# 3 = guesses
# 4 = finished