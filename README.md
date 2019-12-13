# mediawikiTool
a command line tool for mediawiki file format covert and so on

## install

```
# pip install mediawikiTool
```

or

download source:

```
mediawikiTool> python setup.py install
```

## Use

1 . Type 'wikitool' in cmd line to start the console:

```
# wikitool
```

2 . Type 'help' in the console to get the commond list and help info;

3 . Type  'setlanguage zh_cn' to switch language to 'zh_cn';



## Setting

If you want to change the setting, you can go to the lib install path ，to change the config.xml file：

```
C:\Users\74143\AppData\Local\Programs\Python\Python37\Lib\site-packages\mediawikiTool-0.5.1-py3.7.egg\mediawikiTool\conf\config.xml
```

or copy the config.xml file to your self path, and use ‘wikitool config=/your-path/config.xml’ to start console.



## i18n

If you want to support more language,  you can do the following jobs:

1.change ‘/conf/config.xml ’ file,  add more language translate:

```
like :
<start_tips>{
    "en": [
        "",
        "mediawikiTool Console V{{VERSION}}",
        "Power by Li Huijian @ 2019",
        "please type \"help\" to get help info",
        "you can use Ctrl+C cancle when inputing, or use Ctrl+D exit the Console",
        ""
    ],
    "zh_cn": [
            "",
            "mediawikiTool Console (控制台)  V{{VERSION}}",
            "Power by 黎慧剑 @ 2019",
            "查看命令帮助请执行 help 命令",
            "输入过程中可通过Ctrl+C取消输入，通过Ctrl+D退出命令行处理服务",
            ""
    ]
}

and cmd tags help:
<help>{
    "en": [
        "Support mediawikiTool console commands help info",
        "",
        "help [command]",
        "    command : show the [command string] command's help info",
        "",
        "demo: help help",
        ""
    ],
    "zh_cn": [
        "提供 mediawikiTool 控制台命令的帮助信息",
        "",
        "help [command]",
        "    command : 显示指定 command 命令的帮助信息",
        "",
        "示例: help help",
        ""
    ]
}
</help>
```

2. find ‘console->cmd_list->cmd->command=setlanguage’, add you language tags:

   ```
   <cmd_para>{
       "name_para": {},
       "short_para": {},
       "long_para": {},
       "word_para": {
           "en": "",
           "zh_cn": ""
       }
   }
   </cmd_para>
   ```

3. go to the path 'i18n'，add your language file, file name must 'message_your-lang-tag.json'.