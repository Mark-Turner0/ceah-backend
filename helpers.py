import sys
import ssl
import json
import urllib.request
from database import getDB, readDB


def compare(foundorig, installedorig):
    found = foundorig.split('-')[0]
    installed = installedorig.split('-')[0]
    found = found.split('.')
    installed = installed.split('.')
    for i in range(len(found)):
        try:
            eval_installed = ''.join(filter(str.isnumeric, installed[i]))
        except IndexError:
            try:
                return compare(foundorig.split('-')[1], installedorig.split('-')[1])
            except IndexError:
                return True
        try:
            eval_found = ''.join(filter(str.isnumeric, found[i]))
        except IndexError:
            return False
        try:
            if int(eval_found) > int(eval_installed):
                try:
                    return compare(foundorig.split('-')[1], installedorig.split('-')[1])
                except IndexError:
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
    # wiki = readDB(db, "wikidata")
    brew = readDB(db, "brewdata")
    pacman = readDB(db, "pacmandata")
    choco = readDB(db, "chocodata")

    if oper == "windows":
        return [choco, brew, pacman]
    elif oper == "macos":
        return [brew, pacman, choco]
    return [pacman, brew, choco]


def versionCmp(data):
    oper = data.pop("os")
    antivirus_scanning = data.pop("antivirus scanning")
    ip_addr = data.pop("ip_addr")
    firewall = data.pop("firewall")
    firewall_enabled = data.pop("firewall_enabled")
    root = data.pop("root")
    try:
        firewall_rules = data.pop("firewall_rules")
    except KeyError:
        firewall_rules = False
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
                print(i)
                if i in ood:
                    notif.append(i)
            else:
                newData[i] = True

    newData["os"] = oper
    newData["antivirus scanning"] = antivirus_scanning
    newData["ip_addr"] = ip_addr
    newData["firewall"] = firewall
    newData["firewall_enabled"] = firewall_enabled
    newData["root"] = root

    if firewall_rules:
        newData["firewall_rules"] = firewall_rules

    print(newData)
    return newData, notif
