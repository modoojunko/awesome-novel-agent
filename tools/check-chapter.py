#!/usr/bin/env python3
"""章节交付确定性检查。只报警，不自动改文。

与 check-prose.py 分工：check-prose 管 AI 味统计形态（anti-ai Phase 2/4），
本工具管章节交付硬伤（引语夹层、嵌套引号、半角引号、字数对账、回归串）。
标点口径对齐 knowledge/anti-ai/common-rules.md：破折号/省略号不做硬禁，
段落内 ≥3 处时提示逐处按用法判定。

项目级资产外置（缺失即跳过，向上最多找 5 层目录）：
  sandbox/prose-regressions.txt  回归模式库（曾翻车的精确串，一行一条，命中即硬失败）
  sandbox/locked-lines.txt       锁定台词白名单（一行一条，命中行跳过裁定类检查）

用法: python3 check-chapter.py <稿件路径|目录> [更多路径...]   （目录扫描其下 *.md）
退出码: 0 = 无硬性命中（可有需人工裁定的警告）；1 = 存在硬性命中；2 = 用法错误或读取失败
"""

from __future__ import annotations

import re
import sys
from glob import glob
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

MAX_PARENTS = 5

# ---- 硬性检查（命中即失败）----
SANDWICH_TAG = re.compile(r"。”[^”\n]{0,14}，“")
NESTED_QUOTE = re.compile(r"“[^”]*“[^”]*”")
HALFWIDTH_QUOTE = re.compile(r"[\"']")

# 字数表达自动核对：数字在引号前 / 引号在数字前
NUM = r"[一二两三四五六七八九十俩仨]{1,3}"
COUNT_QUOTE_AFTER = re.compile(
    r"(?:这|那|就|才|整整|刚好|一共|第)?(" + NUM + r")个字[，。：：]?[“‘]([^”’‘\n]{1,30})[”’]"
)
QUOTE_COUNT_BEFORE = re.compile(
    r"[“‘]([^”’‘\n]{1,30})[”’](?:这|那)?(" + NUM + r")个字"
)
# 无引号可对的字数表达 → 提示人工逐字核对
COUNT_BARE = re.compile(r"(?:这|那|就|才|整整|刚好|一共)?" + NUM + r"个字")

CN_NUM = {"零": 0, "一": 1, "二": 2, "两": 2, "俩": 2, "三": 3, "仨": 3, "四": 4,
          "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}


def cn2int(s: str):
    if s in CN_NUM:
        return CN_NUM[s]
    if s == "十":
        return 10
    if len(s) == 2 and s[0] in CN_NUM and s[1] == "十":
        return CN_NUM[s[0]] * 10
    if len(s) == 2 and s[0] == "十" and s[1] in CN_NUM:
        return 10 + CN_NUM[s[1]]
    return None


def han_count(s: str) -> int:
    return len(re.findall(r"[\u4e00-\u9fff]", s))


# ---- 警告级检查（需人工裁定，不失败）----
# 破折号/省略号：对齐 common-rules 用法判定，段内 ≥3 处才提示（网文每段一行）
DASH_DENSE = re.compile(r"——|—|--|……")
SPEECH_VERB = r"(?:说|问|答|回|喊|叫|道|念)"
# 广义夹层：两段引语被含言说动词的短叙述隔开（需裁定归属）
SANDWICH_BROAD = re.compile(r"”[^”\n]{1,18}“")
SANDWICH_MID_VERB = re.compile(SPEECH_VERB + r"|接话|插|补|应|骂|叹|劝|拦")
# 多轮问答并段：同段 ≥3 处"代词+言说动词"
QA_DENSITY = re.compile(r"(?:我|他|她|他们|她们)" + SPEECH_VERB)
QA_DENSITY_LIMIT = 3
# 尾随标签窄集（代词+言说动词收尾；人物名表属书级资产，不入通用工具）
TRAILING_TAG = re.compile(r"”[^”\n]{0,12}(?:我|他|她|他们|她们)" + SPEECH_VERB + r"。")
# 弱化副词密度：千字占比超标提示（阈值 3/千字，与 anti-ai 规则口径一致）
WEAK_ADVERB = re.compile(r"缓缓|微微|轻轻|淡淡")
WEAK_ADVERB_PER_KILO = 3


def load_lines_file(start: Path, name: str) -> list[str]:
    """从 start 及其父目录向上找 sandbox/<name>，返回非空行列表。"""
    cur = start.resolve().parent
    for _ in range(MAX_PARENTS):
        f = cur / "sandbox" / name
        if f.exists():
            try:
                return [ln.strip() for ln in
                        f.read_text(encoding="utf-8-sig").splitlines() if ln.strip()]
            except OSError:
                return []
        if cur.parent == cur:
            break
        cur = cur.parent
    return []


def iter_prose_files(paths: list[str]) -> list[Path]:
    files: list[Path] = []
    for p in paths:
        path = Path(p)
        if path.is_dir():
            files.extend(Path(f) for f in sorted(glob(str(path / "*.md"))))
        else:
            files.append(path)
    return files


def check_file(path: Path, regressions: list[str], hard_hits: list[str]) -> None:
    print(f"== {path.name} ==")
    text = path.read_text(encoding="utf-8-sig")
    text = text.replace("\r\n", "\n")
    lines = text.split("\n")
    whitelist = set(load_lines_file(path, "locked-lines.txt"))

    warned_words = False
    for lineno, ln in enumerate(lines, 1):
        locked = ln.strip() in whitelist
        excerpt = ln[:60]

        def report(tag: str, hard: bool, ctx: str = excerpt) -> None:
            prefix = "" if hard else "(需裁定) "
            print(f"  [{tag}] {prefix}L{lineno}: {ctx}")

        # 白名单行：跳过裁定类检查，标注理由
        if locked:
            print(f"  [白名单跳过] L{lineno}: {ln.strip()[:40]}")
            continue

        # --- 硬性 ---
        if SANDWICH_TAG.search(ln):
            report("夹层-标签式", True)
            hard_hits.append(f"{path.name}:{lineno} 夹层-标签式")
        if NESTED_QUOTE.search(ln):
            report("嵌套双引号", True)
            hard_hits.append(f"{path.name}:{lineno} 嵌套双引号")
        if HALFWIDTH_QUOTE.search(ln):
            report("半角引号", True)
            hard_hits.append(f"{path.name}:{lineno} 半角引号")
        for m in COUNT_QUOTE_AFTER.finditer(ln):
            want, got = cn2int(m.group(1)), han_count(m.group(2))
            if want is not None and want != got:
                report(f"字数表达不符(应{want}实{got})", True)
                hard_hits.append(f"{path.name}:{lineno} 字数表达不符")
        for m in QUOTE_COUNT_BEFORE.finditer(ln):
            want, got = cn2int(m.group(2)), han_count(m.group(1))
            if want is not None and want != got:
                report(f"字数表达不符(应{want}实{got})", True)
                hard_hits.append(f"{path.name}:{lineno} 字数表达不符")
        for pat in regressions:
            if pat in ln:
                report(f"回归模式库({pat[:10]}…)", True)
                hard_hits.append(f"{path.name}:{lineno} 回归模式库")
                break

        # --- 警告（需裁定）---
        if len(DASH_DENSE.findall(ln)) >= 3:
            report("破折省略密集", False)
        if any(SANDWICH_MID_VERB.search(m.group(0))
               for m in SANDWICH_BROAD.finditer(ln)):
            report("夹层-广义式", False)
        if len(QA_DENSITY.findall(ln)) >= QA_DENSITY_LIMIT:
            report("多轮问答并段", False)
        if TRAILING_TAG.search(ln):
            report("尾随标签", False)
        if COUNT_BARE.search(ln) and not (COUNT_QUOTE_AFTER.search(ln)
                                          or QUOTE_COUNT_BEFORE.search(ln)):
            report("字数表达(需逐字核对)", False)

    # 弱化副词密度（文件级）
    n_adv = len(WEAK_ADVERB.findall(text))
    n_han = han_count(text)
    if n_han > 0 and n_adv > WEAK_ADVERB_PER_KILO * n_han / 1000:
        print(f"  [弱化副词超标] (需裁定) {n_adv} 处 / {n_han} 字")

    # 平台口径字数（只统计不设阈值，字数要求属书级设定）
    body = text.split("\n", 1)[1] if text.startswith("#") else text
    han = han_count(body)
    full = len(re.findall(r"[\u3000-\u303f\uff00-\uffef]", body))
    quotes = body.count("\u201c") + body.count("\u201d")
    digits = len(re.findall(r"[0-9]", body))
    print(f"  平台口径字数: {han + full + quotes + digits}"
          f"  汉字{han} 全角{full} 引号{quotes} 数字{digits}")


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    files = iter_prose_files(sys.argv[1:])
    if not files:
        print("未找到待检查文件")
        return 2
    regressions = load_lines_file(files[0], "prose-regressions.txt")

    hard_hits: list[str] = []
    for path in files:
        try:
            check_file(path, regressions, hard_hits)
        except OSError as e:
            print(f"  读取失败: {path}: {e}")
            return 2

    if hard_hits:
        print(f">>> 存在 {len(hard_hits)} 处硬性命中，交付前必须清零或逐条裁决 <<<")
        return 1
    print(">>> 无硬性命中（警告项需人工裁定）<<<")
    return 0


if __name__ == "__main__":
    sys.exit(main())
