import socket
import ntplib
import time
from datetime import datetime
import threading

class UDPClient:

    # クライアントソケットのコンストラクタ
    def __init__(self, server_address, server_port):
        self.server_address = server_address
        self.server_port = server_port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # クライアントはbindする必要なし。
        # ノンブロッキングモードの設定
        self.sock.setblocking(False)
        self.print_lock = threading.Lock()
        self.running = True

    # NTPサーバー(日本)から現在時刻の取得
    def get_ntp_time(self):
        # NTPのオブジェクトを作成
        client = ntplib.NTPClient()
        try:
            # ntp.nict.jp=NTPサーバー、バージョンが3
            response = client.request("ntp.nict.jp", version=3)
            # tx_timeでntpサーバーの時刻をUNIXタイムスタンプに変換し、datetimeオブジェクトに変換 
            return datetime.fromtimestamp(response.tx_time)
        except Exception:
            print("時刻取得にエラーが発生しました\n")
            return datetime.now()

    # 入力メッセージの送信
    def send_data(self, user_name, message):
        user_name_length = len(user_name)
        time_stamp = datetime.strftime(self.get_ntp_time(), "%Y-%m-%d %H:%M:%S")

        try:
            # 数値をバイナリにするにはto_byteを使用する。引数は使用するバイト数とエンディアン形式を指定する。
            data = ( 
                user_name_length.to_bytes(1, "big") + 
                user_name.encode() + 
                time_stamp.encode() + 
                message.encode()
            ) 
            self.sock.sendto(data, (self.server_address, self.server_port))
        except Exception as e:
            print(str(e))

    # サーバーや他のユーザーからのメッセージ受信
    def receive_data(self):
        bufferSize = 4096

        while self.running:
            try:
                data, _ = self.sock.recvfrom(bufferSize)

                with self.print_lock:
                    # サーバーからのユーザー登録メッセージの処理
                    if data.decode().startswith("REGISTERED"):
                        print(f"\n {data.decode().split(' ')[1]} として登録されました。")
                        print("メッセージ：", end="", flush=True)
                    # 他ユーザーからのメッセージ受信処理
                    else:
                        remote_user_name_length = data[0]
                        remote_user_name = data[1:1+remote_user_name_length].decode()
                        remote_time_stamp = data[1+remote_user_name_length:20+remote_user_name_length].decode()
                        # 時刻情報が19文字なので、その後から指定する。
                        remote_message = data[20+remote_user_name_length:].decode()

                        time_only = remote_time_stamp.split(" ")[1] if " " in remote_time_stamp else remote_time_stamp
                        
                        print(f"\n{time_only} {remote_user_name}: {remote_message}")
                        print("メッセージ：", end="", flush=True)

            except BlockingIOError:
                time.sleep(0.1)
            except Exception as e:
                # もし、ユーザー自身がアプリから抜けた場合にはエラー出力する必要なし
                if self.running:
                    print(f"\n受信エラー: {e}") 
        
    def run_client(self):
        user_name = ""
        while not user_name or len(user_name) > 50:
            user_name = input("ユーザー名を入力してください。(50文字以内で設定してください)").strip()
            if not user_name:
                print("ユーザー名は必須です。")
            elif len(user_name) > 50:
                print("ユーザー名は50文字以内にしてください。")

        self.send_data(user_name, "")

        receive_message = threading.Thread(target=self.receive_data)
        receive_message.daemon = True
        receive_message.start()

        print("\nチャットを開始します。(「終了」でアプリ終了)")
        print("-" * 40)
        try:
            while True:
                    message = input("メッセージを入力してください\n")
                    if "終了" in message:
                        print("通信を切断します\n")
                        break
                    self.send_data(user_name, message)

        except KeyboardInterrupt:
            print("強制終了します\n")

        finally:
            self.running = False
            self.sock.close()

if __name__ == "__main__":
    server_address = input("サーバーアドレスを入力してください: ")
    server_port = 9001
    client = UDPClient(server_address, server_port)
    client.run_client()
