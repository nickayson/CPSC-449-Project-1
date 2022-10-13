PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE userData(one int primary key, two text, three text);
INSERT INTO userData VALUES(1,'Debdyuti','deb@123');
INSERT INTO userData VALUES(2,'Nick','nick123$');
COMMIT;
