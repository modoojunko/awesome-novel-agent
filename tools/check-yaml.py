#!/usr/bin/env python3
"""pyyaml 门槛检查（安装阶段 fail-fast 用）。

opencode / codex 平台的 agent 转换依赖 pyyaml；install.sh / install.ps1
在任何目录创建/删除前调用本脚本，缺失时立即中止，而不是等 init.py /
sync-project.py 执行时才报错。claude 平台纯复制不转换，无需本检查。

用法:
  python tools/check-yaml.py                # 仅检查当前解释器能否 import yaml
  python tools/check-yaml.py codex          # 附带平台名，报错信息更具体

返回码:
  0 = 已安装
  1 = 缺失（输出 pip install 提示）
  2 = 参数错误
"""

import sys


def main(argv) -> int:
    platform = None
    if len(argv) > 2:
        print("错误: 最多接受一个平台参数。", file=sys.stderr)
        return 2
    if len(argv) == 2:
        platform = argv[1]

    try:
        import yaml  # noqa: F401
    except ImportError:
        label = platform or "当前"
        print(
            f"错误: {label} 平台需要 pyyaml（pip install pyyaml），"
            f"当前解释器 {sys.executable} 未安装。",
            file=sys.stderr,
        )
        return 1

    print(f"pyyaml 已安装（解释器 {sys.executable}）。")
    return 0


if __name__ == "__main__":
    for s in (sys.stdin, sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8")
        except AttributeError:
            pass
    sys.exit(main(sys.argv))
