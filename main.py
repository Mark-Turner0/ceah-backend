import socket
import json
import os
import _thread as thread
from time import gmtime, strftime
from helpers import versionCmp


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
        print(data)
        data = json.loads(olddata)
        try:
            os.mkdir("data/" + unique)
            print("New user" + unique)
        except FileExistsError:
            pass
        currentdt = strftime("%d%m%H%M%S", gmtime())
        f = open("data/" + unique + "/" + currentdt + ".json", 'w')
        f.write(json.dumps(data, indent='\t'))
        f.close()
        conn.send(olddata.encode())
        assert conn.recv(4096).decode() == "ACK " + unique

        data, notif = versionCmp(data)
        toSend = json.dumps(data, indent='\t')
        f = open("data/" + unique + "/" + currentdt + "response.json", 'w')
        f.write(toSend)
        f.close()
        conn.send(toSend.encode())
        assert conn.recv(4096).decode() == "ACK " + unique

        conn.send("\n".join(notif).encode())
        assert conn.recv(4096).decode() == "ACK " + unique
        conn.send(str("FIN " + unique).encode())

        assert conn.recv(4096).decode() == "FIN ACK " + unique
        print("Connection with", unique, "completed successfully!")
        conn.close()

    except AssertionError:
        print("Connection to", addr[0], "dropped due to malformed packet.")
        conn.close()


def main():
    server = socket.socket()
    server.bind((socket.gethostname(), 1701))
    server.listen(5)
    print("Listening...")
    while True:
        conn, addr = server.accept()
        print("Inbound connection from", addr[0])
        thread.start_new_thread(communicate, (conn, addr))


if __name__ == '__main__':
    main()
