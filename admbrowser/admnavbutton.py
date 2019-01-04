from PyQt5 import QtWidgets as qtw
from PyQt5 import QtCore as qtc


class AdmNavButton(qtw.QToolButton):
    """A tool button that emits a QUrl when clicked"""

    clicked = qtc.pyqtSignal(qtc.QUrl)

    def __init__(self, *args, url=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = qtc.QUrl(url)
        super().clicked.connect(self._on_clicked)

    def _on_clicked(self):
        self.clicked[qtc.QUrl].emit(self.url)
