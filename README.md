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
Working   
在给定数据集上使用ChatGPT进行推理
</details>

## Credit
这个项目很大程度上受到了[ChatGPT](https://github.com/acheong08/ChatGPT)以及[PyChatGPT](https://github.com/rawandahmad698/PyChatGPT)的启发。