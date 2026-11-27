"""
gui.py：BreaKHis 乳腺肿瘤病理图像良恶性分类的桌面界面。

在本文件夹中运行：

    python gui.py

Windows 下也可以双击 start_gui.bat 启动（不会出现命令行窗口）。

功能：
  1. 打开一张病理图片（PNG、JPG、TIFF 或 BMP）。
  2. 预览图片。
  3. 点击 “Analyse”（或按回车）进行分类。
  4. 显示结果：预测类别、每个类别的概率条，以及置信度提示。

本文件只负责界面和用户操作。读取图片和调用模型都在 predict.py 中完成，
因此把占位模型换成真实模型时，本文件不需要修改。
"""

import sys
import tkinter as tk
import tkinter.font as tkfont
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from PIL import ImageTk

import config
from predict import (
    ImageLoadError,
    ModelLoadError,
    load_image,
    load_model,
    predict,
    probabilities_for_all_classes,
)

# ---------------------------------------------------------------- 外观设置

WINDOW_TITLE = "BreaKHis Classifier"
PREVIEW_SIZE = (440, 290)  # 预览区大小（像素）；BreaKHis 原图为 700 x 460，保持相近的比例
BAR_LENGTH = 170           # 概率为 100% 时概率条的长度（像素）

CLASS_NAMES = {"benign": "Benign", "malignant": "Malignant"}  # 界面上显示的类别名称
CLASS_COLOURS = {"benign": "#1878B5", "malignant": "#D2561C"}

TEXT_COLOUR = "#1D1928"
MUTED_COLOUR = "#6A647E"
WARNING_COLOUR = "#B3261E"
PREVIEW_BACKGROUND = "#EFECF4"
BAR_TRACK_COLOUR = "#E2DEEA"


def image_file_patterns():
    """返回“打开图片”对话框使用的文件类型，例如 "*.png *.jpg"。

    Windows 的文件名不区分大小写；macOS 和 Linux 区分，
    所以在这两个系统上额外加入大写形式（*.PNG）。
    """
    patterns = [f"*{ext}" for ext in config.SUPPORTED_EXTENSIONS]
    if not sys.platform.startswith("win"):
        patterns += [f"*{ext.upper()}" for ext in config.SUPPORTED_EXTENSIONS]
    return " ".join(patterns)


# “打开图片”对话框中的文件类型选项
FILE_TYPES = [
    ("Image files", image_file_patterns()),
    ("All files", "*"),
]


class ClassifierApp:
    """主窗口：保存所有控件，以及当前加载的模型和图片。"""

    def __init__(self, root):
        self.root = root
        self.model = None          # 模型加载成功后保存在这里
        self.model_failed = False  # 模型加载失败时为 True
        self.image_path = None     # 当前显示的图片路径
        self.preview_photo = None  # 必须保留预览图片的引用，否则图片会被回收，界面上显示空白

        # 系统开启显示缩放（例如 150%）时，图片和概率条按比例放大
        self.scale = max(1.0, root.winfo_fpixels("1i") / 96)

        root.title(WINDOW_TITLE)
        self.make_fonts_and_styles()
        self.build_widgets()
        self.bind_shortcuts()
        self.show_empty_result()

        # 限制窗口的最小尺寸，避免控件被遮挡
        root.update_idletasks()
        root.minsize(root.winfo_reqwidth(), root.winfo_reqheight())

        # 先显示窗口，再加载模型（真实模型加载可能需要几秒）
        root.after(100, self.load_model_at_startup)

    # ------------------------------------------------------------ 创建界面

    def make_fonts_and_styles(self):
        """创建界面使用的字体和 ttk 样式。"""
        family = tkfont.nametofont("TkDefaultFont").actual("family")
        self.fonts = {
            "title": tkfont.Font(family=family, size=15, weight="bold"),
            "heading": tkfont.Font(family=family, size=12, weight="bold"),
            "verdict": tkfont.Font(family=family, size=24, weight="bold"),
            "normal": tkfont.Font(family=family, size=10),
            "bold": tkfont.Font(family=family, size=10, weight="bold"),
        }
        style = ttk.Style(self.root)
        style.configure("Title.TLabel", font=self.fonts["title"], foreground=TEXT_COLOUR)
        style.configure("Heading.TLabel", font=self.fonts["heading"], foreground=TEXT_COLOUR)
        style.configure("Muted.TLabel", foreground=MUTED_COLOUR)
        # 普通 tk 控件（Label、Canvas）的背景色要和 ttk 控件保持一致
        self.background = style.lookup("TFrame", "background") or "#F0F0F0"

    def build_widgets(self):
        """创建所有控件并放到窗口中。"""
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        page = ttk.Frame(self.root, padding=16)
        page.grid(row=0, column=0, sticky="nsew")
        page.columnconfigure(1, weight=1)
        page.rowconfigure(3, weight=1)

        # 第 0-1 行：标题和副标题
        ttk.Label(page, text="Breast tumour histology classifier",
                  style="Title.TLabel").grid(row=0, column=0, columnspan=2, sticky="w")
        ttk.Label(page, text="Is this H&E-stained biopsy image benign or malignant? (BreaKHis dataset)",
                  style="Muted.TLabel").grid(row=1, column=0, columnspan=2, sticky="w", pady=(2, 12))

        # 第 2 行：演示模式提示，只在使用占位模型时显示
        if config.USE_PLACEHOLDER_MODEL:
            tk.Label(page, text="DEMO MODE: placeholder model. The results are made up "
                                "and are NOT real predictions.",
                     bg="#FFF1C2", fg="#5C4400", anchor="w", padx=10, pady=6).grid(
                row=2, column=0, columnspan=2, sticky="ew", pady=(0, 12))

        # 第 3 行左侧：打开图片按钮、图片预览、Analyse 按钮
        image_panel = ttk.Frame(page)
        image_panel.grid(row=3, column=0, sticky="nw", padx=(0, 24))

        top_row = ttk.Frame(image_panel)
        top_row.pack(fill="x")
        ttk.Button(top_row, text="Open image…", command=self.open_image).pack(side="left")
        self.file_label = ttk.Label(top_row, text="No image opened yet", style="Muted.TLabel")
        self.file_label.pack(side="left", padx=10)

        width, height = (round(size * self.scale) for size in PREVIEW_SIZE)
        preview_box = tk.Frame(image_panel, width=width, height=height, bg=PREVIEW_BACKGROUND)
        preview_box.pack(pady=10)
        preview_box.pack_propagate(False)  # 固定预览区大小，不随里面的内容变化
        self.preview = tk.Label(preview_box, text="Open an image to see it here",
                                bg=PREVIEW_BACKGROUND, fg=MUTED_COLOUR)
        self.preview.pack(fill="both", expand=True)

        self.analyse_button = ttk.Button(image_panel, text="Analyse",
                                         command=self.analyse, state="disabled")
        self.analyse_button.pack(fill="x")

        # 第 3 行右侧：结果区
        result_panel = ttk.Frame(page)
        result_panel.grid(row=3, column=1, sticky="nsew")
        ttk.Label(result_panel, text="Result", style="Heading.TLabel").pack(anchor="w")
        self.verdict = tk.Label(result_panel, font=self.fonts["verdict"],
                                bg=self.background, anchor="w")
        self.verdict.pack(fill="x", pady=(4, 8))
        self.bars = tk.Canvas(result_panel, bg=self.background, highlightthickness=0)
        self.bars.pack(anchor="w")
        wrap = round(320 * self.scale)
        self.note = ttk.Label(result_panel, wraplength=wrap, justify="left")
        self.note.pack(anchor="w", pady=(12, 0))
        ttk.Label(result_panel, text="For research and teaching only. Not for clinical diagnosis.",
                  style="Muted.TLabel", wraplength=wrap, justify="left").pack(side="bottom", anchor="w")

        # 窗口底部：状态栏。width=1 防止过长的提示文字把整个窗口撑宽
        self.status = ttk.Label(self.root, relief="sunken", anchor="w", padding=(8, 3), width=1)
        self.status.grid(row=1, column=0, sticky="ew")

    def bind_shortcuts(self):
        """快捷键：Ctrl+O 打开图片，回车开始分析。"""
        self.root.bind("<Control-o>", lambda event: self.open_image())
        self.root.bind("<Control-O>", lambda event: self.open_image())
        self.root.bind("<Return>", lambda event: self.analyse())

    # ------------------------------------------------------------ 响应用户操作

    def load_model_at_startup(self):
        """程序启动时加载一次模型。"""
        self.set_status("Loading the model…")
        self.root.update_idletasks()
        try:
            self.model = load_model()
        except ModelLoadError as error:
            self.report_model_problem(str(error))
            return
        except Exception as error:  # 其他意外错误：弹窗提示，程序不退出
            self.report_model_problem(f"Unexpected error while loading the model:\n\n{error}")
            return

        if config.USE_PLACEHOLDER_MODEL:
            self.set_status("Ready (demo mode). Open an image to begin.")
        else:
            self.set_status(f"Ready. Model: {config.MODEL_PATH.name}. Open an image to begin.")
        self.update_analyse_button()

    def report_model_problem(self, message):
        """提示模型不可用。此时仍然可以打开和查看图片，但不能分析。"""
        self.model_failed = True
        self.set_status("The model could not be loaded, so analysis is switched off.")
        self.show_empty_result()
        messagebox.showerror("Model not available", message, parent=self.root)

    def next_step_hint(self):
        """根据模型是否可用，返回下一步操作的提示。"""
        if self.model_failed:
            return "Analysis is switched off because the model could not be loaded."
        return "Click Analyse."

    def open_image(self):
        """弹出文件选择对话框，选中图片后显示出来。"""
        path = filedialog.askopenfilename(parent=self.root, title="Open a histology image",
                                          filetypes=FILE_TYPES)
        if path:  # 用户点“取消”时返回空字符串
            self.show_image_file(path)

    def show_image_file(self, path):
        """检查 path 指向的文件，可以使用时显示在预览区。"""
        try:
            image = load_image(path)
        except ImageLoadError as error:
            # 保留原来显示的内容，弹窗说明原因
            self.set_status("That file could not be opened. Please choose another image.")
            messagebox.showerror("Cannot open this file", str(error), parent=self.root)
            return

        self.image_path = Path(path)
        self.show_preview(image)
        self.file_label.configure(text=self.image_path.name)
        self.show_empty_result()
        width, height = image.size
        self.set_status(f"Opened {self.image_path.name} ({width} × {height} pixels). "
                        + self.next_step_hint())
        self.update_analyse_button()

    def show_preview(self, image):
        """在预览区显示缩小后的图片。"""
        box = (round(PREVIEW_SIZE[0] * self.scale), round(PREVIEW_SIZE[1] * self.scale))
        small = image.copy()
        small.thumbnail(box)  # 按原比例缩小到预览区大小
        self.preview_photo = ImageTk.PhotoImage(small)
        self.preview.configure(image=self.preview_photo, text="")

    def analyse(self):
        """用模型分析当前图片并显示结果。"""
        if self.model is None or self.image_path is None:
            return  # 还没有可分析的图片或模型（此时按钮本来就是禁用的）

        self.set_status("Analysing…")
        self.root.update_idletasks()  # 先刷新状态栏，再开始计算
        try:
            label, probability = predict(self.model, self.image_path)
        except ImageLoadError as error:  # 例如：打开之后图片被移动或删除
            self.set_status("Analysis stopped: the image could not be read.")
            messagebox.showerror("Cannot read the image", str(error), parent=self.root)
            return
        except Exception as error:  # 其他意外错误：弹窗提示，程序不退出
            self.set_status("Analysis failed.")
            messagebox.showerror("Analysis failed",
                                 f"Something went wrong while analysing the image:\n\n{error}",
                                 parent=self.root)
            return

        self.show_result(label, probability)
        demo = " (demo result)" if config.USE_PLACEHOLDER_MODEL else ""
        self.set_status(f"Done: {self.image_path.name} → "
                        f"{CLASS_NAMES.get(label, label).lower()}, {probability:.0%}{demo}.")

    # ------------------------------------------------------------ 显示结果

    def show_result(self, label, probability):
        """显示预测类别、每个类别的概率条和置信度提示。"""
        self.verdict.configure(text=CLASS_NAMES.get(label, label),
                               fg=CLASS_COLOURS.get(label, TEXT_COLOUR))
        self.draw_bars(probabilities_for_all_classes(label, probability))
        if probability < config.LOW_CONFIDENCE:
            self.note.configure(foreground=WARNING_COLOUR, text=(
                f"The model is unsure: the most likely class has only {probability:.0%}. "
                "Please ask a pathologist to review this image."))
        else:
            self.note.configure(foreground=TEXT_COLOUR, text=(
                f"Model confidence: {probability:.0%}. "
                "A pathologist should still confirm the result."))

    def show_empty_result(self):
        """清空结果区（程序启动时，以及每次打开新图片时）。"""
        self.verdict.configure(text="—", fg=MUTED_COLOUR)
        self.draw_bars(None)
        if self.model_failed:
            self.note.configure(foreground=WARNING_COLOUR, text=self.next_step_hint())
        else:
            self.note.configure(foreground=MUTED_COLOUR, text="Open an image, then click Analyse.")

    def draw_bars(self, probabilities):
        """为每个类别画一条水平概率条。

        probabilities 是类似 {"benign": 0.13, "malignant": 0.87} 的字典；
        为 None 时只画空的概率条。
        """
        canvas = self.bars
        canvas.delete("all")
        normal, bold = self.fonts["normal"], self.fonts["bold"]

        # 按文字的实际宽度排版，开启显示缩放时也不会错位
        name_width = max(normal.measure(CLASS_NAMES.get(name, name)) for name in config.CLASSES) + 12
        bar_length = round(BAR_LENGTH * self.scale)
        bar_height = normal.metrics("linespace")
        row_height = bar_height + round(12 * self.scale)
        canvas.configure(width=name_width + bar_length + 10 + bold.measure("100%") + 4,
                         height=row_height * len(config.CLASSES))

        for row, name in enumerate(config.CLASSES):
            top = row * row_height + 4
            middle = top + bar_height / 2
            canvas.create_text(0, middle, text=CLASS_NAMES.get(name, name), anchor="w",
                               font=normal, fill=TEXT_COLOUR)
            canvas.create_rectangle(name_width, top, name_width + bar_length, top + bar_height,
                                    fill=BAR_TRACK_COLOUR, outline="")
            if probabilities is None:
                value_text = "–"
            else:
                share = probabilities[name]
                canvas.create_rectangle(name_width, top, name_width + bar_length * share,
                                        top + bar_height,
                                        fill=CLASS_COLOURS.get(name, TEXT_COLOUR), outline="")
                value_text = f"{share:.0%}"
            canvas.create_text(name_width + bar_length + 10, middle, text=value_text, anchor="w",
                               font=bold, fill=TEXT_COLOUR)

    # ------------------------------------------------------------ 辅助函数

    def update_analyse_button(self):
        """只有模型和图片都已加载时，才允许点击 Analyse。"""
        ready = self.model is not None and self.image_path is not None
        self.analyse_button.configure(state="normal" if ready else "disabled")

    def set_status(self, text):
        """在窗口底部的状态栏显示提示文字。"""
        self.status.configure(text=text)


def make_text_sharp_on_windows():
    """在开启了显示缩放的 Windows 电脑上避免界面文字模糊。

    macOS 和 Linux 上不做任何操作。
    """
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except (AttributeError, OSError):
        pass


def main():
    make_text_sharp_on_windows()
    root = tk.Tk()

    # 双击 start_gui.bat 启动时没有命令行窗口，报错信息无处输出，
    # 所以意外错误统一用弹窗显示，而不是悄悄消失。
    root.report_callback_exception = lambda kind, error, trace: messagebox.showerror(
        "Unexpected error", f"{kind.__name__}: {error}", parent=root)
    try:
        ClassifierApp(root)
    except Exception as error:
        messagebox.showerror("The program could not start",
                             f"{type(error).__name__}: {error}", parent=root)
        root.destroy()
        return
    root.mainloop()


if __name__ == "__main__":
    main()
