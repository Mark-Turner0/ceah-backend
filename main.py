import socket
import json
import sys
import _thread as thread
from time import gmtime, strftime
from helpers import versionCmp, notif_parse, versionCmpOS, addNotif
from database import getDB, pushDB
import ssl


def communicate(conn, addr):
    data = conn.recv(4096).decode()
    try:
        assert data.startswith("SYN")
        print(data)
        unique = data[-7:]

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
            firewall = True
        except (socket.timeout, ConnectionRefusedError):
            print("Firewall / NAT detected.")
            firewall = False

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
            notif = addNotif(notif, "osVer")
        response["antivirus_scanning"] = data["antivirus_scanning"]
        response["firewall"] = data["firewall"]
        response["firewall_enabled"] = data["firewall_enabled"]
        response["firewall_rules"] = data["firewall_rules"]
        response["root"] = data["root"]
        response["UAC"] = data["UAC"]
        response["processes"] = data["processes"]
        response["notif"] = notif

        print(notification)

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
    server.bind(("0.0.0.0", 1701))
    server.listen(5)
    print("Listening...")
    sslserver = context.wrap_socket(server, server_side=True)
    while True:
        try:
            conn, addr = sslserver.accept()
            print("Inbound connection from", addr[0])
            thread.start_new_thread(communicate, (conn, addr))
        except (ConnectionResetError, ssl.SSLEOFError):
            continue


if __name__ == '__main__':
    main()
