import socket
import os
from pathlib import Path

# create UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# 0.0.0.0 is accept any address
server_address = "0.0.0.0"
server_port = 9001

# 作成したソケットに自身のIP,PORTをbindする
sock.bind((server_address, server_port))

# クライアントのアドレスとユーザー名をkey, valueで保持
clients = {}

try:
    while True:
        # recvfrom method can accept all clients and data individually
        data, address = sock.recvfrom(4096)

        # 元々、PCが10進数を2進数で取り扱っているため、数値に変換しなくてOK
        user_name_length = data[0]
        user_name = data[1:1+user_name_length].decode()
        time_stamp = data[1+user_name_length:25+user_name_length].decode()
        message = data[25+user_name_length:].decode()
        print(f"{user_name_length}, {user_name}, {time_stamp}, {message}")

        # クライアント辞書に登録がなければ登録する
        if address not in clients:
            clients[address] = {"name" : user_name, "time_stamp" : time_stamp, "inactive_count" : 0}
            print("New client, {} registered.".format(user_name))
            registered_message = "REGISTERED " + user_name
            sock.sendto(registered_message.encode(), address)

        # データ送信してきたクライアントのタイムスタンプと削除候補からリセット
        clients[address]["time_stamp"] = time_stamp
        clients[address]["inactive_count"] = 0

        # 削除予定クライアントリストを作成し、削除候補回数が6以上のクライアントを追加する。
        inactive_clients = [addr for addr, info in clients.items() if info["inactive_count"] >= 6]

        # データ送信していない全クライアントについて削除候補に更新し、
        # もし、候補回数が6以上になったら、削除リストに追加する。
        # 満たしていなければ、受け取っているデータを転送する
        for client_address in clients.keys():
            if client_address != address:
                clients[client_address]["inactive_count"] += 1
                if client_address not in inactive_clients:
                    sock.sendto(data, client_address)

        # 削除予定リストによってリレーシステムから削除
        # UDPの場合、クライアントごとにソケットをつないでいる訳ではないため
        # クライアントリストから削除すればリレーシステムから除外される。
        for addr in inactive_clients:
            print(f"Client {clients[addr]['name']} was deleted due to inactivity.")
            del clients[addr]

except KeyboardInterrupt:
    print("サーバーを切断します。")

finally:
    sock.close()
    