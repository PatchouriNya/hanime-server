"""集号识别相关单元测试

覆盖 DownloadManager 的：
- _cn_to_arabic：中文数字转阿拉伯数字
- _extract_real_episode_number：从标题/副标题提取真实集号
"""
import sys
import unittest
from pathlib import Path

# 将 backend 目录加入模块搜索路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.download_service import DownloadManager  # noqa: E402


class TestCnToArabic(unittest.TestCase):
    """中文数字转换测试"""

    def setUp(self):
        self.dm = DownloadManager()

    def test_single_digits(self):
        self.assertEqual(self.dm._cn_to_arabic("一"), 1)
        self.assertEqual(self.dm._cn_to_arabic("五"), 5)
        self.assertEqual(self.dm._cn_to_arabic("九"), 9)

    def test_tens(self):
        self.assertEqual(self.dm._cn_to_arabic("十"), 10)
        self.assertEqual(self.dm._cn_to_arabic("十一"), 11)
        self.assertEqual(self.dm._cn_to_arabic("十五"), 15)
        self.assertEqual(self.dm._cn_to_arabic("二十"), 20)
        self.assertEqual(self.dm._cn_to_arabic("三十四"), 34)
        self.assertEqual(self.dm._cn_to_arabic("九十九"), 99)

    def test_invalid(self):
        self.assertEqual(self.dm._cn_to_arabic("abc"), 0)
        self.assertEqual(self.dm._cn_to_arabic(""), 0)


class TestExtractRealEpisodeNumber(unittest.TestCase):
    """从标题提取真实集号测试"""

    def setUp(self):
        self.dm = DownloadManager()

    def test_chinese_episode_suffix(self):
        # 第N話/话/期/章/部
        self.assertEqual(self.dm._extract_real_episode_number("某番剧 第十一話", ""), 11)
        self.assertEqual(self.dm._extract_real_episode_number("某番剧 第4話", ""), 4)
        self.assertEqual(self.dm._extract_real_episode_number("某番剧 第2期", ""), 2)

    def test_episode_prefix(self):
        self.assertEqual(self.dm._extract_real_episode_number("某番剧 Episode 5", ""), 5)
        self.assertEqual(self.dm._extract_real_episode_number("某番剧 Ep. 3", ""), 3)

    def test_hash_number(self):
        self.assertEqual(self.dm._extract_real_episode_number("某番剧 ＃2", ""), 2)
        self.assertEqual(self.dm._extract_real_episode_number("某番剧 #7", ""), 7)

    def test_volume_labels(self):
        # 上卷/前編=1, 中卷=2, 下卷/後編=3
        self.assertEqual(self.dm._extract_real_episode_number("某番剧 上巻", ""), 1)
        self.assertEqual(self.dm._extract_real_episode_number("某番剧 前編", ""), 1)
        self.assertEqual(self.dm._extract_real_episode_number("某番剧 中巻", ""), 2)
        self.assertEqual(self.dm._extract_real_episode_number("某番剧 下巻", ""), 3)
        self.assertEqual(self.dm._extract_real_episode_number("某番剧 後編", ""), 3)

    def test_trailing_number_excludes_year(self):
        self.assertEqual(self.dm._extract_real_episode_number("某番剧 2026", ""), 0)
        self.assertEqual(self.dm._extract_real_episode_number("某番剧 12", ""), 12)


if __name__ == "__main__":
    unittest.main()
