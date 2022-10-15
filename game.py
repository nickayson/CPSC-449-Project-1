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

    username = request.args.get("username").lower()

    user = await db.fetch_one("SELECT * FROM userData WHERE username=:username", values={"username": username})

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


@app.route("/game/guess/<int:gameId>", methods=["POST"])
async def guess(gameId):
    db = await _get_db()

    body = await request.get_json()

    game = await db.fetch_one("SELECT * FROM game WHERE id=:id", values={"id": gameId})

    if not(game):
        return {"message": "Could not find a game with this id"}, 404

    username = body.get("username").lower()
    word = body.get("word")

    user = await db.fetch_one("SELECT * FROM userData WHERE username=:username", values={"username": username})

    if not(user):
        return {"message": "Could not find this user"}, 404

    # TODO Check if game is finished


    # Check if word is valid
    wordIsValid = False

    if not(wordIsValid):
        return {"message": "Word is invalid", "valid": False}, 400

    # If word is valid

    # Check if correct word
    secretWord = await db.fetch_one("SELECT word from words WHERE id=:id", values={"id": game[2]})
    wordIsCorrect = word == secretWord

    # If word is correct
    if wordIsCorrect:
        return {"valid": True, "guess": True, "numGuesses": game[3]}

    # TODO If word is not correct

    # TODO Decrease guess count

    # TODO If guess count is 0, game is finished
    return {"valid": True, "guess": False}


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