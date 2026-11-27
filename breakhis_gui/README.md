# BreaKHis Classifier: GUI

A desktop program for the BIA4 ICA1 group project. Open an H&E-stained breast
biopsy image from the BreaKHis dataset and see whether the model classifies it
as **benign** or **malignant**.

> **Status: demo v0.1.** The trained model is not connected yet. Until it is,
> a placeholder returns made-up results so that the interface can be built and
> tested. The window shows a yellow "DEMO MODE" banner while this is the case.

## Install and start on Windows

1. Install Python 3.9 or newer from [python.org](https://www.python.org/downloads/).
   On the first screen of the installer, tick **Add python.exe to PATH**.
2. Double-click **`install_requirements.bat`** (needed only once).
3. Double-click **`start_gui.bat`** to open the program.

## Install and start from a terminal (Windows, macOS or Linux)

```
pip install -r requirements.txt
python gui.py
```

Tkinter, the GUI library, comes with Python from python.org on Windows and
macOS. On Linux, also run `sudo apt install python3-tk` (plus
`python3-pil.imagetk` if Pillow was installed with apt rather than pip).

## Use

1. Click **Open image…** (or press Ctrl+O) and choose a PNG, JPG, TIFF or BMP file.
2. Click **Analyse** (or press Enter).
3. The result shows the predicted class and one bar per class. If the most
   likely class is below 65 % (`LOW_CONFIDENCE` in `config.py`), a note asks
   for a pathologist's review.

## How wrong input is handled

| Situation | What happens |
|---|---|
| Not an image file (for example `.txt`) | A message lists the accepted file types. |
| Damaged or empty image file | A message says the file could not be read. |
| Image with transparency, or in greyscale | Converted to 3-channel RGB automatically. |
| Image deleted after it was opened | A message appears when you click Analyse. |
| Model file missing | A message at start-up; images can still be opened and viewed. |
| Any unexpected error during analysis | A message is shown and the program keeps running. |

## Files

| File | Purpose |
|---|---|
| `gui.py` | The window: buttons, preview, result display and messages. |
| `predict.py` | Opens images and the model. `predict(model, path)` returns `(label, probability)`. |
| `config.py` | Settings shared by both files: class order, model path, demo switch. |
| `test_predict.py` | Automatic tests for `predict.py`. |
| `start_gui.bat` | Windows: double-click to start the program. |
| `install_requirements.bat` | Windows: double-click once to install the required libraries. |

## Tests

```
python -m unittest -v
```

## Connecting the real model

1. Put the trained model file in a `models/` folder here (the path is `MODEL_PATH` in `config.py`).
2. In `predict.py`, fill in `load_real_model()` and `real_probabilities()`, using exactly
   the same pre-processing (and feature extraction, if any) as the training code.
3. Set `USE_PLACEHOLDER_MODEL = False` in `config.py`.

`gui.py` does not need to change.

*For research and teaching only. Not for clinical diagnosis.*
