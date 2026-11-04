"""档案快照冷备 —— 道统算子谱（jinkui）
道统出处：金匮藏书，石渠兰台
工程映射：关键状态快照归档，只增不覆盖
生长纪律：本地生长自由，推送远端需治理决议发令。
# 生长记录 2026-11-02：内核 M1 落地，用例 5 条全绿
"""

import hashlib
import json
import time
from pathlib import Path


class Archive:
    """金匮：版本化快照 + jsonl 索引，同名再存不覆盖旧卷。"""

    def __init__(self, base_dir: str = "/tmp/jinkui-vault"):
        self.base = Path(base_dir)
        self.base.mkdir(parents=True, exist_ok=True)
        self.index_path = self.base / "index.jsonl"

    def _append_index(self, entry: dict):
        with open(self.index_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")

    def snapshot(self, name: str, data: bytes) -> dict:
        """存一卷快照：同名第二次起生成 name.v2/v3 …，绝不覆盖旧卷。"""
        if isinstance(data, str):
            data = data.encode("utf-8")
        version = 1
        target = self.base / f"{name}.bin"
        while target.exists():
            version += 1
            target = self.base / f"{name}.v{version}.bin"
        target.write_bytes(data)
        digest = hashlib.sha256(data).hexdigest()
        entry = {
            "name": name, "file": target.name, "version": version,
            "sha256": digest, "size": len(data),
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }
        self._append_index(entry)
        return entry

    def verify(self, name: str) -> bool:
        """按索引最新一卷重算哈希核对；文件被篡改返回 False。"""
        entries = [e for e in self._load_index() if e.get("name") == name]
        if not entries:
            return False
        latest = entries[-1]
        f = self.base / latest["file"]
        if not f.exists():
            return False
        return hashlib.sha256(f.read_bytes()).hexdigest() == latest["sha256"]

    def _load_index(self) -> list:
        if not self.index_path.exists():
            return []
        out = []
        with open(self.index_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    out.append(json.loads(line))
        return out

    def describe(self) -> dict:
        return {"name": "jinkui", "role": "关键状态快照归档，只增不覆盖", "stage": "m1"}
