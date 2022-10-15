import dataclasses
import databases
from quart import Quart, g, request, jsonify, abort
from werkzeug.security import generate_password_hash, check_password_hash
from quart_schema import validate_request
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



# #Authenticating the user

# @app.route('/login', methods=['POST'])
# async def autenticateUserCredentials():
#         query_parameters = request.form

#         username = await query_parameters.get('username')
#         password = await query_parameters.get('password')

#         db = _get_db()
#         #result = query_db('SELECT password FROM users WHERE username = ?', [username])
#         result=  db.fetch_one("SELECT password FROM userData WHERE username =:username", values={"username": username})

#         hashed_password = result[0].get('password')
#         validate_user = check_password_hash(hashed_password, password)    #checking if user entered password is equal to the hashed password in db
#         if validate_user:
#             return jsonify(validate_user)
#         else:
#             return jsonify({"statusCode": 401, "error": "Unauthorized", "message": "Login failed: Invalid username or password" })





# # Registering a new user

# @app.route('/register', methods=['POST'])
# async def registerUser():
#        query_parameters = request.form
#        id = query_parameters.get('id')
#        username = query_parameters.get('username')
#        password = query_parameters.get('password')
#        hashed_password = generate_password_hash(password, "sha256")

#        app.logger.info(username)

#        db = await _get_db()
#        count = db.fetch_one('SELECT COUNT(*) as count FROM userData WHERE id = ?', [id])
#        if(count[0].get('count') > 0):                             #returns 400 error if username already exists
#           return jsonify({"statusCode": 400, "error": "Bad Request", "message": "Username already taken"})
#        elif username== None or username=='' or password== None or password=='': #returns 400 error if either username or password or email are not provided.
#           return jsonify({"statusCode": 400, "error": "Bad Request", "message": "Invalid parameter(s)"})
#        else:                                                      #new user successful registration
#           db.execute('INSERT INTO userData (id, username, password) VALUES(?,?,?)',(id, username, hashed_password))
#           res = db.commit()
#           return jsonify({"statusCode": 200, "message": "You have successfully registered!"})




#Registering a new user
@app.route("/register/", methods=["POST"])
@validate_request(userData)
async def create_user(data):
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