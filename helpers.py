import sys
import ssl
import json
import urllib.request
from database import getDB, readDB


def search(term, oper):
    REPOS = {
        "windows": ["chocolatey"],
        "macos": ["homebrew", "homebrew_casks"],
        "linux": ["manjaro_stable"]}
    for i in REPOS[oper]:
        url = "https://repology.org/api/v1/projects/?latest=1&search=" + term + "&inrepo=" + i
        api_response = urllib.request.urlopen(url, context=ssl.SSLContext(ssl.PROTOCOL_TLS)).read().decode()
        api_response = json.loads(api_response)
        try:
            for j in api_response[term]:
                if j["repo"] == i:
                    return j["version"]
        except KeyError:
            for j in api_response.keys():
                for k in api_response[j]:
                    if k["repo"] == i:
                        return k["version"]
    return False


def getFiles(oper):
    db = getDB(sys.argv[1], sys.argv[2])
    wiki = readDB(db, "wikidata")
    brew = readDB(db, "brewdata")
    pacman = readDB(db, "pacmandata")
    choco = readDB(db, "chocodata")

    if oper == "windows":
        return [choco, wiki, brew, pacman]
    elif oper == "macos":
        return [wiki, brew, pacman, choco]
    return [pacman, wiki, brew, choco]


def versionCmp(data):
    oper = data["os"]
    data.pop("os")
    data.pop("antivirus scanning")
    order = getFiles(oper)
    newData = {}
    notif = []
    db = getDB(sys.argv[1], sys.argv[2])
    ood = readDB(db, "known_correct")["array"]

    for i in data.keys():
        if data[i] is False:
            print("Version number for", i, "could not be gathered.")
            continue
        latest = False
        first = True
        for j in order:
            for k in j.keys():
                if (first and (k.lower() in i or i in k.lower())) or k == i:
                    print(k, "is in", i)
                    latest = j[k]
                    if type(latest) == dict:
                        try:
                            latest = latest[oper]
                        except KeyError:
                            latest = False
                    break
            if latest:
                break
            first = False
        if latest is False:
            latest = search(i, oper)
        if latest is False:
            newData[i] = False
        else:
            print(i, ":", latest, "compared to", data[i])
            if int(''.join(filter(str.isnumeric, latest))) > int(''.join(filter(str.isnumeric, data[i]))):
                newData[i] = latest
                print(i)
                if i in ood:
                    notif.append(i)
            else:
                newData[i] = True

    print(newData)
    return newData, notif
