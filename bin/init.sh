#!/bin/sh

sqlite3 ./var/users.db < ./share/users.sql
sqlite3 ./var/game.db < ./share/game.sql
