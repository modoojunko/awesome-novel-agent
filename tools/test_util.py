#!/usr/bin/env python3
"""测试共享工具：check 断言 + PASS/FAIL 汇总。

test_style_rules.py / test_style_distill.py / test_platforms.py 三个测试文件共用，
避免各自复制一份 check()（以前三处签名/行为漂移风险）。

用法:
  from test_util import check, summary, exit_code
  check("描述", cond, detail_if_fail)
  ...
  print(f"\n{summary()}"); sys.exit(exit_code())
"""
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
