import pymongo
import ssl


def getDB(username, password):

    CONNECTION_STRING = "mongodb+srv://" + username + ":" + password + "@cluster0.u4oou.mongodb.net/myFirstDatbase?retryWrites=true&w=majority"

    return pymongo.MongoClient(CONNECTION_STRING, ssl_cert_reqs=ssl.CERT_NONE)


def pushDB(db, data, currentdt, name):
    sanitdata = {"timestamp": currentdt}
    for i in data.keys():
        if type(data[i]) == dict:
            temp = {}
            for j in data[i].keys():
                temp[j.replace('.', '-')] = data[i][j]
            sanitdata[i.replace('.', '-')] = temp
        else:
            sanitdata[i .replace('.', '-')] = data[i]
    db[name].insert_one(sanitdata)


def readDB(db):
    data = db.find().limit(1).sort([("$natural", -1)])[0]
    data.pop("_id")
    data.pop("timestamp")
    return data


def popDB(db, data, unique):
    return db[unique].drop()
