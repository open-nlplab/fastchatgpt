# fastChatGPT

fastChatGPT帮助您快速使用当下最强大的对话模型ChatGPT完成各种NLP任务的评测与推理，并能够
自动记录您与ChatGPT在命令行中聊天。

## 安装指南
fastChatGPT可以通过以下的命令进行安装
```shell
pip install fastchatgpt
```

fastChatGPT具有以下功能

<details>
<summary>交互使用</summary>

```shell
$ bot_play --username <your email> --password <your password>
```

如果需要使用代理，可通过 ```--proxies http_proxy=http://proxy.com+https_proxy=http://proxy.com``` 
设置。通过交互使用，fastChatGPT会自动将交互过程中的输入输出记录到当前目录的```play_logs.txt```文件,
如果希望存到其它地址，请通过 ```-o /path/to/log.txt``` 指定保存日志的路径，
一个使用截图如下图所示

#### 运行效果
```
Start to log in openai...
play logs will be saved in /path/to/play_logs.txt.
bot_play - Help user to play with chat bot and log the conversation
Please use \n to represent change line in your input

                !help - Show help message
                !sep {message} - Add a sep message to the log file
                !exit - Exit the program
    
You: What about the whether outside ?
Bot: I'm sorry, but I am a text-based AI assistant and I do not have the ability to access information about the weather. I am not connected to the internet and do not have access to real-time information. My knowledge is based on the text that I have been trained on, and my abilities are limited to natural language processing and generation. Is there something else I can help you with?

You: Have you heard Yesterday Once more?
Bot: As I mentioned earlier, I am a large language model trained by OpenAI and do not have the ability to access information from the internet or to listen to music. My knowledge is based solely on the text that I have been trained on, and I do not have personal experiences or opinions. I am here to assist you with any questions you may have within the scope of my training. Can I help you with something else?

You: !sep The following result should be recorded!!!!
You: Haha, can you help me to use DALLE-2 to generate an image of tiger?
Bot: I'm sorry, but I am not familiar with DALLE-2 or its ability to generate images. As a large language model trained by OpenAI, my abilities are limited to natural language processing and generation. I do not have the ability to access information from the internet or to generate images. I am here to assist you with any questions you may have within the scope of my training. Is there something else I can help you with?

You: Cola
Bot: Cola is a type of carbonated beverage that is flavored with extracts from the kola nut, as well as other ingredients such as caffeine and sweeteners. Cola drinks are typically dark brown in color and have a distinctive flavor that is sweet and slightly bitter. They are popular around the world and are often consumed as a refreshment or as a mixer in cocktails. Some of the most well-known cola brands include Coca-Cola and Pepsi.

You: !quit
```


使用后，日志文件中的内容如下，
```text
New play logs on 2022-12-06 18:13:45

2022-12-06 18:14:05 You: What about the whether outside ?
2022-12-06 18:14:11 Bot: I'm sorry, but I am a text-based AI assistant and I do not have the ability to access information about the weather. I am not connected to the internet and do not have access to real-time information. My knowledge is based on the text that I have been trained on, and my abilities are limited to natural language processing and generation. Is there something else I can help you with?

2022-12-06 18:14:30 You: Have you heard Yesterday Once more?
2022-12-06 18:14:57 Bot: As I mentioned earlier, I am a large language model trained by OpenAI and do not have the ability to access information from the internet or to listen to music. My knowledge is based solely on the text that I have been trained on, and I do not have personal experiences or opinions. I am here to assist you with any questions you may have within the scope of my training. Can I help you with something else?



==========The following result should be recorded!!!!==========


2022-12-06 18:15:42 You: Haha, can you help me to use DALLE-2 to generate an image of tiger?
2022-12-06 18:16:02 Bot: I'm sorry, but I am not familiar with DALLE-2 or its ability to generate images. As a large language model trained by OpenAI, my abilities are limited to natural language processing and generation. I do not have the ability to access information from the internet or to generate images. I am here to assist you with any questions you may have within the scope of my training. Is there something else I can help you with?

2022-12-06 18:16:16 You: Cola
2022-12-06 18:16:37 Bot: Cola is a type of carbonated beverage that is flavored with extracts from the kola nut, as well as other ingredients such as caffeine and sweeteners. Cola drinks are typically dark brown in color and have a distinctive flavor that is sweet and slightly bitter. They are popular around the world and are often consumed as a refreshment or as a mixer in cocktails. Some of the most well-known cola brands include Coca-Cola and Pepsi.


```


</details>
<details>
<summary>数据评测</summary>
Working  
在给定数据集上使用ChatGPT进行评测 
</details>
<details>
<summary>数据推理</summary>
通过fastchatgpt的推理，通过传入多个账号，可以实现同时调用多个账号进行并行，此外考虑到可能非常
容易因为网络问题导致需要重新推理，以下示例还会将已经有结果的请求缓存起来，
下次直接运行的时候会跳过这些已经有结果的请求，使用代码如下

```python
import os.path
from fastchatgpt import SimpleBalancer
import json

# 申明将请求请求结果存放到哪里
response_path = '/your/path/to/save/result'
# 创建一下文件夹，防止保存失败
if os.path.dirname(response_path) != '':
    os.makedirs(os.path.dirname(response_path), exist_ok=True)

# !!!!! 需要自己根据情况修改的部分
# 读取数据
...
# 读取后数据应该类似于下面的结构，每个 key 是用来帮助fastchatgpt追踪这个 sample 是不是已经被标注了(需要为str类型)；value 是一个字典
#  其中必须要包含'prompt'这个key，并且内容需要为一个 str，这个内容将直接传递给 chatgpt 进行生成，chatgpt返回的结果
#  会被存到'response'这个key下，所以输入中不要占据这个 key 。
# prompts = {
#     '0': {'prompt': 'xxxxx'},
#     #  fastchatgpt只会使用其中的'prompt'，可以包含其它 key
#     '1': {'prompt': 'xxxx'},
# }
# !!!!!


# 以下是缓存已经有响应的文件，防止重复请求
count = 0
annotated = {}
if os.path.exists(response_path):
    with open(response_path, 'r') as f:
        annotated = json.load(f)
    for key in annotated:
        prompts.pop(key)
        count += 1

print(f"Intended to annotate {len(prompts)} samples, {count} of them have been annotated.")        

# 初始化一个 Balancer 来协调多个的账号请求
balancer = SimpleBalancer(accounts='please_see_below')
responses = balancer.batch_query(prompts)
annotated.update(responses)
print(f"Annotated {len(responses)}, left {len(prompts) - len(annotated)} samples to annotate")

# 保存结果
try:
    with open(response_path, 'w') as f:
        json.dump(annotated, f, indent=2)
    print(f"The results are saved to {response_path}...")
except:
    # 如果有异常尝试暂时存到一个临时文件，防止白跑了
    print("The following exception occurs when try to save the result")
    import traceback
    from datetime import datetime
    traceback.print_exc()
    file_name = os.path.splitext(os.path.basename(response_path))[0]
    with open(f'{file_name}_tmp.json', 'w') as f:
        f.write(annotated)
    print("The results are saved to a temporary file named:{}")
# 结果为一个 dict 文件
#  {
#    '0': {'prompt': xxx, 'response': xxxx}  # 其中0就是在prompt中对应的0，如果输入中有其它的内容，也会一并保存在这个dict中
#  
#  }
```

account有以下两种
```text
(1) List[Dict]，例如
[{
    'username': 'username1', 
    'password': 'password1',
    'proxies': {'http_proxy': 'http://proxy.com', 'https_proxy': 'http://proxy.com'}  # 可选参数
}
]
(2) str, 传入一个文件地址，文件中的内容应该类似于下面的内容
username1 password1 
usernam2 password2
```

上述代码如果在运行过程中失败，直接尝试再次运行即可。

#### 如果对query过程有特殊的需求，例如需要chain-of-thought，可以继承SimpleBalancer，并修改send_query函数即可。



</details>

## Credit
这个项目很大程度上受到了[ChatGPT](https://github.com/acheong08/ChatGPT)以及[PyChatGPT](https://github.com/rawandahmad698/PyChatGPT)的启发。