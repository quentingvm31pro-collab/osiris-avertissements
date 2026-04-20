import sys
from PySide6.QtWidgets import QApplication

from database import init_database, seed_mock_data
from data.mock_data import mock_players
from ui.login_window import LoginWindow


def main():
    # Init DB locale (si tu veux garder du fallback/mock)
    init_database()
    seed_mock_data(mock_players)

    # Lancement app
    app = QApplication(sys.argv)
    window = LoginWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()