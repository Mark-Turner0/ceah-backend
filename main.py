import socket
import json
import sys
import _thread as thread
from time import gmtime, strftime
from helpers import versionCmp
from database import getDB, pushDB
import ssl


def communicate(conn, addr):
    data = conn.recv(4096).decode()
    try:
        assert data.startswith("SYN")
        print(data)
        unique = data[-7:]
        response = "ACK " + unique
        print(response)

        conn.send(response.encode())
        olddata = conn.recv(4096).decode()
        currentdt = strftime("%d%m%H%M%S", gmtime())

        data = json.loads(olddata)
        conn.send(olddata.encode())
        assert conn.recv(4096).decode() == "ACK " + unique

        response, notif = versionCmp(data)
        toSend = json.dumps(response, indent='\t')
        conn.send(toSend.encode())
        assert conn.recv(4096).decode() == "ACK " + unique

        try:
            conn.send("\n".join(notif).encode())
        except ssl.SSLEOFError:
            conn.send("None".encode())
        assert conn.recv(4096).decode() == "ACK " + unique
        conn.send(str("FIN " + unique).encode())

        assert conn.recv(4096).decode() == "FIN ACK " + unique
        print("Connection with", unique, "completed successfully!")
        conn.close()

        print("Pushing to database...")
        db = getDB(sys.argv[1], sys.argv[2])
        try:
            pushDB(db[unique], data, currentdt, "collected_data")
            pushDB(db[unique], response, currentdt, "reply_data")
            pushDB(db[unique], notif, currentdt, "notif_data")
            print("Success!")
        except Exception as e:
            print("Error: ", e)

    except AssertionError:
        print("Connection to", addr[0], "dropped due to malformed packet.")
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
