import json


def getFiles(oper):
    f = open("wikidata.json")
    wiki = json.loads(f.read())
    f = open("brewdata.json")
    brew = json.loads(f.read())

    if oper == "windows":
        return [wiki, brew]
    elif oper == "macos":
        return [wiki, brew]
    return [wiki, brew]


def versionCmp(data):
    oper = data["os"]
    data.pop("os")
    data.pop("antivirus scanning")
    order = getFiles(oper)
    newData = {}
    notif = []
    f = open("known.txt", 'r')
    ood = [line.strip() for line in f]
    f.close()

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
                        latest = latest[oper]
                    break
            if latest:
                break
            first = False
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