import datetime
import sys
import traceback

import uuid
import os.path
from typing import List, Dict, Union
import time
import random
import threading
from pychatgpt import Chat, Options
from pychatgpt.classes.chat import ask
from fastchatgpt.chatgpt.fast_chat import FastChat
import copy
from tqdm import tqdm


def parse_proxy(proxies:Union[Dict, str, None]) -> Union[Dict, None]:
    if isinstance(proxies, str):
        parts = proxies.split('+')
        _proxies = {}
        for part in parts:
            if part.startswith('http_proxy='):
                _proxies['http'] = part.split('http_proxy=')[1]
            if part.startswith('https_proxy='):
                _proxies['https'] = part.split('https_proxy=')[1]
        return _proxies
    return proxies


class TokenChat:
    """
    用来适配通过access_token来获取的情况

    """
    def __init__(self, access_token, proxies):
        # Manually set the token
        # OpenAI.Auth.save_access_token(access_token=access_token, expiry=time.time() + 3600)

        # Get the token, expiry
        # access_token, expiry = OpenAI.Auth.get_access_token()
        self.access_token = (access_token, time.time()+3600)
        self.proxies = proxies

    def ask(self, prompt):
        answer, previous_convo, convo_id = ask(auth_token=self.access_token,
                prompt=prompt,
                conversation_id=None,
                previous_convo_id=None,
                proxies=self.proxies)
        return answer


def get_account(accounts)->List[Dict]:
    """
    Read accounts to a list of dict

    :param accounts:
    :return:
    """
    if isinstance(accounts, str):
        _account = []
        assert os.path.exists(accounts), 'Please pass an account file when you pass accounts as a string'
        with open(accounts, 'r') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) == 1:  # access token
                    _account.append({
                        'access_token': parts[0]
                    })
                else:
                    _account.append({
                        'username': parts[0],
                        'password': parts[1]
                    })
                    if len(parts)>2:
                        proxy = parse_proxy(parts[2])
                        _account[-1]['proxies'] = proxy

        return _account
    return accounts


class Balancer:
    """
    Balancer is used to balance different accounts, so that we can call Bot concurrently.

    """
    def __init__(self, accounts:Union[List[Dict], str], proxies:Union[Dict, str, None],
                 each_query_time_sep:int=30):
        """

        :param accounts:
        :param proxies:
        :param each_query_time_sep:
        """
        self.accounts = get_account(accounts)
        self.proxies = parse_proxy(proxies)
        self.chats = {}
        self.login_ins()
        self.spare_chats = {k:(v, time.time()) for k,v in self.chats.items()}
        self.chat_last_send = {k:-1 for k in self.chats}
        self.each_query_time_sep = each_query_time_sep

    def login_ins(self):
        fail_accounts = []
        for account in self.accounts:
            option = Options()
            if self.proxies:
                option.proxies = self.proxies
            if account.get('proxies', None):
                option.proxies = account.get('proxies')
            print(f"Login to {account['username']}...")
            try:
                if 'access_token' in account:
                    chat = TokenChat(access_token=account['access_token'], proxies=self.proxies)
                    self.chats[account['username']] = chat
                else:
                    chat = FastChat(email=account['username'], password=account['password'], options=option)
                    # import pdb
                    # pdb.set_trace()
                    if chat.auth_access_token is not None:
                        self.chats[account['username']] = chat
                        print(f"Login to {account['username']} Successfully...")
                    else:
                        print(f"Fail to login to {account['username']}...")
            except Exception as e:
                fail_accounts.append(account['username'])
                print(f"Fail to login to {account['username']}...")
                import traceback
                traceback.print_exc()
            # sleep several seconds
            time.sleep(random.randint(100, 400)/100)
        if len(self.chats)==0:
            raise RuntimeError("No success login...")
        print(f"Successful log {len(self.chats)} chats...")
        print(f"Fail to login to {fail_accounts}")

    def batch_query(self, prompts:List[str]) -> List[str]:
        pass


class SimpleBalancer(Balancer):
    def __init__(self, accounts:Union[List[Dict], str], proxies:Union[Dict, str, None]=None,
                 refresh_dialogue_each_prompt=True, each_query_time_sep=30,
                 skip_account_if_identification_code=True):
        """
        在不同账号之间进行轮询的并行 Balancer，支持传入多个账号，会考虑到当出现了禁止访问后让对应的账号暂停访问1小时。Balancer会首先尝试自动
        登录所有的账号，然后通过这些账号进行轮询访问。在访问过程中，如果出现了异常（通过返回的结果中包含了[Response Text]来判断的），该条请求
        会在之后被重新请求。

        :param accounts: (1) str类型，表明该参数为一个文件路径，文件中的内容以每行为单位，每一行以空格分割，第一个元素为账号，第二个元素为
            密码，第三个元素（可选）为当前账号使用的代理，代理的格式需要类似http_proxy=http://proxy.com+https_proxy=http://proxy.com；
            (2) List[Dict]，类似[{'username': xxx, 'pasdword': xxx, 'proxies': xxx},
                {'username': xxx, 'pasdword': xxx, 'proxies': xxx}]其中proxies是可选参数
        :param proxies: （1）Dict, 类似{'http_proxy': 'http://proxy.com', 'https_proxy': 'http://proxy.com'}
            (2) str，类似http_proxy=http://proxy.com+https_proxy=http://proxy.com；
        :param refresh_dialogue_each_prompt: 是否在每次请求后都刷新对话状态，通过这个方式可以使得不同 sample 之间没有影响
        :param each_query_time_sep: 每个账号的连续两次访问间间隔的时间
        :param skip_account_if_identification_code: 如果某个账号需要输入验证码则跳过这个账号。
        """
        super().__init__(accounts=accounts, proxies=proxies, each_query_time_sep=each_query_time_sep)
        self.refresh_dialogue_each_prompt = refresh_dialogue_each_prompt
        self.skip_account_if_identification_code = skip_account_if_identification_code

    def batch_query(self, prompts:Dict[int, Dict]) -> Dict:
        """

        :param prompts: Each item in this dict should include an id and its corresponding text. The id will be used to check
            whether this text has been annotated.
        :return: the return dict has the folloing form
            {
                idx1: {  # from the input prompts
                    'prompt': '',  # from the input prompts
                    'response': ''  # answered by the bot
                    'username': ''  # 这个请求是由哪个账号发出的,
                    'send_timestamp': '' # 发送请求回应的时间
                    'receive_timestamp': '' # 收到请求回应的时间
                },
                idx2: {  # from the input prompts
                    'prompt': '',  # from the input prompts
                    'response': ''  # answered by the bot
                    'username': ''  # 这个请求是由哪个账号发出的,
                    'send_timestamp': '' # 发送请求回应的时间
                    'receive_timestamp': '' # 收到请求回应的时间
                }
            }
        """
        self.responses = {}
        ts = []
        left_prompts = [(idx, pmt) for idx, pmt in prompts.items()]
        total_prompts = len(left_prompts)
        start_time =time.time()
        try:
            pbar = tqdm(total=total_prompts)
            while len(self.responses) != total_prompts:  # 在没有标注完成前，不会退出
                # 这种情况一般出现在最后几个标注，等待一下，防止最后有标注失败了
                wait_count = 0
                if len(left_prompts) == 0 and len(self.responses) != total_prompts:
                    time.sleep(1)
                    wait_count += 1
                    if wait_count%120 == 0:
                        pbar.write(f'It has been waiting for {wait_count} seconds to get all samples annotated, if it is '
                                   f'not expected, please ctrl+c')
                if len(left_prompts) == 0:  # 说明不需要标注了
                    break
                idx, prompt = left_prompts.pop()
                chat_id, chat = self.get_spare_chat()
                # add random seconds to separate two neighboring request
                rand_secs = random.uniform(0, self.each_query_time_sep/len(self.chats))
                # rand_secs = random.randrange(break_seconds//2*100, break_seconds*100)/100
                time.sleep(rand_secs)
                # send request
                t = threading.Thread(target=self.send_query, args=(idx, prompt, chat, chat_id, left_prompts))
                t.start()

                # 清除掉之前已经运行结束的线程
                i = 0
                for i in range(len(ts)):
                    if ts[i].is_alive():
                       break
                ts = ts[i:]
                ts.append(t)
                pbar.update(1)

            for t in ts:
                t.join()
                pbar.update(1)

            pbar.close()
        except:
            import traceback
            traceback.print_exc()
        finally:
            print(f"Annotate {len(self.responses)} samples, left {len(left_prompts)} samples, "
                  f"takes {time.time()-start_time} seconds")

        return copy.deepcopy(self.responses)

    def refresh_chat_dialogue(self, chat: Chat):
        """
        重置 Chat 的状态。

        :param chat:
        :return:
        """
        chat.conversation_id = None
        chat.previous_convo_id = str(uuid.uuid4())

    def send_query(self, idx:int, prompt:Dict, chat: Chat, chat_id:int, left_prompts:List):
        """
        实际发送请求的函数

        :param idx: 当前 prompt 的index
        :param prompt: 一个包含了 'prompt' key 的字典
        :param chat: 一个ChatGPT账号对象
        :param chat_id: chat 对应的ID
        :param left_prompts: 还没有请求过的 prompt 内容，如果当前访问失败了，会将这个 prompt 重新加入到这个里面
        :return:
        """
        success = False
        try:
            send_timestamp = str(datetime.datetime.now())
            response = chat.ask(prompt=prompt['prompt'])
            if self.refresh_dialogue_each_prompt:
                self.refresh_chat_dialogue(chat)
            if '[Response Text]' in response:  # 大概率是出问题了
                print(f"Fail to get response:`{response}` with account `{chat.email}`. This sample will be retried later...")
            else:
                success = True
                # print(f"Success ask with response:{response} for {chat_id}")
            self.chat_last_send[chat_id] = time.time()
        except:
            import traceback
            traceback.print_exc()
            success = False
        if success:
            self.spare_chats[chat_id] = (chat,
                                         time.time()+random.randint(self.each_query_time_sep//2, self.each_query_time_sep))
            res = copy.deepcopy(prompt)
            res['response'] = response
            if chat.email is not None:
                res['email'] = chat.email
            res['receive_timestamp'] = str(datetime.datetime.now())
            res['send_timestamp'] = send_timestamp
            self.responses[idx] = res
        else:
            # If there is a problem with this response, better to make the agent to wait...
            self.spare_chats[chat_id] = (chat, time.time()+random.randint(3600, 3800))
            left_prompts.append((idx, prompt))
            return None

    def get_spare_chat(self):
        # 找到空闲的chat
        count = 0
        found_spare_chat = False
        while len(self.spare_chats)==0 or found_spare_chat is False:
            time.sleep(1)
            count += 1
            if count>4000:
                raise RuntimeError("It takes too long to retrieve a sentence...")
            for idx in self.spare_chats:
                chat, use_after = self.spare_chats[idx]
                if time.time()>use_after:
                    chat_id, chat = idx, chat
                    found_spare_chat = True
                    break
        # 被选中后，让它不能再被选择
        self.spare_chats[chat_id] = (chat, float('inf'))
        return chat_id, chat
