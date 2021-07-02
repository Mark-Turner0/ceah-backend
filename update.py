import json
import urllib.request
import ssl
import re


def updateBrew():
    urls = [
            "https://formulae.brew.sh/api/formula.json",
            "https://formulae.brew.sh/api/cask.json"
            ]

    data = {}

    for url in urls:
        print("run", url)
        api_response = urllib.request.urlopen(url, context=ssl.SSLContext(ssl.PROTOCOL_TLS)).read().decode()
        api_response = json.loads(api_response)

        for i in api_response:
            try:
                data[i["name"].lower()] = i["versions"]["stable"]
            except KeyError:
                data[i["name"][0].lower()] = i["version"]
    return data


def complexVersionGet(latest_version):
    STABLE_RELEASE = "Q2804309"
    ALIASES = {
            "Q14116": "macos",
            "Q1406": "windows",
            "Q388": "linux"
            }
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
            context=ssl.SSLContext(ssl.PROTOCOL_TLS)
            ).read().decode()

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
    f = open("wikidata.json", 'r')
    data = f.read()
    f.close()
    data = json.loads(data)

    # UPDATE FROM WIKIPEDIA
    for i in data.keys():
        software = i.title() if i.islower() else i
        data[i] = versionGet(software.replace(' ', '_'))

    f = open("wikidata.json", 'w')
    f.write(json.dumps(data, indent='\t'))
    f.close()

    # UPDATE FROM BREW
    print("Updating brew versions...")
    data = updateBrew()
    f = open("brewdata.json", 'w')
    f.write(json.dumps(data, indent='\t'))
    f.close()


if __name__ == '__main__':
    main()
