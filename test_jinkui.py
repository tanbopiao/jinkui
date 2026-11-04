import unittest
import tempfile
import hashlib
from pathlib import Path
from jinkui import Archive

class T(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="jinkui-test-")
        self.a = Archive(base_dir=self.tmp)

    def test_first_snapshot_is_v1_with_correct_hash(self):
        data = "石牛山资产包 V1.0".encode("utf-8")
        entry = self.a.snapshot("shiniushan", data)
        self.assertEqual(entry["version"], 1)
        self.assertEqual(entry["sha256"], hashlib.sha256(data).hexdigest())

    def test_same_name_creates_v2_not_overwrite(self):
        self.a.snapshot("shiniushan", "第一卷".encode("utf-8"))
        entry2 = self.a.snapshot("shiniushan", "第二卷".encode("utf-8"))
        self.assertEqual(entry2["version"], 2)
        self.assertTrue((Path(self.tmp) / "shiniushan.bin").exists())      # v1 仍在
        self.assertTrue((Path(self.tmp) / "shiniushan.v2.bin").exists())   # v2 并存

    def test_index_append_two_entries(self):
        self.a.snapshot("shiniushan", "一".encode("utf-8"))
        self.a.snapshot("shiniushan", "二".encode("utf-8"))
        self.a.snapshot("xuangui-m1", "三".encode("utf-8"))
        index = self.a._load_index()
        self.assertEqual(len(index), 3)
        self.assertEqual([e["name"] for e in index], ["shiniushan", "shiniushan", "xuangui-m1"])

    def test_verify_detects_tampering(self):
        self.a.snapshot("账本", "真账".encode("utf-8"))
        f = Path(self.tmp) / "账本.bin"
        f.write_bytes("假账".encode("utf-8"))            # 篡改
        self.assertFalse(self.a.verify("账本"))

    def test_verify_passes_untouched(self):
        self.a.snapshot("账本", "真账".encode("utf-8"))
        self.assertTrue(self.a.verify("账本"))

if __name__ == "__main__":
    unittest.main()
