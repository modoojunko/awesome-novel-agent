#!/usr/bin/env python3
"""测试共享工具：check 断言 + PASS/FAIL 汇总 + 模块加载。

test_style_rules.py / test_style_distill.py / test_platforms.py 三个测试文件共用，
避免各自复制一份 check()（以前三处签名/行为漂移风险）。

用法:
  from test_util import check, summary, exit_code
  check("描述", cond, detail_if_fail)
  ...
  print(f"\n{summary()}"); sys.exit(exit_code())
"""
import importlib.util
import sys
from pathlib import Path

PASS = 0
FAIL = 0


def check(name: str, cond: bool, detail: str = ""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ok  {name}")
    else:
        FAIL += 1
        print(f"  FAIL {name}  {detail}")


def summary() -> str:
    return f"{PASS} passed, {FAIL} failed"


def exit_code() -> int:
    return 1 if FAIL else 0


def load_module(name: str, path) -> object:
    """按文件路径加载模块（文件名含连字符无法直接 import，如 check-agents.py）。
    各测试文件共用的 importlib 样板（review #41：此前 ×5 复制）。
    先注册进 sys.modules 再 exec——模块内使用 @dataclass 时需要可解析的 __module__。"""
    spec = importlib.util.spec_from_file_location(name, str(Path(path)))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod
