"""
predict.py：连接模型和界面的预测模块。

界面（gui.py）只用到下面三个函数：

    load_image(path)       -> RGB 格式的 PIL 图片；文件不能用时抛出 ImageLoadError
    load_model()           -> 模型对象；加载失败时抛出 ModelLoadError
    predict(model, path)   -> (类别, 概率)，例如 ("malignant", 0.87)

config.USE_PLACEHOLDER_MODEL 为 True 时使用占位模型，返回固定但没有意义的结果，
用于在真实模型完成之前开发和测试界面。接入真实模型时，只需补全本文件末尾的
两个函数，并把该设置改为 False，gui.py 不需要修改。
"""

import hashlib
from pathlib import Path

from PIL import Image, UnidentifiedImageError

import config


class ImageLoadError(Exception):
    """所选文件不能作为输入图片使用。错误信息会直接显示给用户。"""


class ModelLoadError(Exception):
    """模型无法加载。错误信息会直接显示给用户。"""


# ---------------------------------------------------------------- 读取图片

def load_image(path):
    """打开图片文件，返回 RGB 格式的 PIL 图片。

    文件不存在、格式不支持或无法解码时，抛出带说明的 ImageLoadError。
    """
    path = Path(path)
    if not path.exists():
        raise ImageLoadError(f"The file could not be found:\n{path}")
    if not path.is_file():
        raise ImageLoadError(f"'{path.name}' is a folder. Please choose an image file.")
    if path.suffix.lower() not in config.SUPPORTED_EXTENSIONS:
        allowed = ", ".join(config.SUPPORTED_EXTENSIONS)
        raise ImageLoadError(
            f"'{path.name}' is not a supported image type.\n"
            f"Please choose one of these: {allowed}"
        )
    try:
        with Image.open(path) as image:
            image.load()                 # 立即读取全部像素，损坏的文件会在这里报错
            return image.convert("RGB")  # 统一为 3 个颜色通道（透明 PNG、灰度图等都会被转换）
    except Image.DecompressionBombError as error:
        raise ImageLoadError(f"'{path.name}' is too large to open safely.") from error
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError) as error:
        raise ImageLoadError(
            f"'{path.name}' could not be read as an image. The file may be damaged."
        ) from error


# ---------------------------------------------------------------- 模型

# 使用占位模型时，用这个对象代替真实模型。
PLACEHOLDER_MODEL = "placeholder model"


def load_model():
    """根据 config 中的设置，返回占位模型或真实模型。"""
    if config.USE_PLACEHOLDER_MODEL:
        return PLACEHOLDER_MODEL
    return load_real_model(config.MODEL_PATH)


def predict(model, image_path):
    """对一张图片进行分类。

    返回概率最高的类别及其概率，例如 ("malignant", 0.87)。
    图片无法读取时抛出 ImageLoadError。
    """
    image = load_image(image_path)
    if model is PLACEHOLDER_MODEL:
        probabilities = placeholder_probabilities(image)
    else:
        probabilities = real_probabilities(model, image)

    # 模型输出的概率个数必须和类别个数一致
    if len(probabilities) != len(config.CLASSES):
        raise ValueError(
            f"The model gave {len(probabilities)} probabilities, "
            f"but config.CLASSES lists {len(config.CLASSES)} classes."
        )
    best = max(range(len(config.CLASSES)), key=lambda i: probabilities[i])
    return config.CLASSES[best], float(probabilities[best])


def probabilities_for_all_classes(label, probability):
    """把 ("malignant", 0.87) 转换成 {"benign": 0.13, "malignant": 0.87}。

    只适用于两个类别：另一个类别的概率就是 1 减去这个概率。
    """
    if len(config.CLASSES) != 2:
        raise ValueError("probabilities_for_all_classes() assumes exactly two classes.")
    return {name: (probability if name == label else 1.0 - probability)
            for name in config.CLASSES}


# ---------------------------------------------------------------- 占位模型

def placeholder_probabilities(image):
    """占位模型：为每个类别返回一个假的概率。

    概率由图片像素的校验和计算得到，同一张图片每次结果相同，
    但结果没有任何医学意义。
    """
    checksum = hashlib.sha256(image.tobytes()).digest()
    p_malignant = 0.05 + 0.90 * checksum[0] / 255   # 范围在 0.05 到 0.95 之间
    return [1.0 - p_malignant, p_malignant]         # 顺序与 config.CLASSES 相同


# ---------------------------------------------------------------- 真实模型
# TODO：最终模型确定后补全下面两个函数。

def load_real_model(model_path):
    """从 model_path 加载训练好的模型并返回。"""
    model_path = Path(model_path)
    if not model_path.is_file():
        raise ModelLoadError(
            f"The model file was not found:\n{model_path}\n\n"
            "Put the trained model file in the 'models' folder, or set "
            "USE_PLACEHOLDER_MODEL = True in config.py to run in demo mode."
        )
    # TODO：在这里加载模型，例如 PyTorch 用 torch.load(...)，scikit-learn 用 joblib.load(...)
    raise ModelLoadError(
        "Loading the trained model is not implemented yet "
        "(see load_real_model() in predict.py). Set USE_PLACEHOLDER_MODEL = True "
        "in config.py to run in demo mode."
    )


def real_probabilities(model, image):
    """用真实模型计算每个类别的概率，顺序与 config.CLASSES 相同。

    TODO：先做与训练时完全相同的预处理（如果用到特征提取，也要用同一套方法），
    再让模型输出各类别的概率。
    """
    raise NotImplementedError("real_probabilities() in predict.py is not implemented yet.")
