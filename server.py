import socket
import os
import select
import ntplib
import time
from pathlib import Path
from datetime import datetime, timedelta

class UDPServer:

    def __init__(self, server_address, server_port):
        self.server_address = server_address
        self.server_port = server_port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # クライアントがアクセスできるようにバインドする。
        self.sock.bind((self.server_address, self.server_port))
        # ノンブロッキングモードに設定。プログラムを途中で止めないようにする。
        self.sock.setblocking(0)
        # 接続してくるクライアントのリストを初期化
        self.clients = {}
        self.bufferSize = 4096  

    # NTPサーバーから正確な時刻を取得するメソッド。チャットは時刻順で表示させる必要がある。
    def get_ntp_time(self):
        # オブジェクトの作成
        client = ntplib.NTPClient()
        try:
            # pool.ntp.orgはNTPサーバーのこと。3はサーバーのバージョン
            response = client.request("ntp.nict.jp", version=3)
            # tx_timeはNTPサーバーから取得した時刻情報をUNIXタイムスタンプに変換。
            # fromtimestampはUNIXタイムスタンプを引数に、datetimeオブジェクトに変換。
            return datetime.fromtimestamp(response.tx_time)
        except Exception:
            print("時刻取得にエラーが発生しました\n")
            return datetime.now()

    def register_client(self, addr, user_name, time_stamp):
        # addressをKey、Valueにユーザー名とタイムスタンプを登録
        self.clients[addr] = {"name" : user_name, "time_stamp" : time_stamp}
        print(f"New client {user_name} registered.")
        try:
            # 登録されたクライアントに登録された旨を送信
            self.sock.sendto(f"REGISTERED {user_name}".encode(), addr)
        except Exception as e:
            print(str(e))

    # 現在時刻と比較し、10分以上やり取りがないクライアントを辞書から削除する
    def delete_expired_client(self):
        current_time = self.get_ntp_time()
        # 削除するために一時的な削除リストを作成
        # timedeltaはdatetime間の差について表現、分以外にも色々ある
        expired_clients = [addr for addr, info in self.clients.items() if current_time - info["time_stamp"] > timedelta(minutes = 10)]
        for addr in expired_clients:
            del self.clients[addr]

    def receive_data(self):
        try:
            # selectメソッドで作成したソケットを引数にセットし、使用可能かを読み取り、書き込み、例外のそれぞれで監視する。
            # タイムアウト時間を入れないとブロッキングモードになり、プログラムの操作を受け付けなくなる。
            readable, _, exceptional = select.select([self.sock], [], [self.sock], 1)

            if self.sock in readable:
                # 全クライアントからの送信データを到着順に受け付ける。
                data, addr = self.sock.recvfrom(self.bufferSize)

                user_name_length = data[0]
                user_name = data[1 : 1+user_name_length].decode()
                # 時刻が19文字になるので、それを含めて計算。
                # strptimeは文字列になっている時刻情報をdatetime型に変換する。
                time_stamp = datetime.strptime(data[1+user_name_length : 20+user_name_length].decode(), "%Y-%m-%d %H:%M:%S")
                message = data[20+user_name_length : ].decode()

                print(f"{user_name}, {time_stamp}, {message}")

                if addr not in self.clients:
                    self.register_client(addr, user_name, time_stamp)

                # データ送信者のリスト上のタイムスタンプを更新
                self.clients[addr]["time_stamp"] = time_stamp

                self.broadcast_data(addr, data)

            if self.sock in exceptional:
                print("ソケットにエラーが発生しました。")

        except Exception as e:
            print(str(e))

    # データ送信者以外の全クライアントにデータを転送する
    def broadcast_data(self, sender_addr, data):
        for client_addr in self.clients:
            if client_addr != sender_addr:
                try:
                    self.sock.sendto(data, client_addr)
                except Exception as e:
                    print(str(e))

    def run_server(self):
        try:
            while True:
                self.receive_data()
                self.delete_expired_client()
                
        except KeyboardInterrupt:
            print("サーバーを終了します\n")

        finally:
            self.sock.close()

if __name__ == "__main__":
    # 空文字は0.0.0.0と同じ。マシンとつながっている全クライアントのアクセスを受け付ける。
    server = UDPServer("", 9001)
    server.run_server()
    
