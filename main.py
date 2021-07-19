import socket
import json
import sys
import _thread as thread
from time import gmtime, strftime
from helpers import versionCmp, notif_parse
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

        oper = data.pop("os")
        antivirus_scanning = data.pop("antivirus scanning")

        ip_addr = data.pop("ip_addr")
        firewall = data.pop("firewall")
        firewall_enabled = data.pop("firewall_enabled")
        root = data.pop("root")
        notification = data.pop("notification")
        try:
            firewall_rules = data.pop("firewall_rules")
        except KeyError:
            firewall_rules = False

        response, notif = versionCmp(data, oper)
        notification = notif_parse(notification, unique)

        response["os"] = oper
        response["antivirus scanning"] = antivirus_scanning
        response["ip_addr"] = ip_addr
        response["firewall"] = firewall
        response["firewall_enabled"] = firewall_enabled
        response["root"] = root
        response["notif"] = notif

        if firewall_rules:
            response["firewall_rules"] = firewall_rules

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
        conn, addr = sslserver.accept()
        print("Inbound connection from", addr[0])
        thread.start_new_thread(communicate, (conn, addr))


if __name__ == '__main__':
    main()
