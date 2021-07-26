import re
import sys
import ssl
import json
import urllib.request
import feedparser
from database import getDB, readDB


def compare(foundorig, installedorig):
    found = foundorig.split('-')[0]
    installed = installedorig.split('-')[0]
    found = found.split('.')
    installed = installed.split('.')
    for i in range(max(len(found), len(installed))):
        try:
            eval_installed = ''.join(filter(str.isnumeric, installed[i]))
        except IndexError:
            try:
                return True
            except IndexError:
                try:
                    return compare(foundorig.split('-')[1], installedorig.split('-')[1])
                except IndexError:
                    return False
        try:
            eval_found = ''.join(filter(str.isnumeric, found[i]))
        except IndexError:
            return False
        try:
            if int(eval_found) > int(eval_installed):
                return True
            elif int(eval_installed) > int(eval_found):
                return False
        except ValueError:
            try:
                return compare(foundorig.split('-')[1], installedorig.split('-')[1])
            except IndexError:
                return True
    try:
        found = foundorig.split('-')[1]
    except IndexError:
        return False
    try:
        installed = installedorig.split('-')[1]
    except IndexError:
        return True

    return compare(found, installed)


def search(term, oper):
    REPOS = {
        "windows": ["chocolatey"],
        "macos": ["homebrew", "homebrew_casks"],
        "linux": ["manjaro_stable"]}
    term = term.replace(' ', '-')
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
    # wiki = readDB(db["version_data"]["wikidata"])
    brew = readDB(db["version_data"]["brewdata"])
    pacman = readDB(db["version_data"]["pacmandata"])
    choco = readDB(db["version_data"]["chocodata"])

    if oper == "windows":
        return [choco, brew, pacman]
    elif oper == "macos":
        return [brew, pacman, choco]
    return [pacman, brew, choco]


def notif_parse(notification, unique):
    db = getDB(sys.argv[1], sys.argv[2])
    try:
        current = readDB(db[unique]["notif_data"])
    except IndexError:
        current = {}
    if notification is not False:
        try:
            current[notification[0]]
        except KeyError:
            current[notification[0]] = {
                "shown": 0,
                "clicked": 0,
                "dismissed": 0}
        current[notification[0]]["shown"] += 1
        if len(notification) > 1:
            current[notification[0]][notification[1]] += 1
    return current


def versionCmp(data, oper):
    order = getFiles(oper)
    newData = {}
    notif = {}

    for i in data.keys():
        if data[i] is False:
            print("Version number for", i, "could not be gathered.")
            continue
        latest = False
        for j in order:
            for k in j.keys():
                if i == k:
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
            for k in j.keys():
                if i.lower() in k.lower().split() or k.lower() in i.lower().split():
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
        if latest is False:
            latest = search(i, oper)
        if latest is False:
            newData[i] = False
        else:
            print(i, ":", latest, "compared to", data[i])
            if compare(latest, data[i]):
                newData[i] = latest
                notif = addNotif(notif, i)
                print(i)
            else:
                newData[i] = True

    return newData, notif

def versionCmpOS(oper, osVer):
    if oper == "macos":
        rss = feedparser.parse("https://developer.apple.com/news/releases/rss/releases.rss")["entries"]
        for i in rss:
            if "macOS" in i["title"] and "beta" not in i["title"]:
                latest = re.search("\((.*)\)", i["title"]).groups()[0]
                print(latest)
                if osVer != latest:
                    return False
                return True
        return True
    elif oper == "windows":
        rss = feedparser.parse("https://support.microsoft.com/en-us/feed/rss/6ae59d69-36fc-8e4d-23dd-631d98bf74a9")["entries"]
        for i in rss:
            if "OS Build" in i["title"] and "Preview" not in i["title"]:
                latest = re.search("(\d*\.\d*)", i["title"]).groups()
                print(latest)
                if osVer not in latest:
                    return False
                return True
        return True
    return True

def addNotif(notif, toAdd):
    db = getDB(sys.argv[1], sys.argv[2])
    known_correct = readDB(db["version_data"]["known_correct"])
    try:
        notif[toAdd] = known_correct[toAdd.replace(".", "-")]
    except KeyError:
        pass
    return notif
