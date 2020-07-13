> # **Project Q!i@a#n\$N%i^u Chatbot**

Python based Chatbot + Interface for QN Desktop OR WX Public account

完全用 Python 的聊天机器人 + QN 或者 WX 公众号接口

## About

This project has 2 independent components: a qn desktop natural language chatbot and a WeChat public account menu-based chatbot. Both have very different interfaces but share a core Chatbot process that captures chat information and decides content replies.

## 关于

这个项目有两个部分：qn 桌面自然语言机器人和 wx 公众号菜单机器人。两个部分都用到

机器人的回答方法与回复讯息内容都在以下的文件控制的：
-chatbot_resource.json (主要的)
-policydata.json
-sideinfo.json

如果要改对话流程与内容的话，要配置以上#1 和#2 文件

AI 训练的资源在 "embedding" 文件夹里。训练 AI 的流程在下面。菜单机器人不用到 AI

## 内容

### chatbot_resource

聊天机器人资料
这个文件里有所有的回复讯息内容，关于生意的细节（如：产品价值，几号关店），所有的基数算法
对话中通常会用到所有的数据

`intent` - 讯息意思
在这里定一些主要的意思如：affirm（是），deny（否），purchase（想买），inform_done（通知做完了），等
程序会把收到的讯息转给智能（AI）了解然后返回这些意思。

`state` - 对话情形
可能是这个文件里最重要的部分
在这里定对话流程所有预备的阶段。
对话用《讯息意思》与《对话情形》一起来决定恰当的《对话情形》与回复讯息。这个决定规则在 policydata.json 配置
这里可以控制回复（可以多选），来到这个情形之前需要的信息（如：客户的城市/客户要买什么），找什么`slot`（主要内容）

- req_info - 这个阶段需要的信息
- gated - 如果 req_info 不是空的，这个应该放 True，不然 False。这个会检查机器人知识有关键的信息。如果没有，会造问题跟客户要求这些信息。（看 request_string)

request_string 是一个特别的讯息模板。只有《对话情形》TMP_recv_info 会发 request_string。TMP_recv_infos 是一个暂时《对话情形》，好像一个锁门，只会出现。解决好了，对话流程会继续走到本来要到的《对话情形》。

`reply_formatting` - 讯息模板
很多回复讯息的形状是一样的，差别只在细节。用讯息模板让我们只要定一次可以再用好几次
用`{信息名}`来代表想显示的信息（如：城市名（city_name))

`formulae` - 算法
这些算法是用来得到一些重要的基数如客户产品一共付多少。

`vault_info`
这里主要是 lookup_info 写下生意关键的数据如产品的价值，服务费价值，产品的链接，淘宝店链接，每个月什么时候关，等
`database_protocol` 的 “\_on_find” 是管理 SQL 如果找到这个客户的话程序该怎么填信息。目前是如果找到的话就把这个客户当老客户，不再问新客户的事。

`policy_data_location`/`sideinfo_location`:
关键的文件地址。默认是在同样文件夹里

### policydata

政策数据

主要部分：policy_rules
这个文件是控制对话流程，决定每个《对话情形>：

- 可以走到哪些《对话情形》
- 哪个《讯息意思》可以让你换到哪个《对话情形》
- 看机器人信息(如：城市，是不是老客户)走到不同的《对话情形》以及不同的回复讯息

```
"init":[
        ["affirm","provide_taobao_link"],
        ["purchase", "provide_taobao_link"],
        ["purchase_xufei", "provide_taobao_link"],
        ["inform_paid","finished_payment"],
        ["deny", "initplus"]
    ]
}
```

`《目前对话情形》:[[《讯息意思》:《下个对话情形》]]`
在例子里，如果机器人目前在"init"《对话情形》，机器人收到"purchase"《讯息意思》会走到"provide_taobao_link"的《对话情形》

### sideinfo

sideinfo 可以定一些关键词如 城市，月。
可以控制机器人怎么抓到主要的信息。所谓的主要信息叫`slot`。
机器人接受信息时会找用户定的`slot`词配对然后更新机器人知识

### AI 训练

数据格式：
看 sample_data.csv

流程：

1. 跑 csv2train_data.py，会生成 generated_data.csv
2. 跑 nlp_trainer.py。让程序跑一会儿，长久要靠电脑，生成 trained.h5 这是了解讯息意思的 AI
3. 把 trained.h5 改名成 API_MODEL.h5 放在 embedding 文件夹
   接下来 qn 机器人会用到 API_MODEL.h5 来了解讯息给程序返回《讯息意思》

### QNPlugin

_注意！跑这个程序之前要登录 QN 然后开聊天窗口_

程序
有两个模式：自动，等人（推荐）
跑程序的时候会问用户。打任何字会选等人模式，空打“enter”会选自动模式

这个程序主要功能是个 QN 接口。读 QN 聊天窗口里的内容，找到最新的讯息放在一起然后传给机器人去了解。机器人回复时，QNPlugin 会把文字贴进聊天窗口。自动模式会直接发送讯息。等人模式会等到用户自己去发讯息，用户可以先改善讯息内容然后发。

QN 读字时会自动排除一些通用词（如：吧，是）因为这些词对讯息意思的贡献不大。研究报告到排除通用词一般会提高 AI 理解能力

主要文件：

- QNPlugin.py

### 机器人服务器

_WePay 功能还没测试。请登录 WX 的平台看关键的文件_

这个程序主要功能是 HTTP interface。HTTP request 的信息传给机器人，然后把机器人返回的信息造成一个 HTTP request
要用 wx 公众号的聊天机器人需要接受 wx 的 GET 与 POST request
_注意！wechat_dev.py 里面有些公司的私人信息。请别让这个文件公开存取_

这个程序会关注码号，接受任何 wx HTTP request 然后返回恰当的 POST request。
例如：
接受开启的 auth 的 GET request 然后返回 request 里的 auth code
公众号收到用户信息的 POST request，把信息传到机器人，然后返回回复讯息的 POST request
wxpay 的 auth GET request

文件：

- http_files_utils.py
- http_request_interpreter.py
- http_customer_manager.py
- http_server.py (主要)
- http_utils.py
- http_wx_message.py
- wechat_dev.py (公司私人信息)

* docker 命令
  docker build -t 《这里定项目名字》
  docker run -p 8081:8081 -d 《项目名字》

在 http_server.py 配置码号 (现在是 8181)

### Project Dependencies

Core:

- pymssql<3.0
- urllib3
- requests

NLP/QN:

- tensorflow (2.0.0)
- pywin32
- Jpype1
- jieba
- pandas
- keras
- Java >8
- jdk 12.0.2
- aiohttp
- python-socketio

### Useful resources

- [Seq2Seq Chinese Chatbot on android](http://www.shareditor.com/blogshow/?blogId=63)
