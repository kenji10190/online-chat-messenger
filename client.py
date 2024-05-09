import socket
import ntplib
import time
import select

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

server_address = input("Enter server address: ")
server_port = 9001

# 0.0.0.0にアドレスを設定することにより、このクライアントのアクティブな
# ネットワークインターフェースで受信することが可能になる。
# port番号を0にすることで、osがほかのクライアントと衝突しない
# port番号を設定してくれる。
sock.bind(("", 0))

def get_ntp_time():
    client = ntplib.NTPClient()
    try:
        # pool.ntp.orgはntpサーバーの名前、サーバーのversionが3というもの
        response = client.request("pool.ntp.org", version=3)
        # timeモジュールのもので、分かりやすい時間表記に変更する
        return time.ctime(response.tx_time)
    except Exception as e:
        return str(e)

user_name = input("Enter your user name: ")
user_name_length = len(user_name)
first_message = input("Enter your first message: ")
time_stamp = get_ntp_time()

try:
    # 数値もbinaryに変換しないとサーバーが受け取れない
    sock.sendto(user_name_length.to_bytes(1, byteorder="big") + user_name.encode() + time_stamp.encode() + first_message.encode(), (server_address, server_port))
except Exception as e:
    print(str(e))

bufferSize = 4096

try:
    while True:
        readable, writable, exceptional = select.select([sock], [sock], [sock], 1)

        if sock in readable:
            data, address = sock.recvfrom(bufferSize)

            # もし、サーバーから新規登録通知が来たら、その旨を出力
            if data.decode().startswith("REGISTERED"):
                print("You have been registered as:", data.decode().split(" ")[1])
            else:
                remote_user_name_length = data[0]
                remote_user_name = data[1:1+remote_user_name_length].decode()
                # この間にタイムスタンプが24文字で含まれているため、そのあとからメッセージ取得
                remote_message = data[1+remote_user_name_length+25:].decode()

                print(f"{remote_user_name}: {remote_message}")

        if sock in writable:

            message = input("メッセージを入力してください。")
            if "抜けます" in message:
                break

            time_stamp = get_ntp_time()
            
            try:
                sock.sendto(user_name_length.to_bytes(1, byteorder="big") + user_name.encode() + time_stamp.encode() + message.encode(), (server_address, server_port))
            except Exception as e:
                print(str(e))

        if sock in exceptional:
            print("ソケットにエラーが発生しました。")
            break

except KeyboardInterrupt:
    print("通信を切断します。")
    
finally:
    sock.close()