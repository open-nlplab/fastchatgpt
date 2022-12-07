import argparse
import os
import random
import time

from colorama import Style, Fore
import logging
from logging import FileHandler, Formatter, NullHandler
import types
from datetime import datetime

from tls_client.exceptions import TLSClientExeption

from fastchatgpt.bots import BOT
from fastchatgpt.utils.show_typing import ShowTyping

parser = argparse.ArgumentParser()


def bot_play():
    parser.add_argument("--bot", type=str, default="ChatGPT")
    parser.add_argument('--output', type=str, default='play_logs.txt', help='Where to save the dialogue history')

    args = parser.parse_known_args()[0]
    bot = BOT.build(dict(type=vars(args)['bot']))
    print("Start to log in openai...")
    bot.login()
    logger = logging.getLogger('fastchatgpt')
    if args.output is not None or args.output != 'None':
        fp = os.path.abspath(args.output)
        dirname = os.path.dirname(fp)
        os.makedirs(dirname, exist_ok=True)

        logger.setLevel(logging.DEBUG)
        handler = FileHandler(fp, mode='a', encoding='utf8')
        formatter = Formatter(fmt='%(asctime)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        handler.setFormatter(formatter)
        handler.setLevel(logging.INFO)
        logger.addHandler(handler)
        logger.propagate = False  # forbid pass log to upper logger
        # for separator and some other info to log
        def log_pure_message(self, message):
            # Switch formatter, output a blank line
            self.handler.setFormatter(self.blank_formatter)
            self.info(message)
            # Switch back
            self.handler.setFormatter(self.formatter)
        logger.handler = handler
        blank_formatter = logging.Formatter(fmt="")
        logger.formatter = formatter
        logger.blank_formatter = blank_formatter
        logger.pure_info = types.MethodType(log_pure_message, logger)

        print(Fore.GREEN+f'play logs will be saved in {fp}.'+Style.RESET_ALL)
        logger.pure_info(f'\n\nNew play logs on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
    else:
        logger.addHandler(NullHandler())

    # print info
    print("bot_play - Help user to play with chat bot and log the conversation")
    print("Please use \\n to represent change line in your input")
    help_msg = """
                !help - Show help message
                !sep {message} - Add a sep message to the log file
                !exit - Exit the program
    """
    print(help_msg)
    bot_prompt = Fore.BLUE+"Bot: "
    show_type = ShowTyping(bot_prompt)
    show_type.start()
    start_time = time.time()
    num_turns = 0
    response_total_time = 0
    while True:
        # Here, we need to use color to make the interaction more pretty
        prompt = 'You: '
        # text = get_input(prompt)
        text = input(prompt)

        if text == '!help':
            print(help_msg)
            continue
        elif text.startswith('!sep'):
            info = text.split('!sep')[1].strip()
            info = '='*10 + info + '='*10
            logger.pure_info('\n\n' + info + '\n\n')
            continue
        elif text.startswith('!quit') or text.startswith('!exit'):
            total_time = round(time.time() - start_time, 2)
            response_avg_time = round(response_total_time/(num_turns+1e-6), 2)
            print(Fore.RED+f"Communicate with Bot {total_time} seconds, every turn takes "
                           f"Bot {response_avg_time} seconds to response."+Style.RESET_ALL)
            break

        logger.info(prompt + text)
        # print(bot_prompt, end="", flush=True)
        turn_output = ''
        turn_output += bot_prompt.split(Fore.BLUE)[1]
        show_type.start_waiting()
        retry = 0
        turn_start_time = time.time()
        while True:
            try:
                # TODO here, we need to make it smarter
                shift = 0
                for response in bot.request(text):
                    show_type.end_waiting()
                    w = response["message"]
                    print(w[shift:], end='')
                    shift = len(w)
                turn_output = response['message']
                # response = next(bot.request(text))
                # show_type.end_waiting()
                # words = response["message"]
                # for word in words.split():
                #     print(word, end=' ', flush=True)
                #     turn_output += word + ' '
                #     time.sleep(random.randint(100, 300)/1000.0)
                retry += 1
                break
            except TLSClientExeption as e:
                if retry>3:
                    break
                raise e
        response_total_time += time.time() - turn_start_time
        num_turns += 1
        print(Style.RESET_ALL, flush=True)
        print()
        logger.info(turn_output)  # save the output from the bot
        logger.pure_info('')  # keep one empty line in the log

