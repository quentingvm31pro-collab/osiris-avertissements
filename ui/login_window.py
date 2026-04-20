from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from api_client import APIClient, APIClientError
from ui.register_dialog import RegisterDialog


class LoginWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("Connexion - OSIRIS")
        self.resize(420, 260)

        self.api = APIClient()
        self.logged_officer = None
        self.main_window = None

        self.title_label = QLabel("Connexion officier")
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold;")

        self.info_label = QLabel(
            "Si le serveur gratuit est en veille, la première connexion peut prendre un peu de temps."
        )
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet("color: #bbbbbb; font-size: 12px;")

        self.login_input = QLineEdit()
        self.login_input.setPlaceholderText("Email")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Mot de passe")
        self.password_input.setEchoMode(QLineEdit.Password)

        self.login_button = QPushButton("Se connecter")
        self.login_button.clicked.connect(self.handle_login)

        self.register_button = QPushButton("Créer un compte")
        self.register_button.clicked.connect(self.open_register_dialog)

        layout = QVBoxLayout()
        layout.addWidget(self.title_label)
        layout.addWidget(self.info_label)
        layout.addWidget(self.login_input)
        layout.addWidget(self.password_input)
        layout.addWidget(self.login_button)
        layout.addWidget(self.register_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.apply_dark_style()

    def apply_dark_style(self) -> None:
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
            }

            QWidget {
                background-color: #1e1e1e;
                color: #f0f0f0;
                font-size: 13px;
            }

            QLineEdit {
                background-color: #2a2a2a;
                border: 1px solid #444;
                border-radius: 6px;
                padding: 8px;
            }

            QPushButton {
                background-color: #3a3a3a;
                border: 1px solid #555;
                border-radius: 6px;
                padding: 10px;
            }

            QPushButton:hover {
                background-color: #4a4a4a;
            }

            QPushButton:disabled {
                background-color: #2b2b2b;
                color: #888888;
            }
        """)

    def set_loading_state(self, is_loading: bool, message: str = "") -> None:
        self.login_button.setDisabled(is_loading)
        self.register_button.setDisabled(is_loading)
        self.login_input.setDisabled(is_loading)
        self.password_input.setDisabled(is_loading)

        if is_loading:
            self.info_label.setText(message or "Connexion au serveur...")
            QGuiApplication.setOverrideCursor(Qt.WaitCursor)
        else:
            self.info_label.setText(
                "Si le serveur gratuit est en veille, la première connexion peut prendre un peu de temps."
            )
            QGuiApplication.restoreOverrideCursor()

    def handle_login(self) -> None:
        email = self.login_input.text().strip()
        password = self.password_input.text()

        if not email or not password:
            QMessageBox.warning(self, "Champs manquants", "Remplis l'email et le mot de passe.")
            return

        self.set_loading_state(
            True,
            "Connexion au serveur... le premier démarrage peut prendre jusqu'à une minute.",
        )

        try:
            result = self.api.login(email, password)
        except APIClientError as e:
            QMessageBox.warning(self, "Connexion refusée", str(e))
            return
        except Exception as e:
            QMessageBox.warning(self, "Connexion refusée", f"Erreur de connexion : {e}")
            return
        finally:
            self.set_loading_state(False)

        officer = result.get("officer")
        if officer is None:
            QMessageBox.warning(self, "Connexion refusée", "Réponse serveur invalide.")
            return

        self.logged_officer = officer

        from ui.main_window import MainWindow
        self.main_window = MainWindow(officer, self.api)
        self.main_window.show()
        self.close()

    def open_register_dialog(self) -> None:
        dialog = RegisterDialog(self.api, self)
        dialog.exec()