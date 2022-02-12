import pymongo
from dotenv import dotenv_values

config = dotenv_values(".env")

myclient = pymongo.MongoClient(config["MONGO_URI"])

newtrialdatabase = myclient["newtrialdatabase"]

newtrialcollection = newtrialdatabase["newtrialcollection"]

mydict = { "name": "John", "address": "Highway 37" }

x = newtrialcollection.insert_one(mydict)

