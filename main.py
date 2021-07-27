import socket
import json
import sys
import random
import _thread as thread
from time import gmtime, strftime
from helpers import versionCmp, notif_parse, versionCmpOS, addNotif, parseFirewall, parseUAC, parseProc, diff
from database import getDB, pushDB
import ssl


def communicate(conn, addr):
    data = conn.recv(4096).decode()
    try:
        assert data.startswith("SYN")
        print(data)
        unique = data[-10:]

        db = getDB(sys.argv[1], sys.argv[2])
        if unique not in db.list_database_names():
            raise ValueError

        response = "ACK " + unique
        print(response)
        conn.send(response.encode())

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(20)
        print("Attempting to connect...")
        try:
            s.connect((addr[0], 1701))
            print("No firewall detected.")
            firewall = False
        except (socket.timeout, ConnectionRefusedError):
            print("Firewall / NAT detected.")
            firewall = True

        olddata = ""
        while True:
            buff = conn.recv(4096).decode()
            if buff == "EOF":
                break
            olddata += buff
        currentdt = strftime("%d%m%H%M%S", gmtime())

        data = json.loads(olddata)
        conn.send(olddata.encode())
        conn.send("EOF".encode())
        assert conn.recv(4096).decode() == "ACK " + unique

        if data["ip_addr"] != addr[0] and not firewall:
            data["firewall"] = "NAT"
        else:
            data["firewall"] = firewall

        oper = data["os"]
        response = {}
        notification = notif_parse(data["notification"], unique)

        response["software"], notif = versionCmp(data["software"], oper)
        response["os"] = oper
        response["osVer"] = versionCmpOS(oper, data["osVer"])
        if not response["osVer"]:
            print("osVer failed")
            notif = addNotif(notif, "osVer")
        response["antivirus_scanning"] = data["antivirus_scanning"]
        if response["antivirus_scanning"] == "failed":
            print("Antivirus failed")
            notif = addNotif(notif, "antivirus_scanning")
        response["firewall"] = data["firewall"]
        response["firewall_enabled"] = data["firewall_enabled"]
        print("Firewall:", response["firewall"])
        if not response["firewall_enabled"] or not response["firewall"]:
            print("Firewall not enabled")
            notif = addNotif(notif, "firewall_enabled")
        response["firewall_rules"] = parseFirewall(data["firewall_rules"], oper)
        if not response["firewall_rules"] and response["firewall_enabled"]:
            print("Firewall misconfigured")
            notif = addNotif(notif, "firewall_rules")
        response["root"] = data["root"]
        if response["root"]:
            print("Running program as root/admin!")
            notif = addNotif(notif, "root")
        response["UAC"] = parseUAC(data["UAC"])
        response["processes"] = parseProc(data["processes"], db)
        if response["processes"] is not True:
            notif = addNotif(notif, "access controls", response["processes"])
            print("Access controls misconfigured")
        if not response["UAC"]:
            notif = addNotif(notif, "UAC")
            print("UAC misconfigured")

        changed = diff(db[unique], response)
        print(changed)
        try:
            pool = []
            for i in changed["software"].keys():
                if changed["software"][i] is True:
                    pool.append(i)
            software = random.choice(pool)
            print("Randomly chosen", software)
            notif = addNotif(notif, "positive", software)
        except KeyError:
            print("No new software.")
        except IndexError:
            print("None of the changed software has been updated")

        if "osVer" in changed and changed["osVer"] is True:
            notif = addNotif(notif, "positive", "osVer")
        if "firewall_enabled" in changed and changed["firewall_enabled"] is True:
            notif = addNotif(notif, "positive", "firewall_enabled")
        if "antivirus_scanning" in changed and changed["antivirus_scanning"] != "failed":
            notif = addNotif(notif, "positive", "antivirus_scanning")

        response["notif"] = notif
        toSend = json.dumps(response, indent='\t')
        conn.send(toSend.encode())
        conn.send("EOF".encode())
        assert conn.recv(4096).decode() == "ACK " + unique

        toSend = json.dumps(notif, indent='\t')
        conn.send(toSend.encode())
        conn.send("EOF".encode())
        assert conn.recv(4096).decode() == "ACK " + unique
        conn.send(str("FIN " + unique).encode())

        assert conn.recv(4096).decode() == "FIN ACK " + unique
        print("Connection with", unique, "completed successfully!")
        conn.close()

        print("Pushing to database...")
        try:
            pushDB(db[unique], data, currentdt, "collected_data")
            pushDB(db[unique], changed, currentdt, "diff_data")
            pushDB(db[unique], response, currentdt, "reply_data")
            pushDB(db[unique], notification, currentdt, "notif_data")
            print("Success!")
        except Exception as e:
            print("Error: ", e)

    except AssertionError:
        print("Connection to", addr[0], "dropped due to malformed packet.")
        conn.close()
    except ValueError:
        response = "KNACK " + unique
        print(response)
        conn.send(response.encode())
        conn.close()


def main():
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain('fullchain.pem', 'privkey.pem')

    server = socket.socket()
    while True:
        try:
            server.bind(("0.0.0.0", 1701))
            break
        except OSError:
            continue
    server.listen(5)
    print("Listening...")
    sslserver = context.wrap_socket(server, server_side=True)
    while True:
        try:
            conn, addr = sslserver.accept()
            print("Inbound connection from", addr[0])
            thread.start_new_thread(communicate, (conn, addr))
        except Exception:
            continue


if __name__ == '__main__':
    main()
