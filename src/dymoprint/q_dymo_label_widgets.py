import os

import dymoprint_fonts
from PyQt5 import QtCore
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout, QComboBox, QSpinBox, QPlainTextEdit, QLineEdit, QPushButton, \
    QFileDialog, QMessageBox

from .font_config import parse_fonts


class BaseDymoLabelWidget(QWidget):
    """
    A base class for creating Dymo label widgets.
    Signals:
    --------
    itemRenderSignal : PyQtSignal
        Signal emitted when the content of the label is changed.
    Methods:
    --------
    content_changed()
        Emits the itemRenderSignal when the content of the label is changed.
    render_label()
        Abstract method to be implemented by subclasses for rendering the label.
    """
    itemRenderSignal = QtCore.pyqtSignal(name='itemRenderSignal')

    def content_changed(self):
        """
        Emits the itemRenderSignal when the content of the label is changed.
        """
        self.itemRenderSignal.emit()

    def render_label(self):
        """
        Abstract method to be implemented by subclasses for rendering the label.
        """
        pass


class TextDymoLabelWidget(BaseDymoLabelWidget):
    """
    A widget for rendering text on a Dymo label.
    Args:
        render_engine (RenderEngine): The rendering engine to use.
        parent (QWidget): The parent widget of this widget.
    Attributes:
        render_engine (RenderEngine): The rendering engine used by this widget.
        label (QPlainTextEdit): The text label to be rendered on the Dymo label.
        font_style (QComboBox): The font style selection dropdown.
        font_size (QSpinBox): The font size selection spinner.
        draw_frame (QSpinBox): The frame width selection spinner.
    Signals:
        itemRenderSignal: A signal emitted when the content of the label changes.
    """

    def __init__(self, render_engine, parent=None):
        super(TextDymoLabelWidget, self).__init__(parent)
        self.render_engine = render_engine

        self.label = QPlainTextEdit("text")
        self.label.setFixedHeight(15 * (len(self.label.toPlainText().splitlines()) + 2))
        self.setFixedHeight(self.label.height() + 10)
        self.font_style = QComboBox()
        self.font_size = QSpinBox()
        self.font_size.setMaximum(100)
        self.font_size.setMinimum(0)
        self.font_size.setSingleStep(1)
        self.font_size.setValue(90)
        self.draw_frame = QSpinBox()
        for (name, font_path) in parse_fonts():
            self.font_style.addItem(name, font_path)
            if "Regular" in name:
                self.font_style.setCurrentText(name)

        layout = QHBoxLayout()
        ICON_DIR = os.path.dirname(dymoprint_fonts.__file__)
        item_icon = QLabel()
        item_icon.setPixmap(QIcon(os.path.join(ICON_DIR, "txt_icon.png")).pixmap(32, 32))
        item_icon.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(item_icon)
        layout.addWidget(self.label)
        layout.addWidget(QLabel("Font:"))
        layout.addWidget(self.font_style)
        layout.addWidget(QLabel("Size [%]:"))
        layout.addWidget(self.font_size)
        layout.addWidget(QLabel("Frame Width:"))
        layout.addWidget(self.draw_frame)
        self.label.textChanged.connect(self.content_changed)
        self.draw_frame.valueChanged.connect(self.content_changed)
        self.font_size.valueChanged.connect(self.content_changed)
        self.font_style.currentTextChanged.connect(self.content_changed)
        self.setLayout(layout)

    def content_changed(self):
        """
        Updates the height of the label and emits the itemRenderSignal when the content of the label changes.
        """
        self.label.setFixedHeight(15 * (len(self.label.toPlainText().splitlines()) + 2))
        self.setFixedHeight(self.label.height() + 10)
        self.itemRenderSignal.emit()

    def render_label(self):
        """
        Renders the label using the current settings.
        Returns:
            QImage: The rendered label image.
        Raises:
            QMessageBox.warning: If the rendering fails.
        """
        try:
            render = self.render_engine.render_text(labeltext=self.label.toPlainText().splitlines(),
                                                    font_file_name=self.font_style.currentData(),
                                                    frame_width=self.draw_frame.value(),
                                                    font_size_ratio=self.font_size.value() / 100.0)
            return render
        except BaseException as err:
            QMessageBox.warning(self, "TextDymoLabelWidget render fail!", f"{err}")
            return self.render_engine.render_empty()


class QrDymoLabelWidget(BaseDymoLabelWidget):
    """
    A widget for rendering QR codes on Dymo labels.
    Args:
        render_engine (RenderEngine): The render engine to use for rendering the QR code.
        parent (QWidget, optional): The parent widget. Defaults to None.
    """

    def __init__(self, render_engine, parent=None):
        """
        Initializes the QrDymoLabelWidget.
        Args:
            render_engine (RenderEngine): The render engine to use for rendering the QR code.
            parent (QWidget, optional): The parent widget. Defaults to None.
        """
        super(QrDymoLabelWidget, self).__init__(parent)
        self.render_engine = render_engine

        self.label = QLineEdit("")
        layout = QHBoxLayout()
        ICON_DIR = os.path.dirname(dymoprint_fonts.__file__)
        item_icon = QLabel()
        item_icon.setPixmap(QIcon(os.path.join(ICON_DIR, "qr_icon.png")).pixmap(32, 32))
        item_icon.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(item_icon)
        layout.addWidget(self.label)
        self.label.textChanged.connect(self.content_changed)
        self.setLayout(layout)

    def render_label(self):
        """
        Renders the QR code on the Dymo label.
        Returns:
            bytes: The rendered QR code as bytes.
        Raises:
            QMessageBox.warning: If the rendering fails.
        """
        try:
            render = self.render_engine.render_qr(self.label.text())
            return render

        except BaseException as err:
            QMessageBox.warning(self, "QrDymoLabelWidget render fail!", f"{err}")
            return self.render_engine.render_empty()


class BarcodeDymoLabelWidget(BaseDymoLabelWidget):
    """
    A widget for rendering barcode labels using the Dymo label printer.
    Args:
        render_engine (DymoRenderEngine): An instance of the DymoRenderEngine class.
        parent (QWidget): The parent widget of this widget.
    Attributes:
        render_engine (DymoRenderEngine): An instance of the DymoRenderEngine class.
        label (QLineEdit): A QLineEdit widget for entering the content of the barcode label.
        codding (QComboBox): A QComboBox widget for selecting the type of barcode to render.
    Signals:
        content_changed(): Emitted when the content of the label or the selected barcode type changes.
    Methods:
        __init__(self, render_engine, parent=None): Initializes the widget.
        render_label(self): Renders the barcode label using the current content and barcode type.
    """

    def __init__(self, render_engine, parent=None):
        super(BarcodeDymoLabelWidget, self).__init__(parent)
        self.render_engine = render_engine

        self.label = QLineEdit("")
        layout = QHBoxLayout()
        ICON_DIR = os.path.dirname(dymoprint_fonts.__file__)
        item_icon = QLabel()
        item_icon.setPixmap(QIcon(os.path.join(ICON_DIR, "barcode_icon.png")).pixmap(32, 32))
        item_icon.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter)
        self.codding = QComboBox()
        self.codding.addItems([
            "code39",
            "code128",
            "ean",
            "ean13",
            "ean8",
            "gs1",
            "gtin",
            "isbn",
            "isbn10",
            "isbn13",
            "issn",
            "jan",
            "pzn",
            "upc",
            "upca",
        ])

        layout.addWidget(item_icon)
        layout.addWidget(self.label)
        layout.addWidget(QLabel("Codding:"))
        layout.addWidget(self.codding)

        self.label.textChanged.connect(self.content_changed)
        self.codding.currentTextChanged.connect(self.content_changed)
        self.setLayout(layout)

    def render_label(self):
        """
        Renders the barcode label using the current content and barcode type.
        Returns:
            QPixmap: A QPixmap object representing the rendered barcode label.
        """
        try:
            render = self.render_engine.render_barcode(self.label.text(), self.codding.currentText())
            return render

        except BaseException as err:
            QMessageBox.warning(self, "BarcodeDymoLabelWidget render fail!", f"{err}")
            return self.render_engine.render_empty()


class ImageDymoLabelWidget(BaseDymoLabelWidget):
    """
    A widget for rendering image-based Dymo labels.
    Args:
        render_engine (RenderEngine): The render engine to use for rendering the label.
        parent (QWidget, optional): The parent widget. Defaults to None.
    """

    def __init__(self, render_engine, parent=None):
        """
        Initializes the ImageDymoLabelWidget.
        Args:
            render_engine (RenderEngine): The render engine to use for rendering the label.
            parent (QWidget, optional): The parent widget. Defaults to None.
        """
        super(ImageDymoLabelWidget, self).__init__(parent)
        self.render_engine = render_engine

        self.label = QLineEdit("")
        layout = QHBoxLayout()
        ICON_DIR = os.path.dirname(dymoprint_fonts.__file__)
        item_icon = QLabel()
        item_icon.setPixmap(QIcon(os.path.join(ICON_DIR, "img_icon.png")).pixmap(32, 32))
        item_icon.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter)

        button = QPushButton('Select file')
        file_dialog = QFileDialog()
        button.clicked.connect(lambda: self.label.setText(file_dialog.getOpenFileName()[0]))

        layout.addWidget(item_icon)
        layout.addWidget(self.label)
        layout.addWidget(button)

        self.label.textChanged.connect(self.content_changed)
        self.setLayout(layout)

    def render_label(self):
        """
        Renders the label using the render engine and the selected image file.
        Returns:
            QPixmap: The rendered label as a QPixmap.
        """
        try:
            render = self.render_engine.render_picture(self.label.text())
            return render
        except BaseException as err:
            QMessageBox.warning(self, "ImageDymoLabelWidget render fail!", f"{err}")
            return self.render_engine.render_empty()
