from database import getDB, pushDB, popDB, readDB
import json
import urllib.request
import ssl
import re
import sys
import os
from time import gmtime, strftime


def updateBrew():
    urls = [
        "https://formulae.brew.sh/api/formula.json",
        "https://formulae.brew.sh/api/cask.json"]

    data = {}

    for url in urls:
        api_response = urllib.request.urlopen(url, context=ssl.SSLContext(ssl.PROTOCOL_TLS)).read().decode()
        api_response = json.loads(api_response)

        for i in api_response:
            try:
                data[i["name"].lower()] = i["versions"]["stable"]
            except KeyError:
                data[i["name"][0].lower()] = i["version"]
    return data


def updatePacman():
    URL = "https://mirrors.gethosted.online/manjaro/repos/stable/"
    versions = {}

    for i in ["community", "extra", "core"]:
        os.system("curl " + URL + i + "/x86_64/" + i + ".db.tar.gz -O &>/dev/null")
        try:
            os.mkdir(i + ".db")
        except FileExistsError:
            pass
        os.system("tar -xf " + i + ".db.tar.gz -C " + i + ".db &>/dev/null")
        for j in os.listdir(i + ".db/"):
            f = open(i + ".db/" + j + "/desc")
            description = f.read()
            f.close()
            name = re.search("%NAME%\n(.*)", description).groups()[0]
            version = re.search("%VERSION%\n(.*)", description).groups()[0]
            versions[name.lower()] = version
    return versions


def updateChocolatey():
    versions = {}
    projects = [""]
    for start in projects:
        URL = "https://repology.org/api/v1/projects/" + start + "?newest=1&inrepo=chocolatey"
        api_response = urllib.request.urlopen(URL, context=ssl.SSLContext(ssl.PROTOCOL_TLS)).read().decode()
        api_response = json.loads(api_response)
        for i in api_response:
            final = i
            for j in range(len(api_response[i])):
                if api_response[i][j]["repo"] == "chocolatey":
                    versions[i] = api_response[i][j]["version"]
                    break
        if final + "/" != projects[-1]:
            projects.append(final + "/")
    return versions


def complexVersionGet(latest_version):
    STABLE_RELEASE = "Q2804309"
    ALIASES = {
        "Q14116": "macos",
        "Q1406": "windows",
        "Q388": "linux"}
    try:
        entity = re.search("\| ?(Q.*?)\|", latest_version).groups()[0]  # noqa: W605
    except AttributeError:
        print("No Q value found.")
        return False

    api_response = urllib.request.urlopen("https://www.wikidata.org/w/api.php?action=wbgetclaims&property=P348&format=json&rank=preferred&entity=" + entity,
                                          context=ssl.SSLContext(ssl.PROTOCOL_TLS)).read().decode()

    api_response = json.loads(api_response)["claims"]["P348"]
    for i in range(len(api_response)):
        if api_response[i]["qualifiers"]["P548"][0]["datavalue"]["value"]["id"] == STABLE_RELEASE:
            vers = {}
            try:
                for j in api_response[i]["qualifiers"]["P400"]:
                    vers[ALIASES[j["datavalue"]["value"]["id"]]] = api_response[i]["mainsnak"]["datavalue"]["value"]
            except KeyError:
                if i == len(api_response) - 1:
                    return api_response[i]["mainsnak"]["datavalue"]["value"]
                continue
    if len(vers) == 1:
        return list(vers.values())[0]
    return vers


def versionGet(software):
    try:
        api_response = urllib.request.urlopen(
            "https://en.wikipedia.org/w/index.php?action=raw&title=Template:Latest_stable_software_release/" + software,
            context=ssl.SSLContext(ssl.PROTOCOL_TLS)).read().decode()

    except urllib.error.HTTPError:

        try:
            api_response = urllib.request.urlopen(
                "http://en.wikipedia.org/w/index.php?action=raw&title=" + software,
                context=ssl.SSLContext(ssl.PROTOCOL_TLS)).read().decode()

        except urllib.error.HTTPError:
            return False

    if "{{Multiple releases" in api_response:
        latest_version = re.search("version1 ?= ?(.*)", api_response).groups()[0]
        if latest_version.startswith("{{"):
            return complexVersionGet(latest_version)
        return latest_version
    try:
        latest_version = re.search("latest.release.version ?= ?(.*)", api_response).groups()[0]
    except AttributeError:
        print("No Wikipedia page for", software)
        return False

    if latest_version.startswith("{{"):
        print(software)
        print(latest_version)
        return complexVersionGet(latest_version)

    latest_version = latest_version.split("<ref")[0]
    return latest_version


def main():

    db = getDB(sys.argv[1], sys.argv[2])

    # UPDATE FROM REPOLOGY
    print("Updating Chocolatey...`")
    currentdt = strftime("%d%m%H%M%S", gmtime())
    data = updateChocolatey()
    popDB(db["version_data"], data, "chocodata")
    pushDB(db["version_data"], data, currentdt, "chocodata")

    # UPDATE FROM WIKIPEDIA
    data = readDB(db, "wikidata")
    print("Updating Wikipedia versions...")
    currentdt = strftime("%d%m%H%M%S", gmtime())
    for i in data.keys():
        software = i.title() if i.islower() else i
        data[i] = versionGet(software.replace(' ', '_'))

    popDB(db["version_data"], data, "wikidata")
    pushDB(db["version_data"], data, currentdt, "wikidata")

    # UPDATE FROM BREW
    print("Updating brew versions...")
    currentdt = strftime("%d%m%H%M%S", gmtime())
    data = updateBrew()
    popDB(db["version_data"], data, "brewdata")
    pushDB(db["version_data"], data, currentdt, "brewdata")

    # UPDATE FROM PACMAN
    print("Updating pacman versions...")
    currentdt = strftime("%d%m%H%M%S", gmtime())
    data = updatePacman()
    popDB(db["version_data"], data, "pacmandata")
    pushDB(db["version_data"], data, currentdt, "pacmandata")


if __name__ == '__main__':
    main()
