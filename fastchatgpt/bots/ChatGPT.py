import json
import re
from copy import deepcopy
import os.path
import base64
from urllib.parse import quote

import requests
import tls_client
import uuid
from bs4 import BeautifulSoup
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM
from io import BytesIO

from fastchatgpt.bots.BaseBot import parser, BOT
from fastchatgpt.utils import Config

from time import sleep


@BOT.register_module()
class ChatGPT:

    def __init__(self):
        self.parse_args()
        self.config = Config(parser)
        if self.config.data["no_context"]:
            self.config.data["conversation_id"] = ""
        else:
            self.config.data["no_context"] = False
        self.session = None

    def parse_args(self):
        parser.add_argument("--username", type=str, default="")
        parser.add_argument("--password", type=str, default="")
        parser.add_argument("--encode_username", type=str, default="")
        parser.add_argument("--encode_password", type=str, default="")
        parser.add_argument("--conversation_id", type=str, default="")
        parser.add_argument("--parent_id", type=str, default=str(uuid.uuid4()))
        parser.add_argument("--format", type=str, default="text")
        parser.add_argument("--no_context", action="store_true")
        parser.add_argument("--config", type=str, default="chatgpt")
        parser.add_argument("--account_list", type=str, default="")
        parser.add_argument("--access_token", type=str, default="")
        parser.add_argument("--timeout", type=int, default=100)
        parser.add_argument("--proxies", type=str, default=None)

    def get_header(self):
        return {
            "Accept": "application/json",
            "Authorization": "Bearer " + self.config.data["access_token"],
            "Content-Type": "application/json",
            "origin": "https://chat.openai.com",
            "pragma": "no-cache",
            "referer": "https://chat.openai.com/",
            "sec-ch-ua": '" Not A;Brand";v="99", "Chromium";v="90", "Google Chrome";v="90"',
            "sec-ch-ua-mobile": "?0",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36"
        }

    def request(self, prompt) -> dict:
        if self.config.data["account_list"] != "":
            self.change_account()
        if self.config.data["access_token"] == "" or not self.session:
            self.login()
        data = {
            "action": "next",
            "messages": [
                {
                    "id": str(uuid.uuid4()),
                    "role": "user",
                    "content": {
                        "content_type": "text",
                        "parts": [prompt]
                    }
                }],
            "parent_message_id": self.config.data["parent_id"],
            "model": "text-davinci-002-render"
        }
        if self.config.data["conversation_id"] != "" and self.config.data["conversation_id"] != None:
            data["conversation_id"] = self.config.data["conversation_id"]
        if self.config.data["format"] == 'text':
            while True:
                response = requests.post("https://chat.openai.com/backend-api/conversation", headers=self.get_header(),
                                         data=json.dumps(data), timeout=self.config.data['timeout'])
                try:
                    if response.status_code == 200:
                        response = response.text.splitlines()[-4]
                        response = response[6:]
                        break
                    elif response.status_code == 429:
                        # 此时说明这个账号在一个小时内的请求次数过多了，更换账号使用
                        self.change_account()
                    else:
                        print(f"Network error with error code {response.status_code}, will retry soon...")
                        self.login()
                        continue
                except:
                    raise ValueError("Response is not in the correct format")
            response = json.loads(response)
            self.config.set("parent_id", response["message"]["id"])
            self.config.set("conversation_id", response["conversation_id"])
            message = response["message"]["content"]["parts"][0]
            yield {'message': message, 'conversation_id': self.config.data["conversation_id"],
                    'parent_id': self.config.data["parent_id"]}
        elif self.config.data["format"] == 'stream':
            response = requests.post("https://chat.openai.com/backend-api/conversation", headers=self.get_header(),
                                     data=json.dumps(data), stream=True, timeout=self.config.data['timeout'])
            for line in response.iter_lines():
                try:
                    line = line.decode('utf-8')
                    if line == "":
                        continue
                    line = line[6:]
                    line = json.loads(line)
                    try:
                        message = line["message"]["content"]["parts"][0]
                        self.config.set("parent_id", line["message"]["id"])
                        self.config.set("conversation_id", line["conversation_id"])
                    except:
                        continue
                    yield {'message': message, 'conversation_id': self.config.data["conversation_id"],
                           'parent_id': self.config.data["parent_id"]}
                except:
                    continue

    def login(self):
        # the following code are from https://github.com/rawandahmad698/PyChatGPT
        if self.config.data['username'] == "" or self.config.data['password'] == "":
            return
        if self.config.data['encode_username'] == "" or self.config.data['encode_password'] == "":
            self.config.set('encode_username', quote(self.config.data['username']))
            self.config.set('encode_password', quote(self.config.data['password']))
        while True:
            self.session = tls_client.Session(
                client_identifier="chrome_105"
            )
            proxies = self.config.data['proxies']
            if proxies is not None:
                assert isinstance(proxies, str), 'Only string proxies information is allowed. ' \
                                                 'Such as http_proxy=http://proxy.com+https_proxy=http://proxy.com.'
                parts = proxies.split('+')
                _proxies = {}
                for part in parts:
                    if part.startswith('http_proxy='):
                        _proxies['http'] = part.split('http_proxy=')[1]
                    if part.startswith('https_proxy='):
                        _proxies['https'] = part.split('https_proxy=')[1]
                if _proxies:
                    self.session.proxies = _proxies
            try:
                headers = {
                    "Host": "ask.openai.com",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15',
                    "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Connection": "keep-alive",
                }
                response = self.session.get(url="https://chat.openai.com/auth/login", headers=headers)
                assert response.status_code == 200
                headers = {
                    "Host": "ask.openai.com",
                    "Accept": "*/*",
                    "Connection": "keep-alive",
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15',
                    "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
                    "Referer": "https://chat.openai.com/auth/login",
                    "Accept-Encoding": "gzip, deflate, br",
                }
                response = self.session.get(url="https://chat.openai.com/api/auth/csrf", headers=headers)
                assert response.status_code == 200
                payload = f'callbackUrl=%2F&csrfToken={response.json()["csrfToken"]}&json=true'
                headers = {
                    'Host': 'ask.openai.com',
                    'Origin': 'https://chat.openai.com',
                    'Connection': 'keep-alive',
                    'Accept': '*/*',
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15',
                    'Referer': 'https://chat.openai.com/auth/login',
                    'Content-Length': '100',
                    'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
                    'Content-Type': 'application/x-www-form-urlencoded',
                }
                response = self.session.post(url="https://chat.openai.com/api/auth/signin/auth0?prompt=login",
                                             headers=headers, data=payload)
                if response.status_code == 400:
                    raise Exception("Bad request from your IP address")
                assert response.status_code == 200 and 'json' in response.headers['Content-Type']
                headers = {
                    'Host': 'auth0.openai.com',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Connection': 'keep-alive',
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Referer': 'https://chat.openai.com/',
                }
                response = self.session.get(url=response.json()["url"], headers=headers)
                assert response.status_code == 302
                state = re.findall(r"state=(.*)", response.text)[0].split('"')[0]
                headers = {
                    'Host': 'auth0.openai.com',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Connection': 'keep-alive',
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Referer': 'https://chat.openai.com/',
                }
                response = self.session.get(f"https://auth0.openai.com/u/login/identifier?state={state}", headers=headers)
                assert response.status_code == 200
                soup = BeautifulSoup(response.text, 'lxml')
                captcha_input = None
                if soup.find('img', alt='captcha'):
                    svg_captcha = soup.find('img', alt='captcha')['src'].split(',')[1]
                    decoded_svg = base64.decodebytes(svg_captcha.encode("ascii"))
                    drawing = svg2rlg(BytesIO(decoded_svg))
                    renderPM.drawToFile(drawing, "captcha.png", fmt="PNG", dpi=300)
                    captcha_input = input('Please enter the identifying code...the identifying code image lies in your'
                                          ' current folder, named captcha.png')
                    assert captcha_input
                if captcha_input:
                    payload = f'state={state}&username={self.config.data["encode_username"]}&captcha={captcha_input}&js-available=true&webauthn-available=true&is-brave=false&webauthn-platform-available=true&action=default'
                else:
                    payload = f'state={state}&username={self.config.data["encode_username"]}&js-available=false&webauthn-available=true&is-brave=false&webauthn-platform-available=true&action=default'
                headers = {
                    'Host': 'auth0.openai.com',
                    'Origin': 'https://auth0.openai.com',
                    'Connection': 'keep-alive',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15',
                    'Referer': f'https://auth0.openai.com/u/login/identifier?state={state}',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Content-Type': 'application/x-www-form-urlencoded',
                }
                response = self.session.post(f"https://auth0.openai.com/u/login/identifier?state={state}", headers=headers, data=payload)
                assert response.status_code == 302
                payload = f'state={state}&username={self.config.data["encode_username"]}&password={self.config.data["encode_password"]}&action=default'
                headers = {
                    'Host': 'auth0.openai.com',
                    'Origin': 'https://auth0.openai.com',
                    'Connection': 'keep-alive',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15',
                    'Referer': f'https://auth0.openai.com/u/login/password?state={state}',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Content-Type': 'application/x-www-form-urlencoded',
                }
                response = self.session.post(f"https://auth0.openai.com/u/login/password?state={state}", headers=headers, data=payload)
                assert response.status_code == 302
                new_state = re.findall(r"state=(.*)", response.text)[0].split('"')[0]
                headers = {
                    'Host': 'auth0.openai.com',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Connection': 'keep-alive',
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15',
                    'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
                    'Referer': f'https://auth0.openai.com/u/login/password?state={state}',
                }
                response = self.session.get(f"https://auth0.openai.com/authorize/resume?state={new_state}", headers=headers, allow_redirects=True)
                assert response.status_code == 200
                soup = BeautifulSoup(response.text, 'lxml')
                next_data = soup.find("script", {"id": "__NEXT_DATA__"})
                self.config.set('access_token', re.findall(r"accessToken\":\"(.*)\"", next_data.text)[0].split('"')[0])
                break
            except Exception as e:
                import traceback
                traceback.print_exc()
                sleep(5)
                continue

    def change_account(self):
        if self.config.data["account_list"] == "":
            return
        if isinstance(self.config.data["account_list"], str):
            if not os.path.exists(self.config.data["account_list"]):
                return
            with open(self.config.data["account_list"], "r", encoding="utf-8") as f:
                lines = f.readlines()
                self.config.set("account_list",
                                [{"username": line.split()[0], "password": line.split()[1]} for line in lines])
        new_config = deepcopy(self.config)
        new_account = new_config.data["account_list"].pop(0)
        new_config.data['config'] = new_account["username"]
        if new_config.config_exist():
            new_config.prepare_config()
        else:
            new_config.data['username'] = new_account["username"]
            new_config.data['password'] = new_account["password"]
            new_config.data["account_list"].append(new_account)
            new_config.data["access_token"] = ""
            new_config.save_config()
        self.config = new_config



if __name__ == "__main__":
    bot = ChatGPT()

    while True:
        prompt = input("You: ")
        print("Bot: ", end="")
        for response in bot.request(prompt):
            print(response["message"], end=' ')
        # bot.refresh_session()
        print("")
