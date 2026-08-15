"""下载工具函数与系列名提取单元测试

覆盖：
- DownloadManager._sanitize_filename：文件名清洗
- downloads.py 的 _extract_series_name：从标题提取系列名
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.download_service import DownloadManager  # noqa: E402
from app.api.endpoints.downloads import _extract_series_name  # noqa: E402


class TestSanitizeFilename(unittest.TestCase):
    """文件名清洗测试"""

    def setUp(self):
        self.dm = DownloadManager()

    def test_illegal_chars(self):
        self.assertEqual(self.dm._sanitize_filename('a<b>:c'), 'a_b__c')
        self.assertEqual(self.dm._sanitize_filename('a/b\\c'), 'a_b_c')

    def test_length_limit(self):
        long_name = 'x' * 300 + '.mp4'
        cleaned = self.dm._sanitize_filename(long_name)
        self.assertLessEqual(len(cleaned), 200)


class TestExtractSeriesName(unittest.TestCase):
    """系列名提取测试"""

    def test_color_suffix(self):
        self.assertEqual(_extract_series_name("不潔之星・赤"), "不潔之星")
        self.assertEqual(_extract_series_name("不洁之星 2"), "不洁之星")

    def test_season_suffix(self):
        self.assertEqual(_extract_series_name("某番剧 第2期"), "某番剧")
        self.assertEqual(_extract_series_name("某番剧 Season 2"), "某番剧")

    def test_no_suffix(self):
        self.assertEqual(_extract_series_name("普通番剧"), "普通番剧")
        self.assertEqual(_extract_series_name(""), "")


if __name__ == "__main__":
    unittest.main()
