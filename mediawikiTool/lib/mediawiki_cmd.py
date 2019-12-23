#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# Copyright 2019 黎慧剑
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
mediawiki工具命令模块
@module mediawiki_cmd
@file mediawiki_cmd.py
"""

import os
import sys
import re
import shutil
import requests
import traceback
import platform
import subprocess
import time
import datetime
import copy
import json
try:
    import chardet
except:
    pass
import mwclient
import xlrd
from prompt_toolkit.shortcuts import ProgressBar
from HiveNetLib.base_tools.run_tool import RunTool
from HiveNetLib.prompt_plus import PromptPlus
from HiveNetLib.base_tools.file_tool import FileTool
from HiveNetLib.base_tools.string_tool import StringTool
from HiveNetLib.simple_i18n import _
from HiveNetLib.simple_console.base_cmd import CmdBaseFW
from HiveNetLib.generic import CResult
# 根据当前文件路径将包路径纳入，在非安装的情况下可以引用到
sys.path.append(os.path.abspath(os.path.join(
    os.path.dirname(__file__), os.path.pardir, os.path.pardir)))


__MOUDLE__ = 'mediawiki_cmd'  # 模块名
__DESCRIPT__ = u'mediawiki工具命令模块'  # 模块描述
__VERSION__ = '0.5.1'  # 版本
__AUTHOR__ = u'黎慧剑'  # 作者
__PUBLISH__ = '2019.12.09'  # 发布日期


class MediaWikiCmd(CmdBaseFW):
    """
    MediaWiki的离线处理命令
    """
    #############################
    # 构造函数，在里面增加函数映射字典
    #############################

    def _init(self, **kwargs):
        """
        实现类需要覆盖实现的初始化函数

        @param {kwargs} - 传入初始化参数字典（config.xml的init_para字典）

        @throws {exception-type} - 如果初始化异常应抛出异常
        """
        self._CMD_DEALFUN_DICT = {
            'mdtowiki': self._mdtowiki_cmd_dealfun,
            'docxtowiki': self._docxtowiki_cmd_dealfun,
            'xlstowiki': self._xlstowiki_cmd_dealfun,
            'filestowiki': self._filestowiki_cmd_dealfun
        }
        self._console_global_para = RunTool.get_global_var('CONSOLE_GLOBAL_PARA')

    #############################
    # 实际处理函数
    #############################
    def _cmd_dealfun(self, message='', cmd='', cmd_para='', prompt_obj=None, **kwargs):
        """
        通用处理函数，通过cmd区别调用实际的处理函数

        @param {string} message='' - prompt提示信息
        @param {string} cmd - 执行的命令key值
        @param {string} cmd_para - 传入的命令参数（命令后的字符串，去掉第一个空格）
        @param {PromptPlus} prompt_obj=None - 传入调用函数的PromptPlus对象，可以通过该对象的一些方法控制输出显示
        @param {kwargs} - 传入的主进程的初始化kwargs对象

        @returns {CResult} - 命令执行结果，可通过返回错误码10101通知框架退出命令行, 同时也可以通过CResult对象的
            print_str属性要求框架进行打印处理
        """
        # 获取真实执行的函数
        self._prompt_obj = prompt_obj  # 传递到对象内部处理
        _real_dealfun = None  # 真实调用的函数
        if 'ignore_case' in kwargs.keys() and kwargs['ignore_case']:
            # 区分大小写
            if cmd in self._CMD_DEALFUN_DICT.keys():
                _real_dealfun = self._CMD_DEALFUN_DICT[cmd]
        else:
            # 不区分大小写
            if cmd.lower() in self._CMD_DEALFUN_DICT.keys():
                _real_dealfun = self._CMD_DEALFUN_DICT[cmd.lower()]

        # 执行函数
        if _real_dealfun is not None:
            return _real_dealfun(message=message, cmd=cmd, cmd_para=cmd_para, prompt_obj=prompt_obj, **kwargs)
        else:
            prompt_obj.prompt_print(_("'$1' is not support command!", cmd))
            return CResult(code='11404', i18n_msg_paras=(cmd, ))

    #############################
    # 实际处理函数
    #############################
    def _mdtowiki_cmd_dealfun(self, message='', cmd='', cmd_para='', prompt_obj=None, **kwargs):
        """
        将markdown格式文件转换为mediawiki格式

        @param {string} message='' - prompt提示信息
        @param {string} cmd - 执行的命令key值
        @param {string} cmd_para - 传入的命令参数（命令后的字符串，去掉第一个空格）
        @param {PromptPlus} prompt_obj=None - 传入调用函数的PromptPlus对象，可以通过该对象的一些方法控制输出显示
        @param {kwargs} - 传入的主进程的初始化kwargs对象

        @returns {CResult} - 命令执行结果，可通过返回错误码10101通知框架退出命令行, 同时也可以通过CResult对象的
            print_str属性要求框架进行打印处理
        """
        _ok_result = CResult(code='00000')
        try:
            if not self._para_dict_check(cmd=cmd, cmd_para=cmd_para, prompt_obj=prompt_obj):
                return _ok_result

            # 展示处理信息
            prompt_obj.prompt_print(
                '%s ( %s ):' % (
                    _('convert info'),
                    _('change stander pic name' if self._para_dict['stdpic']
                      else 'use source pic name')
                )
            )
            prompt_obj.prompt_print('  %s: %s' % (_('source file'), self._para_dict['in']))
            prompt_obj.prompt_print('  %s: %s' % (_('out path'), self._para_dict['out']))
            prompt_obj.prompt_print('  %s: %s' % (_('wiki page title'), self._para_dict['real_name']))
            prompt_obj.prompt_print('  %s: %s' % (_('copy pic path'), self._para_dict['pic_dir']))
            prompt_obj.prompt_print('')
            prompt_obj.prompt_print('%s  =================>' % (_('begin convert'), ))
            prompt_obj.prompt_print('')

            # 删除原有复制图片
            self._create_pic_dir()

            # 预处理markdown文件
            prompt_obj.prompt_print('\n%s %s: ' % (_('begin'), _('copy pic file')))
            _md_text = FileTool.get_file_text(self._para_dict['in'], encoding=None)

            # 增加文件名中有()和[]的处理规则的影响支持
            self._para_dict['pre_deal_name'] = False
            if len(re.findall(r'[\(|\)|\[|\]]', self._para_dict['real_name'])) > 0:
                self._para_dict['pre_deal_name'] = True
                _md_text = _md_text.replace(self._para_dict['real_name'], '{{__PRE_DEAL_NAME__}}')

            _temp_text = re.sub(
                r'!\[.*?\]\(.*?\)|\<img .*? /\>',
                self._deal_md_pic,
                _md_text
            )

            if self._para_dict['pre_deal_name']:
                # 转换回来
                _temp_text = _temp_text.replace('{{__PRE_DEAL_NAME__}}', self._para_dict['real_name'])

            prompt_obj.prompt_print('%s %s' % (_('copy pic file'), _('done')))

            with open(
                os.path.join(self._para_dict['out'], self._para_dict['name'] + '_temp.md'),
                "w", encoding='utf-8'
            ) as f:
                f.write(_temp_text)
            prompt_obj.prompt_print('\n%s %s' % (_('pre convert to temp file'), _('done')))

            # 调用Pandoc进行转换处理
            prompt_obj.prompt_print('%s:' % (_('use Pandoc convert'), ))
            if platform.system() == 'Windows':
                # Win平台要先执行chcp 65001命令
                _sys_cmd = 'chcp 65001'
                self._console_global_para['shell_encoding'] = 'utf-8'
                prompt_obj.prompt_print('%s: %s' % (_('execute'), _sys_cmd))
                if(self._exe_syscmd(_sys_cmd, shell_encoding='utf-8') != 0):
                    return CResult(code='20999')

            # 执行转换命令
            _sys_cmd = 'pandoc %s -f markdown -t mediawiki -s -o %s' % (
                os.path.join(self._para_dict['out'], self._para_dict['name'] + '_temp.md'),
                os.path.join(self._para_dict['out'], self._para_dict['real_name'] + '.txt')
            )
            prompt_obj.prompt_print('%s: %s' % (_('execute'), _sys_cmd))
            if(self._exe_syscmd(_sys_cmd, shell_encoding='utf-8') != 0):
                return CResult(code='20999')

            # 删除临时文件
            FileTool.remove_file(os.path.join(
                self._para_dict['out'], self._para_dict['name'] + '_temp.md'))

            prompt_obj.prompt_print('\n=================>  %s %s' % (_('convert'), _('done')))
        except Exception as e:
            _prin_str = '%s (%s):\n%s' % (
                _('execution exception'), str(e), traceback.format_exc()
            )
            prompt_obj.prompt_print(_prin_str)
            return CResult(code='20999')

        # 结束
        return _ok_result

    def _docxtowiki_cmd_dealfun(self, message='', cmd='', cmd_para='', prompt_obj=None, **kwargs):
        """
        将docx格式文件转换为mediawiki格式

        @param {string} message='' - prompt提示信息
        @param {string} cmd - 执行的命令key值
        @param {string} cmd_para - 传入的命令参数（命令后的字符串，去掉第一个空格）
        @param {PromptPlus} prompt_obj=None - 传入调用函数的PromptPlus对象，可以通过该对象的一些方法控制输出显示
        @param {kwargs} - 传入的主进程的初始化kwargs对象

        @returns {CResult} - 命令执行结果，可通过返回错误码10101通知框架退出命令行, 同时也可以通过CResult对象的
            print_str属性要求框架进行打印处理
        """
        _ok_result = CResult(code='00000')
        try:
            if not self._para_dict_check(cmd=cmd, cmd_para=cmd_para, prompt_obj=prompt_obj):
                return _ok_result

            self._para_dict['stdpic'] = True

            # 展示处理信息
            prompt_obj.prompt_print(
                '%s:' % (
                    _('convert info')
                )
            )
            prompt_obj.prompt_print('  %s: %s' % (_('source file'), self._para_dict['in']))
            prompt_obj.prompt_print('  %s: %s' % (_('out path'), self._para_dict['out']))
            prompt_obj.prompt_print('  %s: %s' % (_('wiki page title'), self._para_dict['real_name']))
            prompt_obj.prompt_print('  %s: %s' % (_('copy pic path'), self._para_dict['pic_dir']))
            prompt_obj.prompt_print('')
            prompt_obj.prompt_print('%s  =================>' % (_('begin convert'), ))
            prompt_obj.prompt_print('')

            # 删除原有复制图片
            self._create_pic_dir()

            # 先将docx转换为md
            prompt_obj.prompt_print('%s: ' % (_('change docx file to markdown'), ))
            if platform.system() == 'Windows':
                # Win平台要先执行chcp 65001命令
                _sys_cmd = 'chcp 65001'
                self._console_global_para['shell_encoding'] = 'utf-8'
                prompt_obj.prompt_print('%s: %s' % (_('execute'), _sys_cmd))
                if(self._exe_syscmd(_sys_cmd, shell_encoding='utf-8') != 0):
                    return CResult(code='20999')

            _sys_cmd = 'pandoc %s -f docx -t markdown -s -o %s --extract-media=%s' % (
                self._para_dict['in'],
                os.path.join(self._para_dict['out'], self._para_dict['name'] + '_temp.md'),
                self._para_dict['pic_dir']
            )
            prompt_obj.prompt_print('%s: %s' % (_('execute'), _sys_cmd))
            if(self._exe_syscmd(_sys_cmd, shell_encoding='utf-8') != 0):
                return CResult(code='20999')

            # 预处理markdown文件
            prompt_obj.prompt_print('\n%s %s: ' % (_('begin'), _('begin copy pic file')))
            _md_text = FileTool.get_file_text(os.path.join(
                self._para_dict['out'], self._para_dict['name'] + '_temp.md'), encoding=None)
            # 增加文件名中有()和[]的处理规则的影响支持
            self._para_dict['pre_deal_name'] = False
            if len(re.findall(r'[\(|\)|\[|\]]', self._para_dict['real_name'])) > 0:
                self._para_dict['pre_deal_name'] = True
                _md_text = _md_text.replace(self._para_dict['real_name'], '{{__PRE_DEAL_NAME__}}')

            _temp_text = re.sub(
                r'(!\[.*?\]\(.*?\)|\<img .*? /\>)(\{[width=|height=][\s\S]*?\})*',
                self._deal_md_pic,
                _md_text
            )

            if self._para_dict['pre_deal_name']:
                # 转换回来
                _temp_text = _temp_text.replace('{{__PRE_DEAL_NAME__}}', self._para_dict['real_name'])

            prompt_obj.prompt_print('%s %s' % (_('copy pic file'), _('done')))
            with open(
                os.path.join(self._para_dict['out'], self._para_dict['name'] + '_temp.md'),
                "w", encoding='utf-8'
            ) as f:
                f.write(_temp_text)
            prompt_obj.prompt_print('\n%s %s' % (_('pre convert to temp file'), _('done')))

            # 调用Pandoc进行转换处理
            prompt_obj.prompt_print('\n%s:' % (_('use Pandoc convert'), ))

            # 执行转换命令
            _sys_cmd = 'pandoc %s -f markdown -t mediawiki -s -o %s' % (
                os.path.join(self._para_dict['out'], self._para_dict['name'] + '_temp.md'),
                os.path.join(self._para_dict['out'], self._para_dict['real_name'] + '.txt')
            )
            prompt_obj.prompt_print('%s: %s' % (_('execute'), _sys_cmd))
            if(self._exe_syscmd(_sys_cmd, shell_encoding='utf-8') != 0):
                return CResult(code='20999')

            # 删除临时文件
            FileTool.remove_file(os.path.join(
                self._para_dict['out'], self._para_dict['name'] + '_temp.md'))
            FileTool.remove_dir(os.path.join(self._para_dict['pic_dir'], 'media'))

            prompt_obj.prompt_print('\n=================>  %s %s' % (_('convert'), _('done')))
        except Exception as e:
            _prin_str = '%s (%s):\n%s' % (
                _('execution exception'), str(e), traceback.format_exc()
            )
            prompt_obj.prompt_print(_prin_str)
            return CResult(code='20999')

        # 结束
        return _ok_result

    def _xlstowiki_cmd_dealfun(self, message='', cmd='', cmd_para='', prompt_obj=None, **kwargs):
        """
        将Excel格式文件转换为mediawiki格式

        @param {string} message='' - prompt提示信息
        @param {string} cmd - 执行的命令key值
        @param {string} cmd_para - 传入的命令参数（命令后的字符串，去掉第一个空格）
        @param {PromptPlus} prompt_obj=None - 传入调用函数的PromptPlus对象，可以通过该对象的一些方法控制输出显示
        @param {kwargs} - 传入的主进程的初始化kwargs对象

        @returns {CResult} - 命令执行结果，可通过返回错误码10101通知框架退出命令行, 同时也可以通过CResult对象的
            print_str属性要求框架进行打印处理
        """
        _ok_result = CResult(code='00000')
        try:
            # 参数处理
            _run_para = {
                '-in': '',
                '-out': '',
                '-name': '',
                '-para_name': ''
            }
            _run_para.update(self._cmd_para_to_dict(cmd_para))
            # 参数检查及初始化
            if _run_para['-in'] == '' or not os.path.exists(_run_para['-in']) or not os.path.isfile(_run_para['-in']):
                # 输入文件不存在
                prompt_obj.prompt_print(_('File \'$1\' not exists, please check [-in] para!', _run_para['-in']))
                return CResult(code='20999')

            _run_para['-in'] = os.path.realpath(_run_para['-in'])  # 获取全路径
            _run_para['in_dir'] = FileTool.get_file_path(_run_para['-in'])

            if _run_para['-out'] == '':
                _run_para['-out'] = self._console_global_para['work_path']  # 使用工作路径
            else:
                if not os.path.exists(_run_para['-out']):
                    # 创建对应目录
                    FileTool.create_dir(_run_para['-out'])
                _run_para['-out'] = os.path.realpath(_run_para['-out'])

            if _run_para['-name'] == '':
                _run_para['-name'] = FileTool.get_file_name_no_ext(_run_para['-in'])

            # 展示处理信息
            prompt_obj.prompt_print(
                '%s:' % (
                    _('convert info')
                )
            )
            prompt_obj.prompt_print('  %s: %s' % (_('source file'), _run_para['-in']))
            prompt_obj.prompt_print('  %s: %s' % (_('out path'), _run_para['-out']))
            prompt_obj.prompt_print('')
            prompt_obj.prompt_print('%s  =================>' % (_('begin convert'), ))
            prompt_obj.prompt_print('')

            # 获取转换具体参数
            _convert_para = {
                "show_all_sheet": True,  # 是否显示所有的sheet页
                "sheet_index_list": [],  # 如果show_all_sheet为False, 列出要显示的页索引, 从0开始, 例如[0, 1]
                "sheet_name_list": [],  # 如果show_all_sheet为False, 列出要显示的页名, 例如["sheet1", "sheet2"]
                "default_para": {  # 默认的转换参数，如果转换参数在sheet_index_para_list和sheet_name_para_list找不到, 则会使用这里的参数
                    "has_head": False,  # 是否包含表格头
                    "head_row": 0,  # 表格头所在行
                    "data_row_start": 0,  # 数据开始行, 从0开始
                    "data_row_end": -1,  # 数据结束行, 如果不设置结束行，填-1
                    "data_col_start": 0,  # 数据开始列, 从0开始
                    "data_cols_end": -1,  # 数据结束列，如果不设置结束列，填-1
                    "col_filter": [],  # 列出要显示的列索引，同时也可以通过该参数控制显示的顺序，空数组代表按顺序显示所有列
                    "head_trans_dict": {},  # 表格头的名字转换参数，为一个字典，key为sheet页中字符串, value为要转换显示的字符串
                    "col_trans_dict": {}  # 列数据的转换参数，为一个字典，key为str(列索引)，value为一个值和显示内容的转换字典
                },
                "sheet_index_para_list": {},  # 按页位置定义的个性处理参数，key为索引数字, value为参数(如果参数有缺失的项会使用默认参数)
                "sheet_name_para_list": {}  # 按页名字定义的个性处理参数，key为页名, value为参数(如果参数有缺失的项会使用默认参数)
            }

            _mtfile = os.path.join(_run_para['in_dir'], 'xlstowiki.mt')
            if os.path.exists(_mtfile):
                _temp_para = StringTool.json_to_object(
                    FileTool.get_file_text(_mtfile, encoding=None)
                )
                _para_name = _run_para['-para_name']
                if _para_name == '':
                    _para_name = _run_para['-name']
                if _para_name in _temp_para.keys():
                    prompt_obj.prompt_print(_("get convert para from 'xlstowiki.mt[$1]'", _para_name))
                    _convert_para.update(
                        _temp_para[_para_name]
                    )

            # 打开文件开始逐个处理
            _wiki_text = ''
            _wb = xlrd.open_workbook(filename=_run_para['-in'])
            if _convert_para['show_all_sheet']:
                _convert_para['sheet_name_list'] = _wb.sheet_names()
                _convert_para['sheet_index_list'] = []

            for _index in _convert_para['sheet_index_list']:
                _convert_para['sheet_name_list'].append(_wb.sheet_by_index(_index).name)

            _convert_para['sheet_index_list'] = []

            for _sheet_name in _convert_para['sheet_name_list']:
                # 获取对应的转换参数
                _sheet_para = copy.deepcopy(_convert_para['default_para'])
                _sheet_index = _wb._sheet_names.index(_sheet_name)
                if _sheet_index in _convert_para['sheet_index_para_list'].keys():
                    _sheet_para.update(_convert_para['sheet_index_para_list'][_sheet_index])
                elif _sheet_name in _convert_para['sheet_name_para_list'].keys():
                    _sheet_para.update(_convert_para['sheet_name_para_list'][_sheet_name])

                # 开始处理
                _wiki_text = '%s\n=%s=\n%s' % (
                    _wiki_text,
                    _sheet_name,
                    self._convert_xls_sheet_to_wiki(_wb, _wb.sheet_by_index(_sheet_index), _sheet_para)
                )

            # 将结果写入文件
            with open(
                os.path.join(_run_para['-out'], _run_para['-name'] + '.txt'),
                "w", encoding='utf-8'
            ) as f:
                f.write(_wiki_text)

            prompt_obj.prompt_print('\n=================>  %s %s' % (_('convert'), _('done')))
        except Exception as e:
            _prin_str = '%s (%s):\n%s' % (
                _('execution exception'), str(e), traceback.format_exc()
            )
            prompt_obj.prompt_print(_prin_str)
            return CResult(code='20999')

        # 结束
        return _ok_result

    def _filestowiki_cmd_dealfun(self, message='', cmd='', cmd_para='', prompt_obj=None, **kwargs):
        """
        将指定目录下的文件批量转换为mediawiki格式

        @param {string} message='' - prompt提示信息
        @param {string} cmd - 执行的命令key值
        @param {string} cmd_para - 传入的命令参数（命令后的字符串，去掉第一个空格）
        @param {PromptPlus} prompt_obj=None - 传入调用函数的PromptPlus对象，可以通过该对象的一些方法控制输出显示
        @param {kwargs} - 传入的主进程的初始化kwargs对象

        @returns {CResult} - 命令执行结果，可通过返回错误码10101通知框架退出命令行, 同时也可以通过CResult对象的
            print_str属性要求框架进行打印处理
        """
        _ok_result = CResult(code='00000')
        try:
            # 获取参数及处理参数
            _run_para = {
                '-in': '',
                '-out': '',
                '-add_category': '',
                '-summary': ''
            }
            _run_para.update(self._cmd_para_to_dict(cmd_para))

            if _run_para['-in'] == '':
                _run_para['-in'] = self._console_global_para['work_path']
            else:
                if not os.path.exists(_run_para['-in']) or not os.path.isdir(_run_para['-in']):
                    prompt_obj.prompt_print(_("Path '$1' not exists, please check [-in] para!", _run_para['-in']))
                    return CResult(code='20999')

                _run_para['-in'] = os.path.realpath(_run_para['-in'])
            if _run_para['-out'] == '':
                _run_para['-out'] = self._console_global_para['work_path']
            else:
                if not os.path.exists(_run_para['-out']):
                    # 创建对应目录
                    FileTool.create_dir(_run_para['-out'])
                _run_para['-out'] = os.path.realpath(_run_para['-out'])

            # 是否在文件头添加原文件链接, 创建目录
            if '-add_file_link' in _run_para.keys():
                _run_para['source_file_dir'] = os.path.join(_run_para['-out'], 'source_file_list')
                if not os.path.exists(_run_para['source_file_dir']):
                    FileTool.create_dir(_run_para['source_file_dir'])

            # 遍历文件并进行处理
            prompt_obj.prompt_print(_("begin convert files in $1", _run_para['-in']) + ' =======================>')
            prompt_obj.prompt_print('')
            _file_list = FileTool.get_filelist(path=_run_para['-in'], is_fullname=True)
            for _file in _file_list:
                _ext = FileTool.get_file_ext(_file)
                if _ext == 'md':
                    prompt_obj.prompt_print('%s: %s' % (_('convert'), _file))
                    self._mdtowiki_cmd_dealfun(
                        message=message, cmd='mdtowiki',
                        cmd_para="-in '%s' -out '%s'%s" % (
                            _file, _run_para['-out'], ' -stdpic' if ('-stdpic' in _run_para.keys()) else ''
                        ),
                        prompt_obj=prompt_obj,
                        **kwargs
                    )
                elif _ext == 'docx':
                    prompt_obj.prompt_print('%s: %s' % (_('convert'), _file))
                    self._docxtowiki_cmd_dealfun(
                        message=message, cmd='docxtowiki',
                        cmd_para="-in '%s' -out '%s'" % (
                            _file, _run_para['-out']
                        ),
                        prompt_obj=prompt_obj,
                        **kwargs
                    )
                elif _ext in ['xls', 'xlsx']:
                    prompt_obj.prompt_print('%s: %s' % (_('convert'), _file))
                    self._xlstowiki_cmd_dealfun(
                        message=message, cmd='xlstowiki',
                        cmd_para="-in '%s' -out '%s'" % (
                            _file, _run_para['-out']
                        ),
                        prompt_obj=prompt_obj,
                        **kwargs
                    )
                else:
                    prompt_obj.prompt_print('%s: %s' % (_('not support file format'), _file))
                    continue

                # 进行额外处理
                _filename = FileTool.get_file_name(_file)
                _filename_no_ext = FileTool.get_file_name_no_ext(_filename)
                _before_text = ''  # 在转换文件头要增加的内容
                _after_text = ''  # 在转换文件结尾要增加的内容
                if '-add_file_link' in _run_para.keys():
                    # 复制文件到source_file_list目录
                    shutil.copyfile(_file, os.path.join(_run_para['source_file_dir'], _filename))
                    # 添加到filter.mt文件中
                    _new_filename = _filename.replace('{ns}', '_').replace('{sub}', '_')
                    self._append_to_filter_mt(
                        _run_para['source_file_dir'],
                        '%s|%s|%s' % (_filename, _new_filename, _run_para['-summary'])
                    )
                    _before_text += '原文附件：[[File:%s]]\n\n' % _new_filename

                if '-add_category' in _run_para.keys():
                    # 增加分类信息
                    _categorys = _run_para['-add_category'].split(',')
                    for _category in _categorys:
                        if _category.strip() != '':
                            _before_text += '[[category:%s]]\n' % _category.strip()

                if '-add_comments' in _run_para.keys():
                    # 增加评论信息
                    _after_text += '\n<br>\n<br>\n<comments />'

                # 修改转换后的文件内容，保存到文件中
                _temp_text = FileTool.get_file_text(
                    os.path.join(_run_para['-out'], _filename_no_ext + '.txt'),
                    encoding='utf-8'
                )
                with open(
                    os.path.join(_run_para['-out'], _filename_no_ext + '.txt'),
                    "w", encoding='utf-8'
                ) as f:
                    f.write('%s%s%s' % (_before_text, _temp_text, _after_text))

                # 增加filter.mt信息
                if '-add_filter' in _run_para.keys():

                    self._append_to_filter_mt(
                        _run_para['-out'],
                        '%s|%s|%s|%s' % (
                            _filename_no_ext + '.txt',
                            _filename_no_ext.replace('{ns}', ':').replace('{sub}', '/'),
                            _run_para['-summary'], 'true'
                        )
                    )

            # 处理完成
            prompt_obj.prompt_print('\n=======================>  %s %s' % (_('convert files'), _('done')))
        except Exception as e:
            _prin_str = '%s (%s):\n%s' % (
                _('execution exception'), str(e), traceback.format_exc()
            )
            prompt_obj.prompt_print(_prin_str)
            return CResult(code='20999')

        # 结束
        return _ok_result

    #############################
    # 内部函数
    #############################
    def _para_dict_check(self, cmd='', cmd_para='', prompt_obj=None, **kwargs):
        """
        检查并生成

        @param {string} cmd - 执行的命令key值
        @param {string} cmd_para - 传入的命令参数（命令后的字符串，去掉第一个空格）

        @return {bool} - 如果返回空字符串代表成功，有值的字符串代表失败
        """
        # 获取命令执行参数
        _cmd_list = PromptPlus.get_cmd_para_list(cmd_para)
        self._para_dict = {
            'in': '',
            'out': '',
            'name': '',
            'stdpic': False,
            'pic_dir': '',
            'pic_list': {},
            'pic_num': 0
        }
        for _item in _cmd_list:
            if '-in' == _item[0]:
                self._para_dict['in'] = _item[1].strip("'")
            elif '-out' == _item[0]:
                self._para_dict['out'] = _item[1].strip("'")
            elif '-name' == _item[0]:
                self._para_dict['name'] = _item[1].strip("'")
            elif '-stdpic' == _item[0]:
                self._para_dict['stdpic'] = True

        # 参数检查及初始化
        if self._para_dict['in'] == '' or not os.path.exists(self._para_dict['in']) or not os.path.isfile(self._para_dict['in']):
            # 输入文件不存在
            prompt_obj.prompt_print(_('File \'$1\' not exists, please check [-in] para!', self._para_dict['in']))
            return False

        self._para_dict['in'] = os.path.realpath(self._para_dict['in'])  # 获取全路径
        self._para_dict['in_dir'] = FileTool.get_file_path(self._para_dict['in'])

        if self._para_dict['out'] == '':
            self._para_dict['out'] = self._console_global_para['work_path']  # 使用工作路径
        else:
            if not os.path.exists(self._para_dict['out']):
                # 创建对应目录
                FileTool.create_dir(self._para_dict['out'])
            self._para_dict['out'] = os.path.realpath(self._para_dict['out'])

        if self._para_dict['name'] == '':
            self._para_dict['name'] = FileTool.get_file_name_no_ext(self._para_dict['in'])

        # 保存真正的名字 - 命名空间间隔符用{ns}替代，子页面间隔符用{sub}替代
        self._para_dict['real_name'] = self._para_dict['name']
        self._para_dict['name'] = self._para_dict['name'].replace('{ns}', '_').replace('{sub}', '_')

        self._para_dict['pic_dir'] = os.path.join(
            self._para_dict['out'], self._para_dict['real_name'] + '_copy_pic')

        return True

    def _deal_md_pic(self, match_str):
        """
        针对获取到的md图片路径字符串进行文件处理和替换

        @param {re.Match} match_str - 匹配到的对象

        @return {string} - 替换后的图片字符串
        """
        _str = match_str.group()
        # 提取图片路径信息
        _alt = ''
        _src = ''
        _name = ''
        if _str.startswith('!['):
            # ![img004](mdtowiki_pic/img004.png)的格式
            _p_alt = re.compile(r'!\[(.*?)\]')
            _p_src = re.compile(r'\((.*?)\)')
            _alt = re.findall(_p_alt, _str)[0]
            _src = re.findall(_p_src, _str)[0]
        else:
            # <img src="https://yt-adp.ws.126.net/channel4/1200125_pads_20190404.jpg" alt="163" style="zoom:33%;" />的格式
            _p_alt = re.compile(r'\salt=(.*?)\s')
            _p_src = re.compile(r'\ssrc=(.*?)\s')
            _temp = re.findall(_p_alt, _str)
            if len(_temp) > 0:
                _alt = _temp[0].strip('\'"')
            _temp = re.findall(_p_src, _str)
            if len(_temp) > 0:
                _src = _temp[0].strip('\'"')

        # 增加文件名中有()和[]的处理规则的影响支持
        if self._para_dict['pre_deal_name']:
            # 转换回来
            _src = _src.replace('{{__PRE_DEAL_NAME__}}', self._para_dict['real_name'])
            _alt = _alt.replace('{{__PRE_DEAL_NAME__}}', self._para_dict['real_name'])

        # 检查文件是否已经处理过
        if _src in self._para_dict['pic_list']:
            _name = self._para_dict['pic_list'][_src]
            self._prompt_obj.prompt_print('%s: %s -> %s %s' % (_('copy pic file'), _src, _name, _('done')))
        else:
            # 未处理过
            if self._para_dict['stdpic']:
                # 按顺序命名
                self._para_dict['pic_num'] = self._para_dict['pic_num'] + 1
                _name = '%s_%s_%s.%s' % (
                    self._para_dict['name'], _('embed'),
                    StringTool.fill_fix_string(str(self._para_dict['pic_num']), 5, '0'),
                    FileTool.get_file_ext(_src)
                )
            else:
                # 使用原名称
                _temp_str = _src.replace('\\', '/').replace(' ', '_')
                _index = _temp_str.rfind("/")
                if _index == -1:
                    _name = _temp_str
                else:
                    _name = _temp_str[_index + 1:]

                _name = '%s_%s_%s' % (
                    self._para_dict['name'], _('embed'), _name
                )

            # 加入到清单中
            self._para_dict['pic_list'][_src] = _name

            # 复制或下载文件
            try:
                self._down_md_pic(_src, os.path.join(self._para_dict['pic_dir'], _name))
                self._prompt_obj.prompt_print('%s: %s -> %s %s' % (_('copy pic file'), _src, _name, _('done')))
            except Exception as e:
                # 提示
                self._prompt_obj.prompt_print(
                    '%s: %s -> %s %s ( %s ):\n %s' % (
                        _('copy pic file'), _src, _name, _('execution exception'), str(e),
                        traceback.format_exc()
                    )
                )

        # 改写文件
        if _alt == '':
            return '[[Image:%s]]' % (_name, )
        else:
            return '[[Image:%s|%s]]' % (_name, _alt)

    def _down_md_pic(self, src, dest):
        """
        将图片文件下载到指定路径

        @param {string} src - 要下载的文件路径
        @param {string} dest - 目标文件
        """
        if src.startswith('http://') or src.startswith('https://'):
            # 网络图片，需要下载
            _resp = requests.get(src)
            with open(dest, "wb") as f:
                f.write(_resp.content)
        else:
            # 本地文件，进行复制
            _src_file = os.path.join(self._para_dict['in_dir'], src)
            shutil.copyfile(_src_file, dest)

    def _exe_syscmd(self, cmd, shell_encoding='utf-8'):
        """
        执行系统命令

        @param {string} cmd - 要执行的命令
        @param {string} shell_encoding='utf-8' - 界面编码

        @return {int} - 返回执行结果
        """
        _sp = subprocess.Popen(
            cmd, close_fds=True,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            shell=True
        )
        # 循环等待执行完成
        _exit_code = None
        try:
            while True:
                try:
                    # 打印内容
                    _show_str = _sp.stdout.readline().decode(shell_encoding).strip()
                    if _show_str != '':
                        self._prompt_obj.prompt_print(_show_str)

                    _exit_code = _sp.poll()
                    if _exit_code is not None:
                        # 结束，打印异常日志
                        _show_str = _sp.stdout.read().decode(shell_encoding).strip()
                        if _show_str != '':
                            self._prompt_obj.prompt_print(_show_str)
                        if _exit_code != 0:
                            _show_str = _sp.stderr.read().decode(shell_encoding).strip()
                            if _show_str != '':
                                self._prompt_obj.prompt_print(_show_str)
                        break
                    # 释放一下CPU
                    time.sleep(0.01)
                except KeyboardInterrupt:
                    # 不允许取消
                    self._prompt_obj.prompt_print(_("Command Executing, can't exit execute job!"))
        except KeyboardInterrupt:
            # 遇到 Ctrl + C 退出
            pass

        # 最后返回
        if _exit_code is not None:
            if _exit_code != 0:
                # 执行错误，显示异常
                self._prompt_obj.prompt_print('%s : %d' % (_("Command done, exit code"), _exit_code))
            else:
                self._prompt_obj.prompt_print('%s' % (_("Command execute done"), ))

        return _exit_code

    def _create_pic_dir(self):
        """
        新建或删除图片复制目录
        """
        if os.path.exists(self._para_dict['pic_dir']):
            FileTool.remove_files(path=self._para_dict['pic_dir'])
        else:
            # 创建目录
            FileTool.create_dir(self._para_dict['pic_dir'])

        self._prompt_obj.prompt_print('%s %s' % (_('make pic path'), _('done')))

    def _append_to_filter_mt(self, path, text):
        """
        把信息添加到filter.mt文件中

        @param {string} path - 文件所在路径
        @param {string} text - 要追加的信息
        """
        with open(os.path.join(path, 'filter.mt'), 'a+', encoding='utf-8') as f:
            f.writelines('\n' + text)

    def _convert_xls_sheet_to_wiki(self, wb, sheet, conver_para):
        """
        将Excel的sheet页转换为wiki表格样式

        @param {WorkBook} wb - Excel打开的工作簿
        @param {Sheet} sheet - 要处理的sheet页
        @param {dict} conver_para - 转换参数

        @return {string} - 转换后的wiki显示表格字符串
        """
        # 处理列过滤取值
        _col_filter = conver_para['col_filter']
        if len(_col_filter) == 0:
            if conver_para['data_col_start'] > 0 or conver_para['data_cols_end'] >= 0:
                # 直接将需要的列转换为_col_filter
                if conver_para['data_cols_end'] < 0:
                    conver_para['data_cols_end'] = sheet.ncols - 1
                _col_filter = [_i for _i in range(conver_para['data_col_start'], conver_para['data_cols_end'] + 1)]

        # 先清洗数据到数组中
        _sheet_name = sheet.name
        _head = []
        _data = []
        # 标题行
        if conver_para['has_head']:
            # 处理标题行
            _head = self._xls_rows_to_strlist(sheet.row(conver_para['head_row']))
            if len(_col_filter) > 0:
                _head = [_head[_i] for _i in _col_filter]
            # 显示转换
            _i = 0
            while _i < len(_head):
                if _head[_i] in conver_para['head_trans_dict'].keys():
                    _head[_i] = conver_para['head_trans_dict'][_head[_i]]
                _i += 1

        # 数据数组
        if conver_para['data_row_end'] < 0:
            conver_para['data_row_end'] = sheet.nrows - 1

        _row = conver_para['data_row_start']
        while _row <= conver_para['data_row_end']:
            _row_data = self._xls_rows_to_strlist(sheet.row(_row))
            # 转换显示值
            for _tran_index in conver_para['col_trans_dict'].keys():
                _index_num = int(_tran_index)
                if _row_data[_index_num] in conver_para['col_trans_dict'][_tran_index].keys():
                    _row_data[_index_num] = conver_para['col_trans_dict'][_tran_index][_row_data[_index_num]]

            # 处理显示列
            if len(_col_filter) > 0:
                _row_data = [_row_data[_i] for _i in _col_filter]

            # 加入到数组中
            _data.append(_row_data)
            _row += 1

        # 处理显示的wiki文本
        # 表格标题头
        _wiki_text = '{| class="wikitable sortable"\n|+%s\n!%s\n' % (
            _sheet_name, '\n!'.join(_head)
        )
        # 表格数据
        for _row_data in _data:
            _wiki_text = '%s|-\n|%s\n' % (
                _wiki_text, '\n|'.join(_row_data)
            )
        # 表格结尾
        _wiki_text = '%s%s' % (_wiki_text, '|}\n')

        # 返回结果
        return _wiki_text

    def _xls_rows_to_strlist(self, rows):
        """
        将一行转换为字符串数组返回

        @param {xlrd.sheet.Cell[]} rows - 行数组

        @return {list} - 字符数组
        """
        return [str(row.value) for row in rows]


class MediaWikiSite(CmdBaseFW):
    """
    MediaWiki的网站操作命令
    使用mwclient类支持相应的操作处理
    """
    #############################
    # 构造函数，在里面增加函数映射字典
    #############################

    def _init(self, **kwargs):
        """
        实现类需要覆盖实现的初始化函数

        @param {kwargs} - 传入初始化参数字典（config.xml的init_para字典）

        @throws {exception-type} - 如果初始化异常应抛出异常
        """
        self._CMD_DEALFUN_DICT = {
            'wiki_connect': self._wiki_connect_cmd_dealfun,
            'wiki_reconnect': self._wiki_reconnect_cmd_dealfun,
            'wiki_site': self._wiki_site_cmd_dealfun,
            'wiki_getpage': self._wiki_getpage_cmd_dealfun,
            'wiki_upload': self._wiki_upload_cmd_dealfun,
            'wiki_edit': self._wiki_edit_cmd_dealfun,
            'wiki_contributions': self._wiki_contributions_cmd_dealfun
        }
        self._mwsite = None
        self._console_global_para = RunTool.get_global_var('CONSOLE_GLOBAL_PARA')

    #############################
    # 实际处理函数
    #############################
    def _cmd_dealfun(self, message='', cmd='', cmd_para='', prompt_obj=None, **kwargs):
        """
        通用处理函数，通过cmd区别调用实际的处理函数

        @param {string} message='' - prompt提示信息
        @param {string} cmd - 执行的命令key值
        @param {string} cmd_para - 传入的命令参数（命令后的字符串，去掉第一个空格）
        @param {PromptPlus} prompt_obj=None - 传入调用函数的PromptPlus对象，可以通过该对象的一些方法控制输出显示
        @param {kwargs} - 传入的主进程的初始化kwargs对象

        @returns {CResult} - 命令执行结果，可通过返回错误码10101通知框架退出命令行, 同时也可以通过CResult对象的
            print_str属性要求框架进行打印处理
        """
        # 获取真实执行的函数
        self._prompt_obj = prompt_obj  # 传递到对象内部处理
        _real_dealfun = None  # 真实调用的函数
        if 'ignore_case' in kwargs.keys() and kwargs['ignore_case']:
            # 区分大小写
            if cmd in self._CMD_DEALFUN_DICT.keys():
                _real_dealfun = self._CMD_DEALFUN_DICT[cmd]
        else:
            # 不区分大小写
            if cmd.lower() in self._CMD_DEALFUN_DICT.keys():
                _real_dealfun = self._CMD_DEALFUN_DICT[cmd.lower()]

        # 执行函数
        if _real_dealfun is not None:
            return _real_dealfun(message=message, cmd=cmd, cmd_para=cmd_para, prompt_obj=prompt_obj, **kwargs)
        else:
            prompt_obj.prompt_print(_("'$1' is not support command!", cmd))
            return CResult(code='11404', i18n_msg_paras=(cmd, ))

    #############################
    # 实际处理函数
    #############################
    def _wiki_connect_cmd_dealfun(self, message='', cmd='', cmd_para='', prompt_obj=None, **kwargs):
        """
        连接到wiki网站

        @param {string} message='' - prompt提示信息
        @param {string} cmd - 执行的命令key值
        @param {string} cmd_para - 传入的命令参数（命令后的字符串，去掉第一个空格）
        @param {PromptPlus} prompt_obj=None - 传入调用函数的PromptPlus对象，可以通过该对象的一些方法控制输出显示
        @param {kwargs} - 传入的主进程的初始化kwargs对象

        @returns {CResult} - 命令执行结果，可通过返回错误码10101通知框架退出命令行, 同时也可以通过CResult对象的
            print_str属性要求框架进行打印处理
        """
        _ok_result = CResult(code='00000')
        try:
            self._site_para = {
                'host': '',
                'path=': '/',
                'scheme=': 'http',
                'auth=': 'no-auth',
                'username=': '',
                'password=': '',
                'client_pem=': '',
                'key_pem=': '',
                'consumer_token=': None,
                'consumer_secret=': None,
                'access_token=': None,
                'access_secret=': None
            }
            self._site_para.update(self._cmd_para_to_dict(cmd_para))
            if '{para}1' not in self._site_para.keys():
                prompt_obj.prompt_print(_('you must give the $1 para!', 'host'))
                return CResult(code='20999')

            self._site_para['host'] = self._site_para['{para}1']

            # 连接到wiki网站
            self._connect_to_wikisite()

            # 返回提示
            prompt_obj.prompt_print(
                '%s: %s://%s\n %s:%s  %s:%s' % (
                    _('connect to wikisite'), self._site_para['scheme='],
                    self._site_para['host'], _('auth type'), self._site_para['auth='],
                    _('username'), self._site_para['username=']
                )
            )
        except Exception as e:
            _prin_str = '%s (%s):\n%s' % (
                _('execution exception'), str(e), traceback.format_exc()
            )
            prompt_obj.prompt_print(_prin_str)
            return CResult(code='20999')

        # 结束
        return _ok_result

    def _wiki_reconnect_cmd_dealfun(self, message='', cmd='', cmd_para='', prompt_obj=None, **kwargs):
        """
        重新连接wiki网站(cookie超时的情况)

        @param {string} message='' - prompt提示信息
        @param {string} cmd - 执行的命令key值
        @param {string} cmd_para - 传入的命令参数（命令后的字符串，去掉第一个空格）
        @param {PromptPlus} prompt_obj=None - 传入调用函数的PromptPlus对象，可以通过该对象的一些方法控制输出显示
        @param {kwargs} - 传入的主进程的初始化kwargs对象

        @returns {CResult} - 命令执行结果，可通过返回错误码10101通知框架退出命令行, 同时也可以通过CResult对象的
            print_str属性要求框架进行打印处理
        """
        _ok_result = CResult(code='00000')
        try:
            if self._mwsite is None:
                prompt_obj.prompt_print(_('not connect to wiki site yet, please use wikiconnect to connect!'))
                return CResult(code='20999')

            # 连接到wiki网站
            self._connect_to_wikisite()

            # 返回提示
            prompt_obj.prompt_print(
                '%s: %s://%s\n %s:%s  %s:%s' % (
                    _('connect to wikisite'), self._site_para['scheme='],
                    self._site_para['host'], _('auth type'), self._site_para['auth='],
                    _('username'), self._site_para['username=']
                )
            )
        except Exception as e:
            _prin_str = '%s (%s):\n%s' % (
                _('execution exception'), str(e), traceback.format_exc()
            )
            prompt_obj.prompt_print(_prin_str)
            return CResult(code='20999')

        # 结束
        return _ok_result

    def _wiki_site_cmd_dealfun(self, message='', cmd='', cmd_para='', prompt_obj=None, **kwargs):
        """
        显示当前已连接的wiki网站

        @param {string} message='' - prompt提示信息
        @param {string} cmd - 执行的命令key值
        @param {string} cmd_para - 传入的命令参数（命令后的字符串，去掉第一个空格）
        @param {PromptPlus} prompt_obj=None - 传入调用函数的PromptPlus对象，可以通过该对象的一些方法控制输出显示
        @param {kwargs} - 传入的主进程的初始化kwargs对象

        @returns {CResult} - 命令执行结果，可通过返回错误码10101通知框架退出命令行, 同时也可以通过CResult对象的
            print_str属性要求框架进行打印处理
        """
        if self._mwsite is None:
            prompt_obj.prompt_print(_('not connect to wiki site yet, please use wikiconnect to connect!'))
            return CResult(code='20999')

        # 返回提示
        prompt_obj.prompt_print(
            '%s: %s://%s\n %s:%s  %s:%s' % (
                _('connect to wikisite'), self._site_para['scheme='],
                self._site_para['host'], _('auth type'), self._site_para['auth='],
                _('username'), self._site_para['username=']
            )
        )
        return CResult(code='00000')

    def _wiki_getpage_cmd_dealfun(self, message='', cmd='', cmd_para='', prompt_obj=None, **kwargs):
        """
        获取指定的wiki页面

        @param {string} message='' - prompt提示信息
        @param {string} cmd - 执行的命令key值
        @param {string} cmd_para - 传入的命令参数（命令后的字符串，去掉第一个空格）
        @param {PromptPlus} prompt_obj=None - 传入调用函数的PromptPlus对象，可以通过该对象的一些方法控制输出显示
        @param {kwargs} - 传入的主进程的初始化kwargs对象

        @returns {CResult} - 命令执行结果，可通过返回错误码10101通知框架退出命令行, 同时也可以通过CResult对象的
            print_str属性要求框架进行打印处理
        """
        if self._mwsite is None:
            prompt_obj.prompt_print(_('not connect to wiki site yet, please use wikiconnect to connect!'))
            return CResult(code='20999')

        _ok_result = CResult(code='00000')
        try:
            # 处理参数
            self._getpage_para = {
                'title': '',
                '-output': '',
                '-filename': None,
            }
            self._getpage_para.update(self._cmd_para_to_dict(cmd_para))
            if '{para}1' not in self._getpage_para.keys():
                prompt_obj.prompt_print(_('you must give the $1 para!', 'title'))
                return CResult(code='20999')

            self._getpage_para['title'] = self._getpage_para['{para}1']
            if self._getpage_para['-output'] == '':
                self._getpage_para['-output'] = self._console_global_para['work_path']

            # 创建输出目录
            if not os.path.exists(self._getpage_para['-output']):
                FileTool.create_dir(self._getpage_para['-output'])
            elif os.path.isfile(self._getpage_para['-output']):
                prompt_obj.prompt_print(_('output path error'))
                return CResult(code='20999')

            # 设置获取内部链接的层数
            _max_level = 3
            if '-L' in self._getpage_para.keys():
                if self._getpage_para['-L'] != '':
                    _max_level = int(self._getpage_para['-L'])

            # 执行页面获取
            self._get_page_objs = dict()
            self._get_wiki_page(
                self._getpage_para['title'], self._getpage_para['-output'],
                filename=self._getpage_para['-filename'],
                down_file=('-d' in self._getpage_para.keys()),
                get_links=('-L' in self._getpage_para.keys()),
                max_level=_max_level,
                expandtemplates=('-e' in self._getpage_para.keys()),
                get_templates=('-t' in self._getpage_para.keys())
            )
        except Exception as e:
            _prin_str = '%s (%s):\n%s' % (
                _('execution exception'), str(e), traceback.format_exc()
            )
            prompt_obj.prompt_print(_prin_str)
            return CResult(code='20999')

        # 结束
        return _ok_result

    def _wiki_upload_cmd_dealfun(self, message='', cmd='', cmd_para='', prompt_obj=None, **kwargs):
        """
        上传文件到wiki网站

        @param {string} message='' - prompt提示信息
        @param {string} cmd - 执行的命令key值
        @param {string} cmd_para - 传入的命令参数（命令后的字符串，去掉第一个空格）
        @param {PromptPlus} prompt_obj=None - 传入调用函数的PromptPlus对象，可以通过该对象的一些方法控制输出显示
        @param {kwargs} - 传入的主进程的初始化kwargs对象

        @returns {CResult} - 命令执行结果，可通过返回错误码10101通知框架退出命令行, 同时也可以通过CResult对象的
            print_str属性要求框架进行打印处理
        """
        if self._mwsite is None:
            prompt_obj.prompt_print(_('not connect to wiki site yet, please use wikiconnect to connect!'))
            return CResult(code='20999')

        try:
            # 处理参数
            self._upload_para = {
                '-input': '',
                '-filter': '',
                '-filter_encoding': None,
                '-desc': '',
                'file_list': None
            }
            self._upload_para.update(self._cmd_para_to_dict(cmd_para))

            if self._upload_para['-input'] == '':
                # 如果不传参数默认使用工作路径
                self._upload_para['-input'] = self._console_global_para['work_path']

            # 获取文件列表
            self._upload_para['file_list'] = FileTool.get_filelist(
                path=self._upload_para['-input'],
                is_fullname=False
            )
            # 删除过滤文件
            if 'filter.mt' in self._upload_para['file_list']:
                self._upload_para['file_list'].remove('filter.mt')
                if self._upload_para['-filter'] == '':
                    # 有过滤条件且没有指定
                    self._upload_para['-filter'] = os.path.join(
                        self._upload_para['-input'], 'filter.mt'
                    )

            # 处理过滤清单
            if self._upload_para['-filter'] != '':
                _text = FileTool.get_file_text(
                    self._upload_para['-filter'], encoding=self._upload_para['-filter_encoding']
                ).replace('\r\n', '\n').replace('\r', '\n')
                self._upload_para['file_list'] = _text.split('\n')

            # 开始进行文件上传
            self._upload_objs = dict()
            self._upload_files(
                self._upload_para['-input'], self._upload_para['file_list'],
                rewrite=('-R' in self._upload_para.keys()),
                desc=self._upload_para['-desc'],
                ignore=('-I' in self._upload_para.keys())
            )
        except Exception as e:
            _prin_str = '%s (%s):\n%s' % (
                _('execution exception'), str(e), traceback.format_exc()
            )
            prompt_obj.prompt_print(_prin_str)
            return CResult(code='20999')

        # 结束
        return CResult(code='20999')

    def _wiki_edit_cmd_dealfun(self, message='', cmd='', cmd_para='', prompt_obj=None, **kwargs):
        """
        编辑页面并提交wiki网站

        @param {string} message='' - prompt提示信息
        @param {string} cmd - 执行的命令key值
        @param {string} cmd_para - 传入的命令参数（命令后的字符串，去掉第一个空格）
        @param {PromptPlus} prompt_obj=None - 传入调用函数的PromptPlus对象，可以通过该对象的一些方法控制输出显示
        @param {kwargs} - 传入的主进程的初始化kwargs对象

        @returns {CResult} - 命令执行结果，可通过返回错误码10101通知框架退出命令行, 同时也可以通过CResult对象的
            print_str属性要求框架进行打印处理
        """
        if self._mwsite is None:
            prompt_obj.prompt_print(_('not connect to wiki site yet, please use wikiconnect to connect!'))
            return CResult(code='20999')

        try:
            # 处理参数
            self._edit_para = {
                '-input': '',
                '-encoding': None,
                '-filter': '',
                '-filter_encoding': None,
                '-summary': '',
                'file_list': None,
                '-FD': ''
            }
            self._edit_para.update(self._cmd_para_to_dict(cmd_para))

            if self._edit_para['-input'] == '':
                # 如果不传参数默认使用工作路径
                self._edit_para['-input'] = self._console_global_para['work_path']

            # 获取文件列表
            self._edit_para['file_list'] = FileTool.get_filelist(
                path=self._edit_para['-input'],
                is_fullname=False
            )
            # 删除过滤文件
            if 'filter.mt' in self._edit_para['file_list']:
                self._edit_para['file_list'].remove('filter.mt')
                if self._edit_para['-filter'] == '':
                    # 有过滤条件且没有指定
                    self._edit_para['-filter'] = os.path.join(
                        self._edit_para['-input'], 'filter.mt'
                    )

            # 处理过滤清单
            if self._edit_para['-filter'] != '':
                _text = FileTool.get_file_text(
                    self._edit_para['-filter'], encoding=self._edit_para['-filter_encoding']
                ).replace('\r\n', '\n').replace('\r', '\n')
                self._edit_para['file_list'] = _text.split('\n')

            # 开始进行页面编辑
            self._edit_objs = dict()
            self._upload_objs = dict()
            self._edit_pages(
                self._edit_para['-input'], self._edit_para['file_list'],
                rewrite=('-R' in self._edit_para.keys()),
                summary=self._edit_para['-summary'],
                encoding=self._edit_para['-encoding'],
                upload_files=('-U' in self._edit_para.keys()),
                file_rewrite=('-FR' in self._edit_para.keys()),
                file_ignore=('-FI' in self._edit_para.keys()),
                file_desc=self._edit_para['-FD']
            )

        except Exception as e:
            _prin_str = '%s (%s):\n%s' % (
                _('execution exception'), str(e), traceback.format_exc()
            )
            prompt_obj.prompt_print(_prin_str)
            return CResult(code='20999')

        # 结束
        return CResult(code='00000')

    def _wiki_contributions_cmd_dealfun(self, message='', cmd='', cmd_para='', prompt_obj=None, **kwargs):
        """
        生成网站贡献排名页面

        @param {string} message='' - prompt提示信息
        @param {string} cmd - 执行的命令key值
        @param {string} cmd_para - 传入的命令参数（命令后的字符串，去掉第一个空格）
        @param {PromptPlus} prompt_obj=None - 传入调用函数的PromptPlus对象，可以通过该对象的一些方法控制输出显示
        @param {kwargs} - 传入的主进程的初始化kwargs对象

        @returns {CResult} - 命令执行结果，可通过返回错误码10101通知框架退出命令行, 同时也可以通过CResult对象的
            print_str属性要求框架进行打印处理
        """
        if self._mwsite is None:
            prompt_obj.prompt_print(_('not connect to wiki site yet, please use wikiconnect to connect!'))
            return CResult(code='20999')

        try:
            # 处理参数
            _contributions_para = {
                '-para_file': '',
                '-out': '',
                '-name': '',
                '-add_category': '',
                '-summary': ''
            }
            _contributions_para.update(self._cmd_para_to_dict(cmd_para))

            if _contributions_para['-out'] == '':
                # 如果不传参数默认使用工作路径
                _contributions_para['-out'] = self._console_global_para['work_path']
            else:
                if not os.path.exists(_contributions_para['-out']):
                    # 创建对应目录
                    FileTool.create_dir(_contributions_para['-out'])
                _contributions_para['-out'] = os.path.realpath(_contributions_para['-out'])

            if _contributions_para['-para_file'] == '':
                _contributions_para['-para_file'] = os.path.join(
                    _contributions_para['-out'], 'contributions.json'
                )

            _para_json = StringTool.json_to_object(
                FileTool.get_file_text(_contributions_para['-para_file'], encoding=None)
            )

            if _contributions_para['-name'] == '':
                _contributions_para['-name'] = _('Contribution_ranking')

            # 尝试获取所有页面
            _now = datetime.datetime.now()
            _now_str = _now.strftime("%Y-%m-%d")
            _last_month = (_now - datetime.timedelta(days=30)).strftime("%Y-%m-%d")
            _last_week = (_now - datetime.timedelta(days=7)).strftime("%Y-%m-%d")

            # 机构发布内容排名
            prompt_obj.prompt_print(_('get team publish ranking data') + '....')
            _namespace_ranking_para = _para_json[self._site_para['host']]['namespace_ranking']
            if 'data' not in _namespace_ranking_para.keys():
                _namespace_ranking_para['data'] = dict()
            else:
                _namespace_ranking_para['data'].clear()

            for _ns in _namespace_ranking_para['ranking_ns']:
                self._prompt_obj.prompt_print(
                    _('deal with [$1]', _ns), end=': '
                )
                _count_dict = self._get_ns_page_count(
                    _namespace_ranking_para['ns_dict'][_ns], _last_month, _last_week
                )
                if _ns in _namespace_ranking_para['level_dict']:
                    for _sub_ns in _namespace_ranking_para['level_dict'][_ns]:
                        _sub_count_dict = self._get_ns_page_count(
                            _namespace_ranking_para['ns_dict'][_sub_ns], _last_month, _last_week
                        )
                        _count_dict['count'] += _sub_count_dict['count']
                        _count_dict['last_month_add'] += _sub_count_dict['last_month_add']
                        _count_dict['last_month_change'] += _sub_count_dict['last_month_change']
                        _count_dict['last_week_add'] += _sub_count_dict['last_week_add']
                        _count_dict['last_week_change'] += _sub_count_dict['last_week_change']
                # 增加排序字段
                _count_dict['order'] = _count_dict['count'] * 100 + (_count_dict['last_month_add'] + _count_dict['last_month_change']) * 10 + (_count_dict['last_week_add'] + _count_dict['last_week_change'])
                # 添加到文件的字典中
                _namespace_ranking_para['data'][_ns] = _count_dict
                self._prompt_obj.prompt_print(_('done'))

            # 进行字典排序
            _namespace_ranking_para['count day'] = _now_str
            _namespace_ranking_para['sorted_data'] = sorted(
                _namespace_ranking_para['data'].items(),
                key=lambda d: d[1].get('order', 0),
                reverse=True
            )

            # 个人贡献排名
            prompt_obj.prompt_print(_('get person publish ranking data') + '....')
            _person_ranking_para = _para_json[self._site_para['host']]['person_ranking']
            if 'data' not in _person_ranking_para.keys():
                _person_ranking_para['data'] = dict()
            else:
                _person_ranking_para['data'].clear()
            # 执行处理
            _person_dict = self._get_person_ranking_data(_person_ranking_para, _last_month, _last_week)

            # 添加到字典中
            _person_ranking_para['count day'] = _now_str
            _person_ranking_para['data'] = _person_dict

            # 排序
            _person_ranking_para['sorted_data_total'] = sorted(
                _person_ranking_para['data'].items(),
                key=lambda d: d[1].get('total_ranking_scroe', 0),
                reverse=True
            )
            _person_ranking_para['sorted_data_month'] = sorted(
                _person_ranking_para['data'].items(),
                key=lambda d: d[1].get('last_month_ranking_scroe', 0),
                reverse=True
            )
            _person_ranking_para['sorted_data_week'] = sorted(
                _person_ranking_para['data'].items(),
                key=lambda d: d[1].get('last_week_ranking_scroe', 0),
                reverse=True
            )

            # 写回文件中
            with open(
                _contributions_para['-para_file'], "w", encoding='utf-8'
            ) as f:
                f.write(json.dumps(_para_json, ensure_ascii=False, indent=2))

            # 生成页面文件
            prompt_obj.prompt_print(_('create ranking page') + '....', end=' ')

            # 团队贡献排行
            _wiki_text = '%s: %s\n\n\n=%s=\n%s\n{| class="wikitable"\n|+%s\n!%s\n' % (
                _('statistical date'), _now_str,
                '%s %s' % (_('team'), _('contribution ranking')),
                _namespace_ranking_para['description'],
                '%s %s' % (_('team'), _('contribution ranking')),
                '\n!'.join(
                    [
                        _('rank'), _('team'), _('publish page count'), _('last month add'),
                        _('last month change'), _('last week add'), _('last week change'),
                    ])
            )
            _i = 1
            for _row_data in _namespace_ranking_para['sorted_data']:
                _wiki_text = '%s|-\n|%s\n' % (
                    _wiki_text, '\n|'.join([
                        str(_i), _row_data[0], str(_row_data[1]['count']),
                        str(_row_data[1]['last_month_add']), str(_row_data[1]['last_month_change']),
                        str(_row_data[1]['last_week_add']), str(_row_data[1]['last_week_change']),
                    ])
                )
                _i += 1

            _wiki_text = '%s%s' % (_wiki_text, '|}\n')

            # 总排行
            _wiki_text = '%s\n\n=%s=\n==%s==\n%s\n{| class="wikitable"\n|+%s\n!%s\n' % (
                _wiki_text, '%s %s' % (_('person'), _('contribution ranking')),
                '%s %s' % (_('total'), _('contribution ranking')),
                _person_ranking_para['description_total'],
                '%s %s' % (_('total'), _('contribution ranking')),
                '\n!'.join([
                    _('rank'), _('user'), _('add page count'), _('change page count'), _('ranking scroe')
                ])
            )

            _i = 1
            for _row_data in _person_ranking_para['sorted_data_total']:
                if _i < _person_ranking_para['top'] and _row_data[1]['total_ranking_scroe'] > 0:
                    _wiki_text = '%s|-\n|%s\n' % (
                        _wiki_text, '\n|'.join([
                            str(_i), _row_data[0], str(_row_data[1]['total_add']),
                            str(_row_data[1]['total_change']),
                            str(round(_row_data[1]['total_ranking_scroe'], 2))
                        ])
                    )
                else:
                    break
                _i += 1

            _wiki_text = '%s%s' % (_wiki_text, '|}\n')

            # 月榜
            _wiki_text = '%s\n\n==%s==\n%s\n{| class="wikitable"\n|+%s\n!%s\n' % (
                _wiki_text,
                '%s %s' % (_('last month'), _('contribution ranking')),
                _person_ranking_para['description_last_month'],
                '%s %s' % (_('last month'), _('contribution ranking')),
                '\n!'.join([
                    _('rank'), _('user'), _('add page count'), _('change page count'), _('ranking scroe')
                ])
            )

            _i = 1
            for _row_data in _person_ranking_para['sorted_data_month']:
                if _i < _person_ranking_para['top'] and _row_data[1]['last_month_ranking_scroe'] > 0:
                    _wiki_text = '%s|-\n|%s\n' % (
                        _wiki_text, '\n|'.join([
                            str(_i), _row_data[0], str(_row_data[1]['last_month_add']),
                            str(_row_data[1]['last_month_change']),
                            str(round(_row_data[1]['last_month_ranking_scroe'], 2))
                        ])
                    )
                else:
                    break
                _i += 1

            _wiki_text = '%s%s' % (_wiki_text, '|}\n')

            # 周榜
            _wiki_text = '%s\n\n==%s==\n%s\n{| class="wikitable"\n|+%s\n!%s\n' % (
                _wiki_text,
                '%s %s' % (_('last week'), _('contribution ranking')),
                _person_ranking_para['description_last_week'],
                '%s %s' % (_('last week'), _('contribution ranking')),
                '\n!'.join([
                    _('rank'), _('user'), _('add page count'), _('change page count'), _('ranking scroe')
                ])
            )

            _i = 1
            for _row_data in _person_ranking_para['sorted_data_week']:
                if _i < _person_ranking_para['top'] and _row_data[1]['last_week_ranking_scroe'] > 0:
                    _wiki_text = '%s|-\n|%s\n' % (
                        _wiki_text, '\n|'.join([
                            str(_i), _row_data[0], str(_row_data[1]['last_week_add']),
                            str(_row_data[1]['last_week_change']),
                            str(round(_row_data[1]['last_week_ranking_scroe'], 2))
                        ])
                    )
                else:
                    break
                _i += 1

            _wiki_text = '%s%s' % (_wiki_text, '|}\n')

            _before_text = ''
            if '-add_category' in _contributions_para.keys():
                # 增加分类信息
                _categorys = _contributions_para['-add_category'].split(',')
                for _category in _categorys:
                    if _category.strip() != '':
                        _before_text += '[[category:%s]]\n' % _category.strip()

            # 写入文件
            with open(
                os.path.join(_contributions_para['-out'], _contributions_para['-name'] + '.txt'),
                "w", encoding='utf-8'
            ) as f:
                f.write('%s%s' % (_before_text, _wiki_text))

            # 增加filter.mt信息
            if '-add_filter' in _contributions_para.keys():
                self._append_to_filter_mt(
                    _contributions_para['-out'],
                    '%s|%s|%s|%s' % (
                        _contributions_para['-name'] + '.txt',
                        _contributions_para['-name'].replace('{ns}', ':').replace('{sub}', '/'),
                        _contributions_para['-summary'], 'true'
                    )
                )

            # 完成处理
            prompt_obj.prompt_print(_('done'))
        except Exception as e:
            _prin_str = '%s (%s):\n%s' % (
                _('execution exception'), str(e), traceback.format_exc()
            )
            prompt_obj.prompt_print(_prin_str)
            return CResult(code='20999')

        # 结束
        return CResult(code='00000')

    #############################
    # 内部函数
    #############################
    def _connect_to_wikisite(self):
        """
        连接到wiki网站
        """
        _client_certificate = None
        if self._site_para['auth='] == 'ssl':
            if self._site_para['key_pem='] == '':
                _client_certificate = self._site_para['client_pem=']
            else:
                _client_certificate = (
                    self._site_para['client_pem='], self._site_para['key_pem='])

        _httpauth = None
        if self._site_para['auth='] == 'http':
            _httpauth = (self._site_para['username='], self._site_para['password='])

        self._mwsite = mwclient.Site(
            self._site_para['host'],
            path=self._site_para['path='],
            scheme=self._site_para['scheme='],
            client_certificate=_client_certificate,
            httpauth=_httpauth,
            clients_useragent='mediawikiTool/%s (snakeclub@163.com)' % __VERSION__,
            consumer_token=self._site_para['consumer_token='],
            consumer_secret=self._site_para['consumer_secret='],
            access_token=self._site_para['access_token='],
            access_secret=self._site_para['access_secret=']
        )

        # 登陆验证
        if self._site_para['auth='] == 'old-login':
            self._mwsite.login(
                username=self._site_para['username='], password=self._site_para['password=']
            )

    def _get_wiki_page(self, title, output, filename=None, down_file=False, get_links=False,
                       max_level=3, current_level=0, expandtemplates=False, get_templates=False):
        """
        获取wiki指定页面

        @param {string} title - 页面标题
        @param {string} output - 输出路径
        @param {string} filename=None - 保存页面文件名
        @param {bool} down_file=False - 是否下载页面包含的文件
        @param {bool} get_links=False - 是否下载页面包含的内部链接页面
        @param {int} max_level=3 - 下载内部链接页面的最大层级
        @param {int} current_level=0 - 当前处理层级
        @param {bool} expandtemplates=False - 是否展开模板
        @param {bool} get_templates=False - 是否获取页面包含的模板
        """
        if title in self._get_page_objs.keys():
            self._prompt_obj.prompt_print(_('page [$1] has been processed', title))
            return
        self._get_page_objs[title] = ''  # 加入到已处理列表

        self._prompt_obj.prompt_print('%s: %s =====================>' % (_('getting page'), title))
        _page = self._mwsite.pages[title]
        if not _page.exists:
            self._prompt_obj.prompt_print(_('get wiki page error: page [$1] not exists!', title))
            return

        # 获取页面内容
        _filename = filename
        if filename is None:
            _filename = title.replace(':', '{ns}').replace('/', '{sub}') + '.txt'

        # 写入文件
        with open(os.path.join(output, _filename), "w", encoding='utf-8') as f:
            f.write(_page.text(expandtemplates=expandtemplates))

        self._prompt_obj.prompt_print('%s %s' % (_('get page [$1] text', title), _('done')))

        _filename_no_ext = FileTool.get_file_name_no_ext(_filename)
        # 判断是否下载页面包含的文件
        if down_file:
            self._prompt_obj.prompt_print('\n%s:' % (_('download files in page [$1]', title)))
            # 创建目录
            _file_dir = os.path.join(output, _filename_no_ext + '_copy_pic')
            if os.path.exists(_file_dir):
                FileTool.remove_files(_file_dir)
            else:
                FileTool.create_dir(_file_dir)
            # 下载文件
            for _image in _page.images():
                if _image.name in self._get_page_objs.keys():
                    self._prompt_obj.prompt_print(_('resource [$1] has been processed', _image.name))
                    continue
                self._get_page_objs[_image.name] = ''  # 加入到已处理列表

                _image_name = _image.name.replace(' ', '_')
                _nameindex = _image_name.find(':')
                if _nameindex > -1:
                    _image_name = _image_name[_nameindex + 1:]
                with open(os.path.join(_file_dir, _image_name), 'wb') as fd:
                    _image.download(fd)
                self._prompt_obj.prompt_print('%s %s' % (_('download file [$1]', _image_name), _('done')))

        # 判断是否下载内部链接页面
        if get_links and current_level < max_level:
            self._prompt_obj.prompt_print('\n%s:\n' % (_('get link_pages on page [$1]', title)))
            for _link in _page.links():
                if _link.name in self._get_page_objs.keys():
                    self._prompt_obj.prompt_print(_('resource [$1] has been processed', _link.name))
                    continue

                self._get_wiki_page(
                    _link.name, output, down_file=down_file, get_links=get_links,
                    max_level=max_level, current_level=current_level+1,
                    expandtemplates=expandtemplates, get_templates=get_templates
                )
                self._prompt_obj.prompt_print('\n%s %s' % (_('get link_page [$1]', _link.name), _('done')))

        # 判断是否下载页面使用到的所有模板
        if get_templates:
            self._prompt_obj.prompt_print('\n%s:\n' % (_('get template_pages on page [$1]', title)))
            for _template in _page.templates():
                if _template.name in self._get_page_objs.keys():
                    self._prompt_obj.prompt_print(_('resource [$1] has been processed', _template.name))
                    continue

                self._get_wiki_page(
                    _template.name, output, down_file=True, get_links=False,
                    max_level=max_level, current_level=current_level+1,
                    expandtemplates=False,
                    get_templates=True
                )
                self._prompt_obj.prompt_print('\n%s %s' % (_('get template_page [$1]', _template.name), _('done')))

    def _upload_files(self, input, file_list, rewrite=False, desc='', ignore=False):
        """
        上传文件

        @param {string} input - 上传文件路径
        @param {list} file_list - 上传的文件清单,每行格式为'文件名|上传名|描述'
        @param {bool} rewrite=False - 如果文件已存在，是否覆盖
        @param {string} desc='' - 通用描述
        @param {bool} ignore=False - 如果为True时忽略警告强制执行
        """
        self._prompt_obj.prompt_print('%s: %s =====================>' % (_('uploading files'), input))
        for _file in file_list:
            # 处理基本信息
            _file_info = _file.split('|')
            _filename = _file_info[0].strip()
            if _filename == '':
                # 增加兼容性，允许空行
                continue

            _upload_name = ''
            _desc = ''
            if len(_file_info) > 1 and _file_info[1].strip() != '':
                _upload_name = _file_info[1].strip()
            else:
                _upload_name = _filename
            if len(_file_info) > 2 and _file_info[2].strip() != '':
                _desc = _file_info[2].strip()
            else:
                _desc = desc

            # 判断文件是否已处理
            if _filename in self._upload_objs.keys():
                self._prompt_obj.prompt_print(_('resource [$1] has been processed', _filename))
                continue
            self._upload_objs[_filename] = ''

            _image = self._mwsite.images[_upload_name]
            if _image.exists and not rewrite:
                self._prompt_obj.prompt_print(_('filename [$1] has been in wiki site!', _upload_name))
                continue

            # 处理上传操作
            try:
                _result = self._mwsite.upload(
                    open(os.path.join(input, _filename), 'rb'),
                    _upload_name, _desc, ignore=ignore
                )
            except Exception as e:
                _prin_str = '%s %s (%s):\n%s' % (
                    _('upload file [$1] > [$2]', _filename, _upload_name),
                    _('fail'), str(e), traceback.format_exc()
                )
                self._prompt_obj.prompt_print(_prin_str)
                continue

            if ('result' in _result.keys() and _result['result'] == 'Success') or ('upload' in _result.keys() and 'result' in _result['upload'].keys() and _result['upload']['result'] == 'Success'):
                self._prompt_obj.prompt_print('%s %s' % (_('upload file [$1] > [$2]', _filename, _upload_name), _('done')))
                if 'warnings' in _result.keys():
                    self._prompt_obj.prompt_print('%s:\n%s\n' % (_('upload [$1] with warnings', _filename), _result['warnings']))
            else:
                self._prompt_obj.prompt_print('%s %s:\n%s\n' % (
                    _('upload file [$1] > [$2]', _filename, _upload_name), _('fail'),
                    str(_result)
                ))

    def _edit_pages(self, input, file_list, rewrite=False, summary='', encoding=None,
                    upload_files=False, file_rewrite=False, file_ignore=False, file_desc=''):
        """
        编辑页面

        @param {string} input - 页面文件路径
        @param {list} file_list - 页面的文件清单,每行格式为'文件名|页面标题(含命名空间)|摘要|是否上传附件(true/false)'
        @param {bool} rewrite=False - 如果页面已存在，是否覆盖
        @param {string} summary='' - 摘要
        @param {string} encoding=None - 打开文件的编码
        @param {bool} upload_files=False - 是否上传附件
        @param {bool} file_rewrite=False - 如果文件已存在，是否覆盖
        @param {bool} file_ignore=False - 如果为True时忽略警告强制执行
        @param {string} file_desc='' - 文件通用描述
        """
        self._prompt_obj.prompt_print('%s: %s =====================>' % (_('editing pages'), input))
        for _file in file_list:
            # 处理基本信息
            _file_info = _file.split('|')
            _filename = _file_info[0].strip()
            if _filename == '':
                # 增加兼容性，允许空行
                continue

            _title = ''
            _summary = ''
            _upload_files = upload_files
            if len(_file_info) > 1 and _file_info[1].strip() != '':
                _title = _file_info[1].strip()
            else:
                _title = FileTool.get_file_name_no_ext(_filename)
            _title = _title.replace('{ns}', ':').replace('{sub}', '/')

            if len(_file_info) > 2 and _file_info[2].strip() != '':
                _summary = _file_info[2].strip()
            else:
                _summary = summary

            if len(_file_info) > 3 and _file_info[3].strip() != '':
                if _file_info[3].strip() == 'true':
                    _upload_files = True
                else:
                    _upload_files = False

            # 判断文件是否已处理
            if _filename in self._edit_objs.keys():
                self._prompt_obj.prompt_print(_('page [$1] has been processed', _filename))
                continue
            self._edit_objs[_filename] = ''

            _page = self._mwsite.pages[_title]
            if _page.exists and not rewrite:
                self._prompt_obj.prompt_print(_('page [$1] has been in wiki site!', _title))
                continue

            # 判断是否要上传附件(先上传的目的是避免页面打开看不到图片，需要手工保存一次才能看到)
            self._prompt_obj.prompt_print(_('edit page [$1]:  upload files', _title))
            _pic_path = os.path.join(input, FileTool.get_file_name_no_ext(_filename) + '_copy_pic')
            if _upload_files and os.path.exists(_pic_path) and os.path.isdir(_pic_path):
                # 满足上传附件的条件，模拟执行命令上传
                _cmd_para = "-input '%s' -desc '%s'" % (_pic_path, file_desc)
                if file_rewrite:
                    _cmd_para += ' -R'
                if file_ignore:
                    _cmd_para += ' -I'
                self._wiki_upload_cmd_dealfun(cmd_para=_cmd_para)

            # 处理页面编辑
            try:
                _text = FileTool.get_file_text(
                    os.path.join(input, _filename),
                    encoding=encoding
                )
                _result = _page.save(_text, _summary)
            except Exception as e:
                _prin_str = '%s %s (%s):\n%s' % (
                    _('edit page [$1] > [$2]', _filename, _title), _('fail'), str(e), traceback.format_exc()
                )
                self._prompt_obj.prompt_print(_prin_str)
                continue

            if 'result' in _result.keys() and _result['result'] == 'Success':
                self._prompt_obj.prompt_print('%s %s' % (_('edit page [$1] > [$2]', _filename, _title), _('done')))
                if 'warnings' in _result.keys():
                    self._prompt_obj.prompt_print('%s:\n%s\n' % (_('edit page [$1] with warnings', _filename), _result['warnings']))
            else:
                self._prompt_obj.prompt_print('%s %s:\n%s\n' % (
                    _('edit page [$1] > [$2]', _filename, _title), _('fail'),
                    str(_result)
                ))
                continue

    def _get_ns_page_count(self, ns, last_month, last_week):
        """
        获取命名空间的页面统计

        @param {int} ns - 命名空间编号
        @param {string} last_month - 上一个月(30天)的日期时间，格式为yyyy-mm-dd
        @param {string} last_week - 上一个星期(7天)的日期时间，格式为yyyy-mm-dd

        @return {dict} - 统计信息
            count : 总页面数
            last_month_add : 一个月(30天)内新增
            last_month_change : 一个月(30天)内修改
            last_week_add : 一个星期内新增
            last_week_change : 一个星期内修改
        """
        _dict = {
            'count': 0,
            'last_month_add': 0,
            'last_month_change': 0,
            'last_week_add': 0,
            'last_week_change': 0
        }

        _all_pages = self._mwsite.allpages(namespace=str(ns), filterredir='nonredirects', limit=5000)
        for _page in _all_pages:
            self._prompt_obj.prompt_print('.', end='', flush=True)
            _dict['count'] += 1
            _has_week_revi = False
            # 按周计算
            _revisions = _page.revisions(start='%sT00:00:01Z' % last_week, dir='newer', limit=2)
            for _revi in _revisions:
                if _revi['parentid'] == 0:
                    # 是新增
                    _dict['last_month_add'] += 1
                    _dict['last_week_add'] += 1
                else:
                    # 是修改
                    _dict['last_month_change'] += 1
                    _dict['last_week_change'] += 1
                # 标识按周已经有数据
                _has_week_revi = True
                # 只要判断第一条记录就可以了
                break

            if _has_week_revi:
                # 按周处理过，则无需再判断月
                continue

            # 按月计算
            _revisions = _page.revisions(start='%sT00:00:01Z' % last_month, dir='newer', limit=2)
            for _revi in _revisions:
                if _revi['parentid'] == 0:
                    # 是新增
                    _dict['last_month_add'] += 1
                else:
                    # 是修改
                    _dict['last_month_change'] += 1

                # 只要判断第一条记录就可以了
                break

        return _dict

    def _get_person_ranking_data(self, person_ranking_para, last_month, last_week):
        """
        <description>

        @param {<type>} person_ranking_para - <description>
        @param {<type>} last_month - <description>
        @param {<type>} last_week - <description>
        """
        _dict = dict()
        _ns_list = None
        if len(person_ranking_para['ns_list']) > 0:
            # 命名空间清单: 0-Main,2-用户,6-文件,8-MediaWiki,10-模板,12-帮助
            _ns_list = '|'.join(person_ranking_para['ns_list'])
        _dt_last_month = datetime.datetime.strptime(last_month, '%Y-%m-%d')
        _dt_last_week = datetime.datetime.strptime(last_week, '%Y-%m-%d')

        # 列出有编辑过的用户
        _all_user = self._mwsite.allusers(limit=5000, witheditsonly=True)
        _user_list = [[_user['name']] for _user in _all_user]
        with self._prompt_obj.get_process_bar() as pb:
            for _user_info in pb(_user_list, total=len(_user_list), label=_('deal with [$1]', _('user'))):
                _user = _user_info[0]
                if _user in person_ranking_para['black_list']:
                    # 黑名单用户，不处理
                    continue

                _dict[_user] = {
                    'total_add': 0,
                    'total_change': 0,
                    'total_ranking_scroe': 0,
                    'last_month_add': 0,
                    'last_month_change': 0,
                    'last_month_ranking_scroe': 0,
                    'last_week_add': 0,
                    'last_week_change': 0,
                    'last_week_ranking_scroe': 0
                }

                # 所有的新增贡献
                _contrib = self._mwsite.usercontributions(
                    [_user, ],
                    namespace=_ns_list,
                    limit=50000,
                    show="new",
                    prop='ids|timestamp'
                )
                for _page in _contrib:
                    _dict[_user]['total_add'] += 1
                    _dict[_user]['total_ranking_scroe'] += person_ranking_para['add_score']
                    _dt = datetime.datetime.fromtimestamp(time.mktime(_page['timestamp']))
                    if _dt > _dt_last_month:
                        _dict[_user]['last_month_add'] += 1
                        _dict[_user]['last_month_ranking_scroe'] += person_ranking_para['add_score']
                    if _dt > _dt_last_week:
                        _dict[_user]['last_week_add'] += 1
                        _dict[_user]['last_week_ranking_scroe'] += person_ranking_para['add_score']

                # 所有的修改贡献
                _contrib = self._mwsite.usercontributions(
                    [_user, ],
                    namespace=_ns_list,
                    limit=50000,
                    show="!new|!minor",
                    prop='ids|timestamp'
                )
                for _page in _contrib:
                    _dict[_user]['total_change'] += 1
                    _dict[_user]['total_ranking_scroe'] += person_ranking_para['change_score']
                    _dt = datetime.datetime.fromtimestamp(time.mktime(_page['timestamp']))
                    if _dt > _dt_last_month:
                        _dict[_user]['last_month_change'] += 1
                        _dict[_user]['last_month_ranking_scroe'] += person_ranking_para['change_score']
                    if _dt > _dt_last_week:
                        _dict[_user]['last_week_change'] += 1
                        _dict[_user]['last_week_ranking_scroe'] += person_ranking_para['change_score']

        # 返回结果数组
        return _dict

    def _append_to_filter_mt(self, path, text):
        """
        把信息添加到filter.mt文件中

        @param {string} path - 文件所在路径
        @param {string} text - 要追加的信息
        """
        with open(os.path.join(path, 'filter.mt'), 'a+', encoding='utf-8') as f:
            f.writelines('\n' + text)


if __name__ == '__main__':
    # 当程序自己独立运行时执行的操作
    # 打印版本信息
    print(('模块名：%s  -  %s\n'
           '作者：%s\n'
           '发布日期：%s\n'
           '版本：%s' % (__MOUDLE__, __DESCRIPT__, __AUTHOR__, __PUBLISH__, __VERSION__)))
