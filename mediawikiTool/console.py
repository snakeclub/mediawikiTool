#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# Copyright 2019 黎慧剑
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
mediawikiTool Console (控制台)
@module console
@file console.py
"""

import sys
import os
from HiveNetLib.base_tools.run_tool import RunTool
from HiveNetLib.base_tools.string_tool import StringTool
from HiveNetLib.base_tools.file_tool import FileTool
from HiveNetLib.simple_xml import SimpleXml
# 根据当前文件路径将包路径纳入，在非安装的情况下可以引用到
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))
from mediawikiTool.lib.server import ConsoleServer


__MOUDLE__ = 'console'  # 模块名
__DESCRIPT__ = u'mediawikiTool Console (控制台)'  # 模块描述
__VERSION__ = '0.1.0'  # 版本
__AUTHOR__ = u'黎慧剑'  # 作者
__PUBLISH__ = '2019.12.3'  # 发布日期


def main(**kwargs):
    # 获取命令行参数，需要外部传入config、encoding参数
    # 例如 console.py config=/conf/config.xml encoding=utf-8
    CONSOLE_GLOBAL_PARA = {
        # 'execute_file_path': FileTool.get_exefile_path(),  # 执行文件所在目录，应指当前文件
        'execute_file_path': os.path.realpath(FileTool.get_file_path(__file__)),
        'work_path': os.getcwd(),  # 工作目录，可以通过cd命令切换，通过pwd命令查看工作目录路径
    }
    RunTool.set_global_var('CONSOLE_GLOBAL_PARA', CONSOLE_GLOBAL_PARA)
    _cmd_opts = RunTool.get_kv_opts()
    _config = (
        os.path.join(CONSOLE_GLOBAL_PARA['execute_file_path'], 'conf/config.xml')
    ) if 'config' not in _cmd_opts.keys() else _cmd_opts['config']
    _encoding = 'utf-8' if 'encoding' not in _cmd_opts.keys() else _cmd_opts['encoding']
    CONSOLE_GLOBAL_PARA['config_encoding'] = _encoding
    CONSOLE_GLOBAL_PARA['config_file'] = _config

    # 获取配置文件信息
    _config_xml = SimpleXml(os.path.realpath(_config), encoding=_encoding)
    _config_dict = _config_xml.to_dict()

    # 启动控制台服务
    _server = ConsoleServer(_config_dict['console'])
    _server.start_console()


if __name__ == '__main__':
    main()
