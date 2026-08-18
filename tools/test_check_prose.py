#!/usr/bin/env python3
"""check-prose.py 规则单测（活人感移植 Task D，issue #111）。

用法: python tools/test_check_prose.py
返回码 0 = 全部通过。
"""
import contextlib
import io
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_util import check, summary, exit_code, load_module

CHECK_PROSE = load_module(
    "check_prose_mod", Path(__file__).resolve().parent / "check-prose.py"
)

CLEAN_TEXT = "\n".join([
    "陈放把借条折了两次，塞回口袋。",
    "老板问他是不是嫌少。他说没有，手却一直按着口袋。",
    "门外有人催货。老板起身去接电话。",
    "他站了一会儿，又把借条掏出来放回桌上。",
    "“日期写错了。”",
    "老板看了一眼。日期没有错。",
])


def run_check(text: str):
    """写临时文件跑 main()，返回 (退出码, stdout)。"""
    with tempfile.NamedTemporaryFile(
        "w", suffix=".md", delete=False, encoding="utf-8"
    ) as f:
        f.write(text)
        path = f.name
    argv_backup = sys.argv[:]
    sys.argv = ["check-prose.py", path]
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            code = CHECK_PROSE.main()
    finally:
        sys.argv = argv_backup
        Path(path).unlink(missing_ok=True)
    return code, buf.getvalue()


def test_pivot_hard_fail():
    code, out = run_check("他不是生气，而是失望。他转身走了。")
    check("翻案句判失败（退出码 1）", code == 1, code)
    check("输出含禁用翻案句", "禁用翻案句" in out, out[:200])


def test_semantic_pivot_warning_only():
    code, out = run_check("你以为他赢了，其实他输了。第二天他照常上班。")
    check("翻案腔变形仅警告（退出码 0）", code == 0, code)
    check("输出含疑似翻案腔变形", "疑似翻案腔变形" in out, out[:200])


def test_dash_colon_not_hard_fail():
    code, _ = run_check("他顿了顿——没接话。他说：“走吧。”门关上了。")
    check("单处破折号/引语冒号不判失败（网文口径）", code == 0, code)


def test_dash_dense_warning():
    code, out = run_check("他进门——先看左边——又看右边——最后盯着柜子。")
    check(
        "同段三处破折号出警告不判失败",
        code == 0 and "破折号" in out and "需要人工判断" in out,
        (code, out[:200]),
    )


def test_road_sign_fail():
    code, out = run_check("值得注意的是，他没走。")
    check("模型路标判失败", code == 1 and "模型路标" in out, (code, out[:200]))


def test_uniform_sentence_cv_warning():
    code, out = run_check("他数了一遍又数一遍。\n" * 13)
    check("句长过于接近出警告", "长度过于接近" in out, out[:200])


def test_clean_text_pass():
    code, _ = run_check(CLEAN_TEXT)
    check("干净文本退出码 0", code == 0, code)


def test_read_error():
    argv_backup = sys.argv[:]
    sys.argv = ["check-prose.py", "/nonexistent/__no_such_file__.md"]
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            code = CHECK_PROSE.main()
    finally:
        sys.argv = argv_backup
    check("读取失败退出码 2", code == 2, code)


if __name__ == "__main__":
    test_pivot_hard_fail()
    test_semantic_pivot_warning_only()
    test_dash_colon_not_hard_fail()
    test_dash_dense_warning()
    test_road_sign_fail()
    test_uniform_sentence_cv_warning()
    test_clean_text_pass()
    test_read_error()
    print(f"\n{summary()}")
    sys.exit(exit_code())
