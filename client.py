import socket
import ntplib
import time
import select

class UDPClient:

    def __init__(self, server_address, server_port):
        self.server_address = server_address
        self.server_port = server_port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # 空は0.0.0.0と同じ意味で、クライアント側でアクティブなネットワークにアクセスできる。
        # port番号を0にすると、OS側で自動で競合しないport番号を設定してくれる。
        self.sock.bind(("", 0))
        # ノンブロッキングモードの設定
        self.sock.setblocking(0)

    def get_ntp_time(self):
        # NTPのオブジェクトを作成
        client = ntplib.NTPClient()
        try:
            # pool.ntp.org=NTPサーバー、バージョンが3
            respose = client.request("pool.ntp.org", version=3)
            # timeモジュールからctimeで分かりやすい時刻表示に変更
            return time.ctime(respose.tx_time)
        except Exception as e:
            print(str(e))

    def send_data(self, user_name, message):
        user_name_length = len(user_name)
        time = self.get_ntp_time()

        try:
            self.sock.sendto(user_name_length.to_bytes(1, "big") + user_name.encode() + time.encode() + message.encode(), (self.server_address, self.server_port))
        except Exception as e:
            print(str(e))

    def receive_data(self):
        bufferSize = 4096

        readable, _, exceptional = select.select([self.sock], [], [self.sock], 1)

        if self.sock in readable:
            data, _ = self.sock.recvfrom(bufferSize)

            if data.decode().startswith("REGISTERED"):
                print(f"{data.decode().split(' ')[1]} として登録されました。")
            else:
                remote_user_name_length = data[0]
                remote_user_name = data[1:1+remote_user_name_length].decode()
                remote_message = data[25+remote_user_name_length:].decode()

                print(f"{remote_user_name}: {remote_message}")
        
        if self.sock in exceptional:
            print("ソケットにエラーが発生しました")

    def run_client(self):
        user_name = input("ユーザー名を入力してください")
        try:
            while True:
                    self.receive_data()
                    message = input("メッセージを入力してください")
                    if "out" in message:
                        print("close the connection.")
                        break
                    self.send_data(user_name, message)

        except KeyboardInterrupt:
            print("close the connection with server.")

        finally:
            self.sock.close()

if __name__ == "__main__":
    server_address = input("サーバーアドレスを入力してください")
    server_port = 9001
    client = UDPClient(server_address, server_port)
    client.run_client()

# sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# server_address = input("Enter server address: ")
# server_port = 9001

# # 0.0.0.0にアドレスを設定することにより、このクライアントのアクティブな
# # ネットワークインターフェースで受信することが可能になる。
# # port番号を0にすることで、osがほかのクライアントと衝突しない
# # port番号を設定してくれる。
# sock.bind(("", 0))

# def get_ntp_time():
#     client = ntplib.NTPClient()
#     try:
#         # pool.ntp.orgはntpサーバーの名前、サーバーのversionが3というもの
#         response = client.request("pool.ntp.org", version=3)
#         # timeモジュールのもので、分かりやすい時間表記に変更する
#         return time.ctime(response.tx_time)
#     except Exception as e:
#         return str(e)

# user_name = input("Enter your user name: ")
# user_name_length = len(user_name)
# first_message = input("Enter your first message: ")
# time_stamp = get_ntp_time()

# try:
#     # 数値もbinaryに変換しないとサーバーが受け取れない
#     sock.sendto(user_name_length.to_bytes(1, byteorder="big") + user_name.encode() + time_stamp.encode() + first_message.encode(), (server_address, server_port))
# except Exception as e:
#     print(str(e))

# bufferSize = 4096

# try:
#     while True:
#         readable, _, exceptional = select.select([sock], [], [sock], 1)

#         if sock in readable:
#             data, address = sock.recvfrom(bufferSize)

#             # もし、サーバーから新規登録通知が来たら、その旨を出力
#             if data.decode().startswith("REGISTERED"):
#                 print("You have been registered as:", data.decode().split(" ")[1])
#             else:
#                 remote_user_name_length = data[0]
#                 remote_user_name = data[1:1+remote_user_name_length].decode()
#                 # この間にタイムスタンプが24文字で含まれているため、そのあとからメッセージ取得
#                 remote_message = data[1+remote_user_name_length+25:].decode()

#                 print(f"{remote_user_name}: {remote_message}")


#         if sock in exceptional:
#             print("ソケットにエラーが発生しました。")
#             break

#         message = input("メッセージを入力してください。")
#         if "抜けます" in message:
#             break

#         time_stamp = get_ntp_time()
        
#         try:
#             sock.sendto(user_name_length.to_bytes(1, byteorder="big") + user_name.encode() + time_stamp.encode() + message.encode(), (server_address, server_port))
#         except Exception as e:
#             print(str(e))

# except KeyboardInterrupt:
#     print("通信を切断します。")
    
# finally:
#     sock.close()