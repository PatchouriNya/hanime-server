"""视频解析与评分相关单元测试

覆盖 VideoService 的：
- _parse_views：观看次数文本解析（万/千）
- calculate_rating：综合评分算法
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.video_service import VideoService  # noqa: E402


class TestParseViews(unittest.TestCase):
    """观看次数解析测试"""

    def setUp(self):
        self.vs = VideoService()

    def test_empty(self):
        self.assertEqual(self.vs._parse_views(""), 0)
        self.assertEqual(self.vs._parse_views(None), 0)

    def test_wan(self):
        self.assertEqual(self.vs._parse_views("1.2萬"), 12000)
        self.assertEqual(self.vs._parse_views("3.5万"), 35000)
        self.assertEqual(self.vs._parse_views("10萬"), 100000)

    def test_qian(self):
        self.assertEqual(self.vs._parse_views("5千"), 5000)
        self.assertEqual(self.vs._parse_views("1.5千"), 1500)

    def test_plain(self):
        self.assertEqual(self.vs._parse_views("123"), 123)
        self.assertEqual(self.vs._parse_views("1,234"), 1234)


class TestCalculateRating(unittest.TestCase):
    """综合评分算法测试（10分制）"""

    def setUp(self):
        self.vs = VideoService()

    def test_high_volume_high_rating(self):
        # 100%好评 + 10万赞 + 1000评论 + 5000万播放 → ~9.8
        rating = self.vs.calculate_rating(100.0, 100000, 50000000, 1000)
        self.assertGreaterEqual(rating, 9.0)
        self.assertLessEqual(rating, 9.9)

    def test_low_volume_regression(self):
        # 100%好评 + 10赞 + 500播放 → 向均值回归（< 高分视频）
        low = self.vs.calculate_rating(100.0, 10, 500, 0)
        high = self.vs.calculate_rating(100.0, 100000, 50000000, 1000)
        self.assertLess(low, high)

    def test_bounds(self):
        rating = self.vs.calculate_rating(50.0, 1, 1, 0)
        self.assertGreaterEqual(rating, 1.0)
        self.assertLessEqual(rating, 9.9)

    def test_zero_data(self):
        rating = self.vs.calculate_rating(100.0, 0, 0, 0)
        self.assertGreaterEqual(rating, 1.0)
        self.assertLessEqual(rating, 9.9)


if __name__ == "__main__":
    unittest.main()
