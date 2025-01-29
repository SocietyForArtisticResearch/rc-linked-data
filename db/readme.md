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

## Queries

Queries just return exposition numbers in certain order.

- queries by editor type in default page
- queries by editor type in any page of the exposition. So: give me all expositinos that have a block page (somewhere).
- filter and sort by tool type

- tool type (holistically), so sorting by multiple tool types at once
(audio, video, text)
(1,2,3) (10,2,0) (100,0,2)
