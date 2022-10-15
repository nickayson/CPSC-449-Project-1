#export QUART_APP=UserService:app
UserService: python3 -m quart --bind=localhost:$PORT --debug --reload UserService --access-logfile - --error-logfile - --log-level DEBUG
game: hypercorn game --reload --debug --bind books.local.gd:$PORT --access-logfile - --error-logfile - --log-level DEBUG