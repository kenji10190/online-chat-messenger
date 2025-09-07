import socket
import ntplib
import time
from datetime import datetime
import threading

class UDPClient:

    def __init__(self, server_address, server_port):
        self.server_address = server_address
        self.server_port = server_port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # クライアントはbindする必要なし。
        # ノンブロッキングモードの設定
        self.sock.setblocking(0)
        self.running = True

    def get_ntp_time(self):
        # NTPのオブジェクトを作成
        client = ntplib.NTPClient()
        try:
            # pool.ntp.org=NTPサーバー、バージョンが3
            response = client.request("ntp.nict.jp", version=3)
            # timeモジュールからctimeで分かりやすい時刻表示に変更
            return datetime.fromtimestamp(response.tx_time)
        except Exception:
            print("時刻取得にエラーが発生しました\n")
            return datetime.now()

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

    def receive_data(self):
        bufferSize = 4096

        while self.running:
            try:
                data, _ = self.sock.recvfrom(bufferSize)

                if data.decode().startswith("REGISTERED"):
                    print(f"\n {data.decode().split(' ')[1]} として登録されました。")
                    print("メッセージ：", end="", flush=True)
                else:
                    remote_user_name_length = data[0]
                    remote_user_name = data[1:1+remote_user_name_length].decode()
                    # 時刻情報が19文字なので、その後から指定する。
                    remote_message = data[20+remote_user_name_length:].decode()

                    print(f"\r{" " * 50}\r", end="")
                    print(f"{remote_user_name}: {remote_message}")
                    print("メッセージ：", end="", flush=True)
            except BlockingIOError:
                time.sleep(0.1)      
            except Exception as e:
                # もし、ユーザー自身がアプリから抜けた場合にはエラー出力する必要なし
                if self.running:
                    print(f"\n受信エラー: {e}") 
        
    def run_client(self):
        user_name = input("ユーザー名を入力してください\n")
        self.send_data(user_name, "")

        receive_message = threading.Thread(target=self.receive_data())
        receive_message.daemon = True
        receive_message.start()

        print("\nチャットを開始します。(終了しますでアプリ終了)")
        print("-" * 40)
        try:
            while True:
                    message = input("メッセージを入力してください\n")
                    if "終了します" in message:
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
