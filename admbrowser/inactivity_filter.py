from PyQt5.QtCore import (
    QTimer,
    QObject,
    QEvent,
    pyqtSignal,
)


class InactivityFilter(QTimer):
    """This defines an inactivity filter.

    It's basically a timer that resets when user "activity"
    (Mouse/Keyboard events) are detected in the main application.
    """
    activity = pyqtSignal()

    monitored_events = (
        QEvent.MouseMove,
        QEvent.MouseButtonPress,
        QEvent.HoverMove,
        QEvent.KeyPress,
        QEvent.KeyRelease
    )

    def __init__(self, timeout=0, parent=None):
        """Constructor for the class.

        args:
          timeout -- number of seconds before timer times out (integer)
        """
        super(InactivityFilter, self).__init__(parent)
        # timeout needs to be converted from seconds to milliseconds
        self.timeout_time = timeout * 1000
        self.setInterval(self.timeout_time)
        self.start()

    def eventFilter(self, object, event):
        """Overridden from QTimer.eventFilter"""
        if event.type() in self.monitored_events:
            self.activity.emit()
            self.start(self.timeout_time)
        return QObject.eventFilter(self, object, event)
