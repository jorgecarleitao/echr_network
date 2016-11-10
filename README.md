# About
This repository hosts source code in Python to obtain the [HUDOC database](http://hudoc.echr.coe.int) of all decisions of the 
[European Court of Human Rights (ECHR)](http://www.echr.coe.int/Pages/home.aspx?p=home) 
and create a local database of it (in sqlalchemy).

Formally, this code is able of downloading all the documents from the HUDOC to an SQL database and 
build the citation network of them. A node is a document, a directed edge exists when a document cites another.
The code is restricted in obtaining edges from documents in English.
This procedure is tested (see tests).

To build the network it uses the meta-data "Strasbourg Court law (scl)", 
that contains (textual) references to other documents, and data mining to translate each reference into an unique document.
This is done in an extremely reliable way: no known 
false positives (add a link when it does not exist) and little (99.6% of all references) 
false negatives (not adding a link when it exist): of the ~70k links, currently <300 are not identified.
This procedure is heavily tested against human-made identifications (see live_tests). 

# Requirements
Python 2.7 or 3 and pip. Install dependencies (sqlalchemy and alembic) using

    pip install requirements.txt

# Code
The code is divided in 2 main modules, `crawler.py` that contains the code to download the database from HUDOC,
and `create_network` that contains code to build the network from the database.

# Use

## Construct database
First, you need to decide which SQL database backend you want.
By default, it is set to postgres (see `run_crawler.py`). Once it is set up, change the code 
of `run_crawler.engine` to use it (engine, user, database and password). 
Then, create a directory `_cache`, and run `run_crawler.py`. `_cache` will store caches of HUDOC webpages.

## Build network
To convert the references to the list of edges of a network of documents, run the script `run_create_network.py` (
that uses code on the module `create_network`). This will create a file `network.json` with the network. 

# Tests
This code is unit-tested. Run unittests against the directory `tests` to test crawler.
Run unittests against the directory `live_tests` after you have the database to test the creation of the network.

# Credits
This code was created in the Center of Excellence for International Courts ([icourts](http://jura.ku.dk/icourts/)). 
