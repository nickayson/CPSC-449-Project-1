import dataclasses
import collections
from this import d
from operator import itemgetter
import databases
from quart import Quart, g, request, jsonify, abort
from werkzeug.security import generate_password_hash, check_password_hash
from quart_schema import validate_request, RequestSchemaValidationError
import sqlite3
import toml

app = Quart(__name__)

@dataclasses.dataclass
class userData:
    id: int
    username: str
    password: str

@dataclasses.dataclass
class loginData:    
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


#------------Registering a new user-----------------#

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
    return jsonify({"statusCode": 200, "message": "Successfully registered!"})

@app.errorhandler(RequestSchemaValidationError)
def bad_request(e):
    return {"error": str(e.validation_error)}, 400

@app.errorhandler(409)
def conflict(e):
    return {"error": str(e)}, 409

@app.errorhandler(401)
def unauthorized(e):
    return {"error": str(e)}, 401


SearchParam = collections.namedtuple("SearchParam", ["name", "operator"])
SEARCH_PARAMS = [
    
    SearchParam(
        "username",
        "=",
    ),
    SearchParam(
        "password",
        "=",
    ),
    
]

#-------------Authenticating the credentials for Login----------------
@app.route('/login', methods=['POST'])
@validate_request(loginData)
async def authenticate(data):
    query_parameters = request.args
    db = await _get_db()   
    
    loginData= dataclasses.asdict(data)   
    
    sql = "SELECT username,password FROM userData"
    conditions = []
    values = {}

    for param in SEARCH_PARAMS:
        if query_parameters.get(param.name):
            if param.operator == "=":
                conditions.append(f"{param.name} = :{param.name}")
                values[param.name] = query_parameters[param.name]               

    if conditions:
        sql += " WHERE "
        sql += " AND ".join(conditions)

    app.logger.debug(sql)

    db = await _get_db()
    results = await db.fetch_all(sql, values)    
    
    my_list= list(map(dict, results))    
    pwd = list(map(itemgetter('password'), my_list))
    name = list(map(itemgetter('username'), my_list))    
   
    result_dict= {}

    for key in name:
         for value in pwd:
             result_dict[key] = value
             pwd.remove(value)
             break      
    
    for key in result_dict:
        if(loginData['password']==result_dict[key] and loginData['username']==key  ) :        
            return jsonify({"statusCode": 200, "authenticated": "true"})   
     
    return jsonify({"statusCode": 401, "error": "Unauthorized", "message": "Login failed !" })     
   
    
   
   