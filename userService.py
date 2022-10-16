import dataclasses
import databases
from quart import Quart, g, request, jsonify, abort
from werkzeug.security import generate_password_hash, check_password_hash
from quart_schema import validate_request, RequestSchemaValidationError
import sqlite3

app = Quart(__name__)

@dataclasses.dataclass
class userData:
    id: int
    username: str
    password: str

async def _get_db():
    db = getattr(g, "_sqlite_db", None)
    if db is None:
        db = g._sqlite_db = databases.Database('sqlite+aiosqlite:/user.db')
        await db.connect()
    return db

@app.teardown_appcontext
async def close_connection(exception):
    db = getattr(g, "_sqlite_db", None)
    if db is not None:
        await db.disconnect()

@app.route("/users/all", methods=["GET"])
async def all_users():
    db = await _get_db()
    all_users = await db.fetch_all("SELECT * FROM userData;")

    return list(map(dict, all_users))  

#Registering a new user
@app.route("/register/", methods=["POST"])
@validate_request(userData)
async def register_user(data):
    db = await _get_db()
    
    
    userData = dataclasses.asdict(data)   
    
    try:
        id = await db.execute(
            """
            INSERT INTO userData(id, username, password)
            VALUES(:id, :username, :password)
            """,
            userData,
        )
    except sqlite3.IntegrityError as e:
        abort(409, e)
    
    userData["id"] = id      
    return userData, 201, {"Location": f"/user/{id}"}

@app.errorhandler(RequestSchemaValidationError)
def bad_request(e):
    return {"error": str(e.validation_error)}, 400

@app.errorhandler(409)
def conflict(e):
    return {"error": str(e)}, 409

