import threading
import time


class ShowTyping(threading.Thread):
    """
    Use to show the waiting information

    """
    def __init__(self, prompt, show_time=True, update_every=0.3):
        super().__init__()
        self.show_time = show_time
        self.update_every = update_every
        self.setDaemon(True)
        self.print_typing = False
        self.need_clear = False
        self.prompt = prompt

    def run(self):
        while True:
            text = self.prompt + "I'm thinking, please wait"
            start_time = time.time()
            count = 0
            _text = ''
            while self.print_typing:
                self.need_clear = True
                if count>10:
                    print(text+' '*16, end='\r')
                    count = 0
                _text = text + '.'*count
                count += 1
                if self.show_time:
                    seconds = round(time.time() - start_time, 1)
                    _text += f'{seconds}s'
                print(_text, end='\r')
                time.sleep(self.update_every)
            if count != 0:
                print(' '*len(_text), end='\r')
                print(self.prompt, end='', flush=True)
            self.need_clear = False
            time.sleep(0.01)

    def start_waiting(self):
        self.print_typing = True
        self.need_clear = True

    def end_waiting(self):
        self.print_typing = False
        count = 0
        while self.need_clear:  # waiting for clearing
            count += 1
            time.sleep(0.01)
            if count > 2*(self.update_every/0.01):
                print("There is a bug....")
                break
