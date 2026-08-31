#!/usr/bin/env python3
"""check-chapter.py 规则单测（openspec change: add-zhuque-source-defense）。

用法: python tools/test_check_chapter.py
返回码 0 = 全部通过。
"""
import contextlib
import io
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_util import check, summary, exit_code

TOOL = Path(__file__).resolve().parent / "check-chapter.py"

CLEAN_TEXT = "\n".join([
    "# 第一章 试探",
    "陈放把借条折了两次，塞回口袋。",
    "老板问他是不是嫌少。他说没有，手却一直按着口袋。",
    "“日期写错了。”",
    "老板看了一眼。日期没有错。他把借条推回去，没接话。",
])

# 触发警告级检查的最小章节骨架（够放副词/碎句计数）
CLEAN_LONG_TEXT = "\n".join([CLEAN_TEXT] + [
    "他把杯里的凉茶喝完，起身去柜台结账。窗外的巷子已经亮起灯，收废品的三轮车慢慢骑过去。",
]) * 8


def run_tool(args, cwd=None):
    """命令行跑工具，返回 (退出码, stdout)。"""
    import subprocess
    proc = subprocess.run(
        [sys.executable, str(TOOL)] + args,
        capture_output=True, text=True, cwd=cwd,
    )
    return proc.returncode, proc.stdout + proc.stderr


def write_chapter(text: str, dir_name: str = "正文", name: str = "vol-1-ch-1.md"):
    """建临时项目：<tmp>/<dir_name>/<name>，返回 (tmp, 章节路径)。"""
    tmp = Path(tempfile.mkdtemp())
    chdir = tmp / dir_name
    chdir.mkdir(parents=True)
    path = chdir / name
    path.write_text(text, encoding="utf-8")
    return tmp, path


def test_clean_pass():
    tmp, path = write_chapter(CLEAN_LONG_TEXT)
    code, out = run_tool([str(path)])
    check("干净文本退出码 0", code == 0, out)
    check("干净文本输出平台口径字数", "平台口径字数" in out, out)
    check("干净文本无硬性命中", "处硬性命中" not in out, out)
    sys.stdout.write("ok test_clean_pass\n")


def test_sandwich_tag_hard():
    tmp, path = write_chapter(CLEAN_TEXT + "\n“对数据。就这吧。”他说，“下不为例。”")
    code, out = run_tool([str(path)])
    check("夹层-标签式硬失败", code == 1, out)
    check("夹层-标签式有标记", "夹层-标签式" in out, out)
    sys.stdout.write("ok test_sandwich_tag_hard\n")


def test_nested_quotes_hard():
    tmp, path = write_chapter(CLEAN_TEXT + "\n群里都在刷“重启“重启”的话题，没人说话。")
    code, out = run_tool([str(path)])
    check("嵌套双引号硬失败", code == 1, out)
    check("嵌套双引号有标记", "嵌套双引号" in out, out)
    sys.stdout.write("ok test_nested_quotes_hard\n")


def test_halfwidth_quotes_hard():
    tmp, path = write_chapter(CLEAN_TEXT + '\n他说"就这吧"，说完就走。')
    code, out = run_tool([str(path)])
    check("半角引号硬失败", code == 1, out)
    check("半角引号有标记", "半角引号" in out, out)
    sys.stdout.write("ok test_halfwidth_quotes_hard\n")


def test_dash_ellipsis_warning_only():
    text = CLEAN_TEXT + "\n他——一个干了二十年的老师傅——拿起锤子——又放下。"
    tmp, path = write_chapter(text)
    code, out = run_tool([str(path)])
    check("破折号只警告不硬失败", code == 0, out)
    check("破折号有需裁定标记", "需裁定" in out and "破折" in out, out)
    sys.stdout.write("ok test_dash_ellipsis_warning_only\n")


def test_wordcount_mismatch_hard():
    # "这四个字" 但引号内有 5 个汉字 → 硬失败
    tmp, path = write_chapter(CLEAN_TEXT + "\n“我不干了啊”这四个字，他说得很轻。")
    code, out = run_tool([str(path)])
    check("字数表达不符硬失败", code == 1, out)
    check("字数表达有标记", "字数表达不符" in out, out)
    sys.stdout.write("ok test_wordcount_mismatch_hard\n")


def test_wordcount_manual_warning():
    # 无引号可对的"X个字" → 仅警告
    tmp, path = write_chapter(CLEAN_TEXT + "\n回信就三个字，看得他手心冒汗。")
    code, out = run_tool([str(path)])
    check("字数待人工只警告", code == 0, out)
    check("字数待人工有标记", "字数表达" in out, out)
    sys.stdout.write("ok test_wordcount_manual_warning\n")


def test_qa_density_warning():
    line = "他问她吃了没。她说吃了。他又问去了哪里。她说你别管。他还想问，她把电话挂了。"
    tmp, path = write_chapter(CLEAN_TEXT + "\n" + line)
    code, out = run_tool([str(path)])
    check("多轮问答并段只警告", code == 0, out)
    check("多轮问答并段有标记", "多轮问答" in out, out)
    sys.stdout.write("ok test_qa_density_warning\n")


def test_adverb_density_warning():
    line = "他缓缓起身。她微微点头。他轻轻把门带上。她淡淡应了一声。"
    tmp, path = write_chapter(CLEAN_TEXT + "\n" + line)
    code, out = run_tool([str(path)])
    check("弱化副词密度只警告", code == 0, out)
    check("弱化副词有标记", "弱化副词" in out, out)
    sys.stdout.write("ok test_adverb_density_warning\n")


def test_trailing_tag_warning():
    tmp, path = write_chapter(CLEAN_TEXT + "\n“先这样吧。”我说。")
    code, out = run_tool([str(path)])
    check("尾随标签只警告", code == 0, out)
    check("尾随标签有标记", "尾随标签" in out, out)
    sys.stdout.write("ok test_trailing_tag_warning\n")


def test_regression_hit_hard():
    tmp, path = write_chapter(CLEAN_TEXT + "\n他把手机反扣在桌面上，盯着那行字。")
    sandbox = tmp / "sandbox"
    sandbox.mkdir()
    (sandbox / "prose-regressions.txt").write_text(
        "把手机反扣在桌面上，盯着那行字\n", encoding="utf-8"
    )
    code, out = run_tool([str(path)])
    check("回归串命中硬失败", code == 1, out)
    check("回归串有标记", "回归模式库" in out, out)
    sys.stdout.write("ok test_regression_hit_hard\n")


def test_regression_missing_ok():
    # 无 sandbox 文件 → 正常按其余检查跑
    tmp, path = write_chapter(CLEAN_LONG_TEXT)
    code, out = run_tool([str(path)])
    check("无回归库正常通过", code == 0, out)
    sys.stdout.write("ok test_regression_missing_ok\n")


def test_whitelist_skip():
    line = "“先这样吧。”我说。"
    tmp, path = write_chapter(CLEAN_TEXT + "\n" + line)
    sandbox = tmp / "sandbox"
    sandbox.mkdir()
    (sandbox / "locked-lines.txt").write_text(line + "\n", encoding="utf-8")
    code, out = run_tool([str(path)])
    check("白名单行跳过后通过", code == 0, out)
    check("白名单有标注", "白名单" in out, out)
    sys.stdout.write("ok test_whitelist_skip\n")


def test_crlf_input():
    tmp, path = write_chapter(CLEAN_LONG_TEXT.replace("\n", "\r\n"))
    code, out = run_tool([str(path)])
    check("CRLF 输入正常通过", code == 0, out)
    sys.stdout.write("ok test_crlf_input\n")


def test_missing_file_exit2():
    code, out = run_tool(["/nonexistent/no-such-file.md"])
    check("文件缺失退出码 2", code == 2, out)
    sys.stdout.write("ok test_missing_file_exit2\n")


def test_dir_input():
    tmp, path = write_chapter(CLEAN_TEXT + "\n“对数据。”他说，“下不为例。”")
    code, out = run_tool([str(tmp / "正文")])
    check("目录输入扫描 md 并硬失败", code == 1, out)
    sys.stdout.write("ok test_dir_input\n")


def main() -> int:
    if not TOOL.exists():
        print(f"FAIL: {TOOL.name} 不存在（先实现工具再跑测试）")
        return 1
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        fn()
    summary()
    return exit_code()


if __name__ == "__main__":
    sys.exit(main())
