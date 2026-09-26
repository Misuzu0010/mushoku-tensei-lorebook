#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EPUB 批量转 Markdown 入口包装脚本
实际核心逻辑位于 tools/convert_all.py
"""
import sys
import os

# 将项目根目录与 tools 目录加入 sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "tools"))

from convert_all import main

if __name__ == "__main__":
    main()
