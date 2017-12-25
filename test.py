#! /usr/bin/env python
# -*- coding: utf-8 -*-

#from ansible.module_utils.basic import *
import sys
import os.path
import re
import copy



def unescape_regexp_char(regexp_char):
    regexp_char = regexp_char.replace("\*", "*")
    regexp_char = regexp_char.replace("\?", "?")
    regexp_char = regexp_char.replace("\+", "+")
    regexp_char = regexp_char.replace("\-", "-")
    regexp_char = regexp_char.replace("\^", "^")
    regexp_char = regexp_char.replace("\$", "$")

    return regexp_char



def main():
    # ansibleのモジュールを使用してパラメータ取り込み
    # - filepath : 編集対象のファイルパス
    # - modifies : 編集する行と編集内容の定義
    #module = AnsibleModule(
    #    dict(
    #        filepath=dict(required=True),
    #        modifies=dict(required=True, type='list')
    #    )
    #)
    path = '/etc/hosts'
    prev = '127.0.0.1   localhost localhost.localdomain localhost4 localhost4.localdomain4'
    current = '127.0.0.1   localhost localhost.localdomain localhost4 localhost4.localdomain4\n::1         localhost6 localhost6.localdomain6'
    state = 'absent'
    #modifies = module.params['modifies']

    # ディストリビューションとバージョンを取得(※未使用のパラメータ)
    # - distribution : ディストリの種類
    # - version      : OS のバージョン
    #distribution = get_distribution()
    #version = get_distribution_version()

    # 指定されたファイルに関するチェック
    # - ファイルが存在しているか
    # - ディレクトリではないか
    # - シンボリックリンクではないか
    # どれかに該当すればエラー終了
    #if not os.path.exists(filepath):
        #module.fail_json(msg='[Error] file '+ filepath +' is not found.')
    #elif os.path.isdir(filepath):
        #module.fail_json(msg='[Error] '+ filepath +' is directory.')
    #elif os.path.islink(filepath):
        #module.fail_json(msg='[Error] '+ filepath +' is link.')

    # ファイルに問題が無ければリストとして変数に格納
    # - flines : ファイルの各行が要素となったリスト
    
    # changed : 変更を実施したかの判定
    changed = False
    
    line = open(path).read()
    
    if state == 'present':
        if not re.findall('\n$', current, re.MULTILINE):
            current += '\n'
    
        if re.findall(current, line, re.MULTILINE):
            print('not change')
            sys.exit()
    
        prev = re.findall(prev, line, re.MULTILINE)
        if not prev:
            print('prev is not found')
            sys.exit()
        
        elif len(prev) != 1:
            print('prev is not 1')
            sys.exit()
    
        prev = prev[0] + '\n'
        line = re.sub(prev, current, line)
    
    elif state == 'absent':
        if not re.findall('\n$', prev, re.MULTILINE):
            prev += '\n'
        
        if not re.findall('\n$', current, re.MULTILINE):
            current += '\n'
        
        if not re.findall(current, line, re.MULTILINE):
            if re.findall(prev, line, re.MULTILINE):
                print('not change')
                sys.exit()
            
        line = re.sub(current, prev, line)
    
    print(repr(line))
    print(line)
        
if __name__ == '__main__':
    main()