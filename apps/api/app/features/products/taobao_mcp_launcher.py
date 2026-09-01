"""以 stdout-safe 方式启动外部淘宝 MCP server.py。

MCP stdio 使用 stdout 传输 JSON-RPC。部分第三方服务的缓存日志使用内置
``print`` 写 stdout，会污染协议；这里只把这些日志重定向到 stderr，协议流仍
由外部 MCP SDK 写入 stdout。
"""

from __future__ import annotations

import builtins
import runpy
import sys
from pathlib import Path
from typing import Any


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: taobao_mcp_launcher.py /path/to/server.py")
    server_path = Path(sys.argv[1]).expanduser().resolve()
    if not server_path.is_file():
        raise SystemExit(f"Taobao MCP server.py not found: {server_path}")
    sys.path.insert(0, str(server_path.parent))
    original_print = builtins.print

    def stderr_print(*args: object, **kwargs: Any) -> None:
        kwargs.setdefault("file", sys.stderr)
        original_print(*args, **kwargs)

    builtins.print = stderr_print
    runpy.run_path(str(server_path), run_name="__main__")


if __name__ == "__main__":
    main()
