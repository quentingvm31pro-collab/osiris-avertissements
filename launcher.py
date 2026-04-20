import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from ui.login_window import LoginWindow
from utils import resource_path


def main():
    app_qt = QApplication(sys.argv)
    app_qt.setApplicationName("OSIRIS - Avertissements")
    app_qt.setWindowIcon(QIcon(resource_path("icon.ico")))

    window = LoginWindow()
    window.show()

    sys.exit(app_qt.exec())


if __name__ == "__main__":
    main()