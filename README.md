# About
This repository hosts source code in Python to obtain the [HUDOC database](http://hudoc.echr.coe.int)
of all decisions of the [European Court of Human Rights (ECHR)](http://www.echr.coe.int/Pages/home.aspx?p=home)
and create a local database of it (in sqlalchemy).

Formally, this code is able of downloading all the documents from the HUDOC to an SQL database and
build the citation network of them. A node is a document, a directed edge exists when a document cites another.
The code is restricted in obtaining edges from documents in English.
This procedure is tested (see `tests`).

To build the network, it uses the meta-data "Strasbourg Court law (scl)",
that contains (textual) references to other documents, and it uses data mining to translate each
reference into an unique document. This is done in an extremely reliable way: no known
false positives (add a link when it does not exist) and little (0.3% of all references) 
false negatives (not adding a link when it exist): of the ~70k links, currently <200 are not identified.
This procedure is heavily tested against human-made identifications (see `live_tests`).

# Requirements
Python 2.7 or 3 and pip. Install dependencies (sqlalchemy and alembic) using

    pip install requirements.txt

# Code
The code is divided in 2 main modules, `crawler.py` that contains the code to download the database from HUDOC,
and `create_network` that contains code to build the network from the database.

# Use

## Construct database
Currently this code only works against postgres.
Once the server is set up, change the code
of `run_crawler.engine` to use it (user, database and password).
Then, create a directory `_cache`, and run `run_crawler.py`. `_cache` stores copies of HUDOC webpages.

## Build network
To convert the references to the list of edges of a network of documents, run the script `run_create_network.py`
(that uses code on the module `create_network`). The network is populated in the database.

## Export the network
To export the database in SQL to a `json` file, run the code `run_export_network.py`.
It creates a file named `network.json` with entries with the following format:

    "001-100024": {
            "case_name": "HOVHANNISYAN AND SHIROYAN V. ARMENIA",
            "cases": [
                "5065/06"
            ],
            "references": [
                "001-93184",
                "001-57580",
                "001-58227",
                "001-58832",
                "001-57526",
                "001-57903",
                "001-59051"
            ],
            "year": 2010
        },

which you can easily parse to your favorite network package.

# Tests
This code is unit-tested. To run the tests for the crawler, run unittests against the directory `tests`.
To test the creation of the network from the references, run unittests against the directory `live_tests`
(after creating the database).

# Credits
This code was created in the Center of Excellence for International Courts ([icourts](http://jura.ku.dk/icourts/))
by [Jorge C. Leitão](jorgecarleitao.net).
