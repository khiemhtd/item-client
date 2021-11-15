import logging
import sys

from PySide6 import QtCore
from PySide6.QtWidgets import QApplication, QDialog, QFrame, QGridLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget

from item_client.client import ItemClient
from item_client.config import setup_logging

MIN_WIDTH = 360
MIN_HEIGHT = 640

# Could (should?) be imported from item-restapi, perhaps have a common library to pull from
FIELD_NAME = "name"
FIELD_ORGNO = "orgno"
FIELD_LEADER_TITLE = "leader_title"
FIELD_LEADER_NAME = "leader_name"
FIELD_TYPE = "type"
ACCOUNT_FIELDS = [FIELD_NAME, FIELD_ORGNO, FIELD_LEADER_TITLE, FIELD_LEADER_NAME, FIELD_TYPE]

LOGGER = logging.getLogger(__name__)

class AccountListView(QWidget):
    COL_LEFT = 0
    COL_RIGHT = 1

    def __init__(self, host, port):
        super().__init__()
        self.client = ItemClient(host, port)

        # Set layout properties
        self.grid_row = 0
        self.setMinimumWidth(MIN_WIDTH)
        self.setMinimumHeight(MIN_HEIGHT)
        self.layout = QGridLayout()
        self.layout.setAlignment(QtCore.Qt.AlignTop)
        self.setLayout(self.layout)

        # Add widgets
        row = self.row
        self.layout.addWidget(QPushButton("ADD"), row, self.COL_LEFT, 1, 2)
        row = self.row
        self.layout.addWidget(QPushButton("REFRESH"), row, self.COL_LEFT, 1 , 2)
        row = self.row
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setFrameShadow(QFrame.Sunken)
        self.layout.addWidget(divider, row, self.COL_LEFT, 1, 2)
        row = self.row
        self.layout.addWidget(QLabel(FIELD_NAME.upper()), row, self.COL_LEFT)
        self.layout.addWidget(QLabel(FIELD_ORGNO.upper()), row, self.COL_RIGHT)

        # Set up scrolling
        self._scroll_area = QScrollArea()
        self._scroll_area.setWidget(self)
        self._scroll_area.setMinimumWidth(MIN_WIDTH + self._scroll_area.horizontalScrollBar().size().height())
        self._scroll_area.setMinimumHeight(MIN_HEIGHT + self._scroll_area.verticalScrollBar().size().width())
        self._scroll_area.setVisible(True)

    def _validate_account(self, account):
        for field in ACCOUNT_FIELDS:
            # Check field is present
            if field not in account:
                LOGGER.error(f"Field {field} not in account")
                return False

            # Check for type
            if field == FIELD_ORGNO:
                if not isinstance(account.get(field), int):
                    LOGGER.error(f"Field {field} is not an int")
                    return False
            elif not isinstance(account.get(field), str):
                LOGGER.error(f"Field {field} is not a str")
                return False
        return True

    @property
    def row(self):
        row = self.grid_row
        self.grid_row += 1
        return row

    def add_user(self, account):
        """
        Add a user
        :param dict account: Account as 
        """
        if not self._validate_account(account):
            LOGGER.error("Invalid account")
            return False

        row = self.row
        btn_name = QPushButton(account.get(FIELD_NAME))
        btn_orgno = QPushButton(str(account.get(FIELD_ORGNO)))
        self.layout.addWidget(btn_name, row, self.COL_LEFT)
        self.layout.addWidget(btn_orgno, row, self.COL_RIGHT)

    def add_users(self, accounts):
        for account in accounts:
            self.add_user(account)

def get_error_dialog(text):
    dialog = QDialog()
    dialog.setWindowTitle("FATAL ERROR")
    dialog.setMinimumWidth(100)
    dialog.setMinimumHeight(50)
    layout = QVBoxLayout()
    layout.setAlignment(QtCore.Qt.AlignCenter)
    layout.addWidget(QLabel(text))
    dialog.setLayout(layout)
    return dialog


def main():
    setup_logging()
    app = QApplication(sys.argv)
    try:
        main_view = AccountListView("127.0.0.1", 8080)
        main_view.add_user({FIELD_NAME : "AAA", FIELD_ORGNO : 510, FIELD_LEADER_TITLE : "Manager", FIELD_LEADER_NAME : "Somename", FIELD_TYPE :"Technology"})
        main_view.show()
    except Exception as e:
        LOGGER.error(f"Could not launch app: {e}")
        dialog = get_error_dialog("Could not launch app")
        dialog.exec()
        sys.exit()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
