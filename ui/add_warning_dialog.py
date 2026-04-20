from datetime import datetime

try:
    from zoneinfo import ZoneInfo
except ImportError:
    try:
        from backports.zoneinfo import ZoneInfo
    except ImportError:
        ZoneInfo = None

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QTextEdit,
    QVBoxLayout,
)

from utils import resource_path


class AddWarningDialog(QDialog):
    def __init__(
        self,
        officer_name: str,
        parent=None,
        pseudo: str = "",
        reason: str = "",
        edit_mode: bool = False,
    ) -> None:
        super().__init__(parent)
        self.officer_name = officer_name
        self.edit_mode = edit_mode
        self.warning_data = None

        self.setWindowTitle("OSIRIS - Avertissements")
        self.setWindowIcon(QIcon(resource_path("icon.ico")))
        self.setMinimumWidth(420)

        self.player_input = QLineEdit()
        self.player_input.setPlaceholderText("Pseudo du joueur")
        self.player_input.setText(pseudo)
        if edit_mode:
            self.player_input.setReadOnly(True)

        self.reason_input = QTextEdit()
        self.reason_input.setPlaceholderText("Raison de l'avertissement")
        self.reason_input.setMinimumHeight(100)
        self.reason_input.setPlainText(reason)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal,
            self,
        )
        self.buttons.accepted.connect(self.validate_and_accept)
        self.buttons.rejected.connect(self.reject)

        form = QFormLayout()
        form.addRow("Pseudo :", self.player_input)
        form.addRow("Raison :", self.reason_input)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addWidget(self.buttons)

        self.setLayout(layout)

    def get_paris_now(self) -> datetime:
        if ZoneInfo is not None:
            try:
                return datetime.now(ZoneInfo("Europe/Paris"))
            except Exception:
                pass
        return datetime.now()

    def validate_and_accept(self) -> None:
        pseudo = self.player_input.text().strip()
        reason = self.reason_input.toPlainText().strip()

        if not pseudo:
            QMessageBox.warning(self, "Champ manquant", "Le pseudo du joueur est requis.")
            return

        if not reason:
            QMessageBox.warning(self, "Champ manquant", "La raison est requise.")
            return

        paris_now = self.get_paris_now()

        self.warning_data = {
            "pseudo": pseudo,
            "reason": reason,
            "date": paris_now.strftime("%Y-%m-%d %H:%M:%S"),
            "officer": self.officer_name,
        }
        self.accept()