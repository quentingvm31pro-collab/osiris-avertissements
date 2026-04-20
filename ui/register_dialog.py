from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
)

from api_client import APIClientError


class RegisterDialog(QDialog):
    def __init__(self, api, parent=None) -> None:
        super().__init__(parent)
        self.api = api

        self.setWindowTitle("Créer un compte officier")
        self.setMinimumWidth(420)

        self.pseudo_input = QLineEdit()
        self.email_input = QLineEdit()
        self.password_input = QLineEdit()
        self.confirm_password_input = QLineEdit()

        self.password_input.setEchoMode(QLineEdit.Password)
        self.confirm_password_input.setEchoMode(QLineEdit.Password)

        form = QFormLayout()
        form.addRow("Pseudo en jeu :", self.pseudo_input)
        form.addRow("Email :", self.email_input)
        form.addRow("Mot de passe :", self.password_input)
        form.addRow("Confirmer :", self.confirm_password_input)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal,
            self,
        )
        self.buttons.accepted.connect(self.handle_register)
        self.buttons.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addWidget(self.buttons)
        self.setLayout(layout)

    def set_loading_state(self, is_loading: bool) -> None:
        ok_button = self.buttons.button(QDialogButtonBox.Ok)
        cancel_button = self.buttons.button(QDialogButtonBox.Cancel)

        if ok_button is not None:
            ok_button.setDisabled(is_loading)
        if cancel_button is not None:
            cancel_button.setDisabled(is_loading)

        self.pseudo_input.setDisabled(is_loading)
        self.email_input.setDisabled(is_loading)
        self.password_input.setDisabled(is_loading)
        self.confirm_password_input.setDisabled(is_loading)

        if is_loading:
            QGuiApplication.setOverrideCursor(Qt.WaitCursor)
        else:
            QGuiApplication.restoreOverrideCursor()

    def handle_register(self) -> None:
        pseudo = self.pseudo_input.text().strip()
        email = self.email_input.text().strip()
        password = self.password_input.text()
        confirm_password = self.confirm_password_input.text()

        if not pseudo or not email or not password or not confirm_password:
            QMessageBox.warning(self, "Champs manquants", "Tous les champs sont requis.")
            return

        if password != confirm_password:
            QMessageBox.warning(self, "Erreur", "Les mots de passe ne correspondent pas.")
            return

        self.set_loading_state(True)

        try:
            self.api.register_officer(pseudo, email, password)
        except APIClientError as e:
            QMessageBox.warning(
                self,
                "Erreur",
                f"Impossible de créer le compte.\n\n{e}",
            )
            return
        except Exception as e:
            QMessageBox.warning(
                self,
                "Erreur",
                f"Impossible de créer le compte.\n\n{e}",
            )
            return
        finally:
            self.set_loading_state(False)

        QMessageBox.information(self, "Compte créé", "Le compte officier a bien été créé.")
        self.accept()