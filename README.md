# About
This repository hosts source code in Python to obtain the [database](http://hudoc.echr.coe.int) of cases of the 
[European Court of Human Rights](http://www.echr.coe.int/Pages/home.aspx?p=home) 
and create a local database of it (in sqlalchemy).

# Requirements
Python 2.7 or 3 and pip. Install dependencies (sqlalchemy) using

    pip install requirements.txt

# Use
Create a directory `_cache` and run the script `run_crawler.py`. The script downloads all cases from the chamber and
grand chamber and their respective text (in html).

# Credits
This code was created in the Center of Excellence for International Courts ([icourts](http://jura.ku.dk/icourts/)). 
