# CPSC-449-Web Backend Engineering:Project-1

Guided by Professor: Kenytt Avery @ProfAvery

# Project description: 

This project involves creating two microservices: Users & Games for a Word game RESTful service. It consists of one Quart application connected to a  single SQLite Version 3 database.

The following are the steps to run the project:
1. Clone the github repository https://github.com/nickayson/CPSC-449-Project-1.git
2. Install the pip package manager and other tools by running the following commands
    > sudo apt update
    > sudo apt install --yes python3-pip
    > sudo apt install --yes python3-pip ruby-foreman sqlite3
3. Install Quart:
    > python3 -m pip install --upgrade quart[dotenv] click markupsafe Jinja2
4. Install async database support for SQLite:
    > python3 -m pip install databases[aiosqlite] SQLAlchemy==1.4.41
5. Install schema validation for Quart:
    > python3 -m pip install quart-schema

6. Then cd into the CPSC-449-Project-1 folder
    Run the following commands:     
    > foreman start   


Now, you will be to see that the one Quart application run on the port configured in the Procfile.
Now the API can be tested either using Postman(the method which we followed) or using curl or httpie.


