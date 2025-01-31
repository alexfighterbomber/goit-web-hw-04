import json
import socket
import threading
from datetime import datetime
from http.server import SimpleHTTPRequestHandler, HTTPServer
import urllib.parse
from pathlib import Path 
import mimetypes   
from time import sleep

# налаштування серверів
HOST = '0.0.0.0'
HTTP_PORT = 3000
SOCKET_PORT = 5000
STORAGE_DIR = Path("storage")  
STORAGE_DIR.mkdir(parents=True, exist_ok=True)
DATA_FILE = STORAGE_DIR / "data.json"

# HTTP сервер
class MyHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)
        if pr_url.path == '/':
            self.send_html_file('index.html')
        elif pr_url.path == '/message':
            self.send_html_file('message.html')
        else:
            if Path().joinpath(pr_url.path[1:]).exists():
                self.send_static()
            else:
                self.send_html_file('error.html', 404)

    def do_POST(self):
        """ 
        Обробляє POST-запит від веб-форми. Дані передаються на сокет-сервер для збереження.
        """
        data = self.rfile.read(int(self.headers['Content-Length']))
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            while True:
                try:
                    s.sendto(data, ('127.0.0.1', SOCKET_PORT))   # Відправка даних на сокет-сервер
                    response, _ = s.recvfrom(1024)  # Отримання відповіді від сокет-сервера
                    print(f'From server: {response.decode()}')
                    break
                except ConnectionRefusedError:
                    sleep(0.5)    # Чекаємо, якщо сервер ще не піднято

        self.send_response(302)   # Переадресація після обробки форми
        self.send_header('Location', '/')
        self.end_headers()

    def send_html_file(self, filename, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as fd:
            self.wfile.write(fd.read())

    def send_static(self):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        if mt:
            self.send_header("Content-type", mt[0])
        else:
            self.send_header("Content-type", 'text/plain')
        self.end_headers()
        with open(f'.{self.path}', 'rb') as file:
            self.wfile.write(file.read())

def socket_server():
    """
    UDP-сервер, який приймає дані, конвертує їх у словник 
    і додає у файл JSON із часовою міткою.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)     # Створення сокету
    sock.bind((HOST, SOCKET_PORT))  # Прив'язка сокету до адреси
    try:
        while True:
            data, addr = sock.recvfrom(1024)  # Отримуємо дані від клієнта
            if not data:
                continue
            sock.sendto('Дані отримано'.encode('utf-8'), addr)
            try:
                # Декодуємо та парсимо отримані дані
                data_decoded = urllib.parse.unquote_plus(data.decode())
                data_dict = {key: value for key, value in [el.split('=') for el in data_decoded.split('&')]}
                timestamp = datetime.now().isoformat(" ")

                # Завантажуємо попередні дані
                try:
                    with open(DATA_FILE, "r", encoding="utf-8") as f:
                        messages = json.load(f)
                except (FileNotFoundError, json.JSONDecodeError):
                    messages = {}
                messages[timestamp] = data_dict     # Додаємо нове повідомлення
                with open(DATA_FILE, "w", encoding="utf-8") as f:   # Зберігаємо оновлений JSON
                    json.dump(messages, f, indent=4, ensure_ascii=False)
                print(f"Дані збережено: {data_dict}")

            except Exception as e:
                print(f"Помилка обробки повідомлення: {e}")
    except KeyboardInterrupt:
        print(f'Destroy server')
    finally:
        sock.close()

# Запуск HTTP и Socket серверов
if __name__ == "__main__":
    if not DATA_FILE.exists():
        msg={}
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(msg, f, indent=4)
    http_server = HTTPServer((HOST, HTTP_PORT), MyHandler)
    serv = threading.Thread(target=http_server.serve_forever, daemon=True)
    sock = threading.Thread(target=socket_server)
    serv.start()
    sock.start()
    print(f"HTTP сервер запущен на порту {HTTP_PORT}")
    print(f"Socket сервер запущен на порту {SOCKET_PORT}")
    serv.join()
    sock.join()