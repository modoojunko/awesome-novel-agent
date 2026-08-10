#!/usr/bin/env python3
"""Python 版本门槛检查（安装阶段 fail-fast 用）。

install.sh / install.ps1 在任何目录创建/删除前调用本脚本，解释器版本不满足
要求时立即报错退出——版本问题在安装阶段暴露，而不是等 init.py /
sync-project.py 执行时才以 TypeError / SyntaxError 的形式出现。

用法:
  python tools/check-python.py             # 检查当前解释器 >= 3.9
  python tools/check-python.py --min 3.10  # 自定义最低版本（测试用）

返回码:
  0 = 满足要求
  1 = 版本过低
  2 = 参数错误
"""

import sys

# 项目实际最低版本（tools/*.py 均已验证 3.9 兼容；
# 新代码若用到更高版本语法，应同步提高这里并在安装阶段暴露）。
MIN_VERSION = (3, 9)


def _label(version: tuple) -> str:
    return ".".join(str(x) for x in version)


def main(argv) -> int:
    min_version = MIN_VERSION
    if "--min" in argv:
        idx = argv.index("--min")
        if idx + 1 >= len(argv):
            print("错误: --min 需要一个版本号（如 3.10）", file=sys.stderr)
            return 2
        raw = argv[idx + 1]
        try:
            parts = tuple(int(x) for x in raw.split(".")[:2])
            if len(parts) != 2:
                raise ValueError
            min_version = parts
        except ValueError:
            print(f"错误: --min 需要形如 3.10 的版本号，收到: {raw}", file=sys.stderr)
            return 2

    current = sys.version_info[:2]
    if current < min_version:
        print(
            f"错误: 需要 Python {_label(min_version)} 或更高版本，当前是 {sys.version.split()[0]}。",
            file=sys.stderr,
        )
        print(
            "请升级 Python 后重试：https://www.python.org/downloads/"
            "（macOS 也可运行 `brew install python@3.12`）",
            file=sys.stderr,
        )
        return 1

    print(f"Python {sys.version.split()[0]} 满足要求（>= {_label(min_version)}）。")
    return 0


if __name__ == "__main__":
    for s in (sys.stdin, sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8")
        except AttributeError:
            pass
    sys.exit(main(sys.argv[1:]))
