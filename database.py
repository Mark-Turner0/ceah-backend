import pymongo
import ssl


def getDB(username, password):

    CONNECTION_STRING = "mongodb+srv://" + username + ":" + password + "@cluster0.u4oou.mongodb.net/myFirstDatbase?retryWrites=true&w=majority"

    return pymongo.MongoClient(CONNECTION_STRING, ssl_cert_reqs=ssl.CERT_NONE)


def pushDB(db, data, currentdt, name):
    sanitdata = {"timestamp": currentdt}
    try:
        for i in data.keys():
            sanitdata[i.replace(".", "-")] = data[i]
        db[name].insert_one(sanitdata)
    except AttributeError:
        sanitdata["notified"] = data
        db[name].insert_one(sanitdata)


def readDB(db, name):
    data = db["version_data"][name].find()[0]
    data.pop("_id")
    data.pop("timestamp")
    return data


def popDB(db, data, unique):
    return db[unique].drop()
