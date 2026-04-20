import requests
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QColor, QBrush, QIcon, QPainter, QPen
from PySide6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
    QMenu,
    QMessageBox,
)

from ui.add_warning_dialog import AddWarningDialog
from utils import resource_path


class WarningTreeWidget(QTreeWidget):
    def paintEvent(self, event) -> None:
        super().paintEvent(event)

        painter = QPainter(self.viewport())
        pen = QPen(QColor("#000000"))
        pen.setWidth(1)
        painter.setPen(pen)

        for index in range(self.topLevelItemCount()):
            item = self.topLevelItem(index)
            if item.data(0, Qt.UserRole) != "player":
                continue

            next_index = index + 1
            if next_index >= self.topLevelItemCount():
                continue

            next_item = self.topLevelItem(next_index)
            if next_item.data(0, Qt.UserRole) != "separator":
                continue

            next_rect = self.visualItemRect(next_item)
            if not next_rect.isValid():
                continue

            y = next_rect.center().y()
            painter.drawLine(10, y, self.viewport().width() - 10, y)

        painter.end()


class MainWindow(QMainWindow):
    def __init__(self, officer: dict, api) -> None:
        super().__init__()

        self.officer = officer
        self.api = api

        self.setWindowTitle("OSIRIS - Avertissements")
        self.setWindowIcon(QIcon(resource_path("icon.ico")))
        self.resize(1120, 620)

        self.current_officer_name = self.officer["pseudo"]
        self.players = []

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Rechercher un joueur...")
        self.search_input.textChanged.connect(self.refresh_table)

        self.officer_label = QLabel("Connecté : {}".format(self.current_officer_name))

        self.add_warning_button = QPushButton("Ajouter un avertissement")
        self.add_warning_button.clicked.connect(self.open_add_warning_dialog)

        self.expand_all_button = QPushButton("Tout déplier")
        self.expand_all_button.clicked.connect(self.expand_all_players)

        self.collapse_all_button = QPushButton("Tout replier")
        self.collapse_all_button.clicked.connect(self.collapse_all_players)

        top_bar = QHBoxLayout()
        top_bar.addWidget(self.search_input)
        top_bar.addWidget(self.officer_label)
        top_bar.addWidget(self.add_warning_button)
        top_bar.addWidget(self.expand_all_button)
        top_bar.addWidget(self.collapse_all_button)

        self.tree = WarningTreeWidget()
        self.tree.setColumnCount(4)
        self.tree.setHeaderLabels(["Pseudo", "Raison", "Date", "Officier"])
        self.tree.setRootIsDecorated(True)
        self.tree.setAlternatingRowColors(False)
        self.tree.setIndentation(20)
        self.tree.setUniformRowHeights(True)
        self.tree.setItemsExpandable(True)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.open_context_menu)

        header = self.tree.header()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.Interactive)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Interactive)

        self.tree.setColumnWidth(0, 180)
        self.tree.setColumnWidth(3, 110)

        central_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.addLayout(top_bar)
        main_layout.addWidget(self.tree)
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        self.apply_dark_style()
        self.load_data()
        self.refresh_table()

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

            QLineEdit, QTextEdit, QTreeWidget {
                background-color: #2a2a2a;
                border: 1px solid #444;
                border-radius: 6px;
                padding: 6px;
            }

            QPushButton {
                background-color: #3a3a3a;
                border: 1px solid #555;
                border-radius: 6px;
                padding: 8px 12px;
            }

            QPushButton:hover {
                background-color: #4a4a4a;
            }

            QHeaderView::section {
                background-color: #333;
                color: #fff;
                padding: 6px;
                border: 1px solid #444;
            }

            QTreeWidget {
                outline: none;
                background-color: #252525;
                alternate-background-color: #252525;
            }

            QTreeWidget::item {
                background-color: #252525;
                color: #f0f0f0;
                border: none;
                padding-top: 6px;
                padding-bottom: 6px;
                padding-left: 6px;
            }

            QTreeWidget::item:selected {
                background-color: #3d6ea8;
                color: #ffffff;
            }

            QMenu {
                background-color: #2a2a2a;
                color: #f0f0f0;
                border: 1px solid #444;
            }

            QMenu::item:selected {
                background-color: #3d6ea8;
            }
        """)

    def load_data(self) -> None:
        try:
            players_from_api = self.api.get_players_with_warnings()
            self.players = players_from_api

        except Exception as e:
            QMessageBox.critical(
                self,
                "Erreur API",
                f"Impossible de charger les données depuis le serveur.\n\n{e}",
            )
            self.players = []

    def style_item(self, item: QTreeWidgetItem) -> None:
        for col in range(self.tree.columnCount()):
            item.setBackground(col, QBrush(QColor("#252525")))
            item.setForeground(col, QBrush(QColor("#f0f0f0")))

        item.setTextAlignment(2, Qt.AlignRight | Qt.AlignVCenter)
        item.setTextAlignment(3, Qt.AlignRight | Qt.AlignVCenter)

    def create_player_item(self, pseudo: str, warning: dict) -> QTreeWidgetItem:
        item = QTreeWidgetItem([
            pseudo,
            warning["reason"],
            warning["date"],
            warning["officer"],
        ])
        self.style_item(item)
        item.setData(0, Qt.UserRole, "player")
        item.setData(0, Qt.UserRole + 1, warning["id"])
        item.setData(0, Qt.UserRole + 2, pseudo)
        item.setData(0, Qt.UserRole + 3, warning["reason"])
        item.setData(0, Qt.UserRole + 4, warning["date"])
        return item

    def create_child_warning_item(self, pseudo: str, warning: dict) -> QTreeWidgetItem:
        item = QTreeWidgetItem([
            "",
            warning["reason"],
            warning["date"],
            warning["officer"],
        ])
        self.style_item(item)
        item.setData(0, Qt.UserRole, "warning")
        item.setData(0, Qt.UserRole + 1, warning["id"])
        item.setData(0, Qt.UserRole + 2, pseudo)
        item.setData(0, Qt.UserRole + 3, warning["reason"])
        item.setData(0, Qt.UserRole + 4, warning["date"])
        return item

    def create_separator_item(self) -> QTreeWidgetItem:
        item = QTreeWidgetItem(["", "", "", ""])
        for col in range(self.tree.columnCount()):
            item.setBackground(col, QBrush(QColor("#252525")))
            item.setForeground(col, QBrush(QColor("#252525")))
        item.setFlags(Qt.NoItemFlags)
        item.setData(0, Qt.UserRole, "separator")
        return item

    def refresh_table(self) -> None:
        filter_text = self.search_input.text().strip().lower()
        self.tree.clear()

        visible_players = []
        for player in self.players:
            pseudo = player["pseudo"]
            if filter_text and filter_text not in pseudo.lower():
                continue
            visible_players.append(player)

        for player_index, player in enumerate(visible_players):
            pseudo = player["pseudo"]
            warnings = player.get("warnings", [])

            if warnings:
                parent_item = self.create_player_item(pseudo, warnings[0])
            else:
                parent_item = QTreeWidgetItem([pseudo, "", "", ""])
                self.style_item(parent_item)
                parent_item.setData(0, Qt.UserRole, "player")
                parent_item.setData(0, Qt.UserRole + 1, None)
                parent_item.setData(0, Qt.UserRole + 2, pseudo)
                parent_item.setData(0, Qt.UserRole + 3, "")
                parent_item.setData(0, Qt.UserRole + 4, "")

            self.tree.addTopLevelItem(parent_item)

            for warning in warnings[1:]:
                child_item = self.create_child_warning_item(pseudo, warning)
                parent_item.addChild(child_item)

            parent_item.setExpanded(False)

            if player_index < len(visible_players) - 1:
                self.tree.addTopLevelItem(self.create_separator_item())

        self.tree.viewport().update()

    def find_player_by_pseudo(self, pseudo: str):
        for player in self.players:
            if player["pseudo"].lower() == pseudo.lower():
                return player
        return None

    def open_add_warning_dialog(self) -> None:
        dialog = AddWarningDialog(self.current_officer_name, self)
        if dialog.exec() and dialog.warning_data:
            try:
                pseudo = dialog.warning_data["pseudo"].strip()
                reason = dialog.warning_data["reason"]
                date = dialog.warning_data["date"]

                player = self.find_player_by_pseudo(pseudo)
                if player is None:
                    player = self.api.create_player(pseudo)

                self.api.create_warning(
                    player_id=player["id"],
                    reason=reason,
                    date=date,
                )

                self.load_data()
                self.refresh_table()

            except requests.HTTPError as e:
                detail = None
                try:
                    detail = e.response.json().get("detail")
                except Exception:
                    pass

                QMessageBox.critical(
                    self,
                    "Erreur API",
                    f"Impossible d'ajouter l'avertissement.\n\n{detail or str(e)}",
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Erreur API",
                    f"Impossible d'ajouter l'avertissement.\n\n{e}",
                )

    def open_edit_warning_dialog(
        self,
        warning_id: int,
        pseudo: str,
        reason: str,
        date: str,
    ) -> None:
        dialog = AddWarningDialog(
            self.current_officer_name,
            self,
            pseudo=pseudo,
            reason=reason,
            edit_mode=True,
        )
        if dialog.exec() and dialog.warning_data:
            try:
                self.api.update_warning(
                    warning_id,
                    dialog.warning_data["reason"],
                    dialog.warning_data["date"],
                )
                self.load_data()
                self.refresh_table()

            except requests.HTTPError as e:
                detail = None
                try:
                    detail = e.response.json().get("detail")
                except Exception:
                    pass

                QMessageBox.critical(
                    self,
                    "Erreur API",
                    f"Impossible de modifier l'avertissement.\n\n{detail or str(e)}",
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Erreur API",
                    f"Impossible de modifier l'avertissement.\n\n{e}",
                )

    def open_context_menu(self, position) -> None:
        item = self.tree.itemAt(position)
        if item is None:
            return

        item_type = item.data(0, Qt.UserRole)
        if item_type not in ("player", "warning"):
            return

        warning_id = item.data(0, Qt.UserRole + 1)
        pseudo = item.data(0, Qt.UserRole + 2)
        reason = item.data(0, Qt.UserRole + 3)
        date = item.data(0, Qt.UserRole + 4)

        if warning_id is None:
            return

        menu = QMenu(self)

        edit_action = QAction("Modifier l'avertissement", self)
        edit_action.triggered.connect(
            lambda: self.open_edit_warning_dialog(warning_id, pseudo, reason, date)
        )
        menu.addAction(edit_action)

        delete_action = QAction("Supprimer l'avertissement", self)
        delete_action.triggered.connect(lambda: self.confirm_delete_warning(warning_id))
        menu.addAction(delete_action)

        menu.exec(self.tree.viewport().mapToGlobal(position))

    def confirm_delete_warning(self, warning_id: int) -> None:
        reply = QMessageBox.question(
            self,
            "Confirmation",
            "Supprimer cet avertissement ?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply != QMessageBox.Yes:
            return

        try:
            self.api.delete_warning(warning_id)
            self.load_data()
            self.refresh_table()

        except requests.HTTPError as e:
            detail = None
            try:
                detail = e.response.json().get("detail")
            except Exception:
                pass

            QMessageBox.critical(
                self,
                "Erreur API",
                f"Impossible de supprimer l'avertissement.\n\n{detail or str(e)}",
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Erreur API",
                f"Impossible de supprimer l'avertissement.\n\n{e}",
            )

    def expand_all_players(self) -> None:
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            if item.data(0, Qt.UserRole) == "player":
                item.setExpanded(True)
        self.tree.viewport().update()

    def collapse_all_players(self) -> None:
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            if item.data(0, Qt.UserRole) == "player":
                item.setExpanded(False)
        self.tree.viewport().update()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self.tree.viewport().update()