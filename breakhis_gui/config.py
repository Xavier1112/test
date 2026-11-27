"""
config.py：GUI 和预测代码共用的设置。

多个文件都要用到的值统一放在这里，避免各自保存一份导致不一致。
"""

from pathlib import Path

# 本文件所在的文件夹。下面的路径都以它为起点，
# 这样无论从哪个文件夹启动程序，都能找到对应的文件。
PROJECT_DIR = Path(__file__).resolve().parent

# 类别名称，顺序必须和模型输出的顺序一致：
# 下标 0 = 良性（benign），下标 1 = 恶性（malignant）。
CLASSES = ["benign", "malignant"]

# 训练好的模型文件。最终模型确定后再修改文件名和格式
# （例如 PyTorch 的 best_model.pth，或 scikit-learn 的 model.joblib）。
MODEL_PATH = PROJECT_DIR / "models" / "best_model.pth"

# True：使用占位模型（演示模式），结果是根据像素算出的假数据，只用于测试界面。
# False：使用训练好的真实模型（见 predict.py 末尾的“真实模型”部分）。
USE_PLACEHOLDER_MODEL = True

# 最可能类别的概率低于这个值时，界面提示结果不确定、建议人工复核。
LOW_CONFIDENCE = 0.65

# 支持的图片格式（比较时统一转成小写）。
SUPPORTED_EXTENSIONS = (".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp")
