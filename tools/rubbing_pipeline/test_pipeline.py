# -*- coding: utf-8 -*-
"""B 管线离线自测入口（不依赖网络）。"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from pipeline import self_test  # noqa: E402

if __name__ == "__main__":
    ok = self_test()
    sys.exit(0 if ok else 1)
