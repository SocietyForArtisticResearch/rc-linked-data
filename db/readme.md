mongod --config mongod.conf
python3 rcData_API.py 

http://127.0.0.1:5000/query
http://127.0.0.1:5000/query?overall-score=0.8

## collections
mongosh
show databases
use [database name]
show collections
db.[collection name].find()

## collections
- research
- data
- metrics
- abstract

## queries
- editor type. Default page
- editor type as list
- statistics
- number of tools. filter for exposition with > n tools
