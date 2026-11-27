"""
predict.py 的单元测试。在本文件夹中运行：

    python -m unittest -v

测试会自动生成临时图片文件，不需要真实数据。
"""

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from PIL import Image

import config
import predict


class LoadImageTests(unittest.TestCase):
    """load_image()：正常图片能读取，其他文件都要给出明确的错误。"""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.folder = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def make_image(self, name, mode="RGB"):
        path = self.folder / name
        Image.new(mode, (70, 46)).save(path)
        return path

    def test_png_is_loaded_as_rgb(self):
        image = predict.load_image(self.make_image("slide.png"))
        self.assertEqual(image.mode, "RGB")
        self.assertEqual(image.size, (70, 46))

    def test_transparent_png_becomes_rgb(self):
        image = predict.load_image(self.make_image("slide.png", mode="RGBA"))
        self.assertEqual(image.mode, "RGB")

    def test_greyscale_jpg_becomes_rgb(self):
        image = predict.load_image(self.make_image("slide.jpg", mode="L"))
        self.assertEqual(image.mode, "RGB")

    def test_upper_case_extension_is_accepted(self):
        image = predict.load_image(self.make_image("SLIDE.PNG"))
        self.assertEqual(image.mode, "RGB")

    def test_missing_file_is_refused(self):
        with self.assertRaises(predict.ImageLoadError):
            predict.load_image(self.folder / "does_not_exist.png")

    def test_folder_is_refused(self):
        with self.assertRaises(predict.ImageLoadError):
            predict.load_image(self.folder)

    def test_text_file_is_refused(self):
        path = self.folder / "notes.txt"
        path.write_text("not an image")
        with self.assertRaises(predict.ImageLoadError):
            predict.load_image(path)

    def test_damaged_png_is_refused(self):
        path = self.folder / "broken.png"
        path.write_bytes(b"\x89PNG\r\n\x1a\n" + b"this is not real image data")
        with self.assertRaises(predict.ImageLoadError):
            predict.load_image(path)

    def test_empty_file_is_refused(self):
        path = self.folder / "empty.png"
        path.write_bytes(b"")
        with self.assertRaises(predict.ImageLoadError):
            predict.load_image(path)


class PlaceholderPredictionTests(unittest.TestCase):
    """占位模型的输入输出格式要和真实模型保持一致。"""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "slide.png"
        Image.new("RGB", (70, 46), (200, 120, 180)).save(self.path)

    def tearDown(self):
        self.temp.cleanup()

    def test_returns_a_known_class_and_a_probability(self):
        label, probability = predict.predict(predict.PLACEHOLDER_MODEL, self.path)
        self.assertIn(label, config.CLASSES)
        self.assertGreaterEqual(probability, 0.5)  # 两个类别中概率较高的那个
        self.assertLessEqual(probability, 1.0)

    def test_same_image_gives_same_result(self):
        first = predict.predict(predict.PLACEHOLDER_MODEL, self.path)
        second = predict.predict(predict.PLACEHOLDER_MODEL, self.path)
        self.assertEqual(first, second)

    def test_missing_image_raises_image_error(self):
        with self.assertRaises(predict.ImageLoadError):
            predict.predict(predict.PLACEHOLDER_MODEL, Path(self.temp.name) / "missing.png")


class ModelLoadingTests(unittest.TestCase):
    """load_model()：演示模式返回占位模型；找不到模型文件时给出明确的错误。"""

    def test_demo_mode_gives_the_placeholder(self):
        with mock.patch.object(config, "USE_PLACEHOLDER_MODEL", True):
            self.assertIs(predict.load_model(), predict.PLACEHOLDER_MODEL)

    def test_missing_model_file_gives_a_clear_error(self):
        with mock.patch.object(config, "USE_PLACEHOLDER_MODEL", False), \
             mock.patch.object(config, "MODEL_PATH", Path("no_such_folder") / "model.pth"):
            with self.assertRaises(predict.ModelLoadError):
                predict.load_model()


class ProbabilityTests(unittest.TestCase):
    """probabilities_for_all_classes()：两个类别的概率之和为 1。"""

    def test_two_class_probabilities_add_up_to_one(self):
        probabilities = predict.probabilities_for_all_classes("malignant", 0.87)
        self.assertAlmostEqual(probabilities["malignant"], 0.87)
        self.assertAlmostEqual(probabilities["benign"], 0.13)
        self.assertAlmostEqual(sum(probabilities.values()), 1.0)


if __name__ == "__main__":
    unittest.main()
