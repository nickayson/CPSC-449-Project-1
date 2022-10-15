BEGIN TRANSACTION;
DROP TABLE IF EXISTS userData;
CREATE TABLE userData(id INTEGER PRIMARY KEY, username TEXT, _password TEXT);
INSERT INTO userData VALUES(1,'Debdyuti','deb@123');
INSERT INTO userData VALUES(2,'Nick','nick123$');
INSERT INTO userData VALUES(3,'john','goodpw');

DROP TABLE IF EXISTS words;
CREATE TABLE words(id INTEGER PRIMARY KEY, word TEXT);
INSERT INTO words VALUES(1,'apple');
INSERT INTO words VALUES(2,'peach');
INSERT INTO words VALUES(3,'bacon');
INSERT INTO words VALUES(4,'badge');
INSERT INTO words VALUES(5,'badly');
INSERT INTO words VALUES(6,'bagel');
INSERT INTO words VALUES(7,'baggy');
INSERT INTO words VALUES(8,'baker');

DROP TABLE IF EXISTS game;
CREATE TABLE game(
    id INTEGER PRIMARY KEY, 
    userId INTEGER,
    wordId INTEGER,
    guesses INTEGER DEFAULT 6,
    finished BIT DEFAULT 0,
    FOREIGN KEY(userId) REFERENCES userData(id), 
    FOREIGN KEY(wordId) REFERENCES words(id)
);

COMMIT;