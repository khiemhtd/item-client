import argparse
import json
import logging
import os
import sys

from requests.exceptions import ConnectionError

from PySide6 import QtCore
from PySide6.QtWidgets import QApplication, QDialog, QFrame, QGridLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget

from item_client.client import ItemClient
from item_client.config import setup_logging
from item_client.views import AccountFormView
from item_client.constants import *

LOGGER = logging.getLogger(__name__)


def generate_dialog(text: str, success=False):
    dialog = QDialog()
    dialog.setWindowTitle("Success" if success else "FATAL ERROR!")
    dialog.setMinimumWidth(300)
    dialog.setMinimumHeight(100)
    layout = QVBoxLayout()
    layout.setAlignment(QtCore.Qt.AlignCenter)
    layout.addWidget(QLabel(text))
    dialog.setLayout(layout)
    return dialog


def validate_account(account_data: dict):
    """
    Ensures all proper fields exist and they're of the correct type
    """
    for field in ACCOUNT_FIELDS:
        # Check field is present
        if field not in account_data:
            LOGGER.error(f"Field {field} not in account")
            return False

        # Check for type
        if field == FIELD_ORGNO:
            if not isinstance(account_data.get(field), int):
                LOGGER.error(f"Field {field} is not an int")
                return False
        elif not isinstance(account_data.get(field), str):
            LOGGER.error(f"Field {field} is not a str")
            return False
    return True


class Account:
    """
    Class holding both account data and account related widgets
    """
    def __init__(self, account_data: dict, client: ItemClient):
        self.account_data = account_data
        self.btn_name = QPushButton(self.account_data.get(FIELD_NAME))
        self.btn_orgno = QPushButton(str(self.account_data.get(FIELD_ORGNO)))
        self.client = client
        self.btn_name.clicked.connect(lambda : self.handle_edit(self.account_data))
        self.btn_orgno.clicked.connect(lambda : self.handle_edit(self.account_data))

    @property
    def name(self):
        return self.account_data.get(FIELD_NAME)

    @property
    def orgno(self):
        return self.account_data.get(FIELD_ORGNO)

    def get_view_name(self):
        return self.btn_name

    def get_view_orgno(self):
        return self.btn_orgno

    def update_account(self, account_data):
        LOGGER.debug(f"Updating account: {self.orgno}")
        self.account_data.update(account_data)
        self.btn_name.setText(self.name)

    def handle_edit(self, account):
        form = AccountFormView("EDIT ACCOUNT", account)
        res = form.exec()
        if res[0]:
            account = res[1]
            if validate_account(account):
                try:
                    LOGGER.info(f"Editing account: {account.get(FIELD_ORGNO)}")
                    resp = self.client.edit_account(account)
    
                    LOGGER.debug(f"Response: {resp}")
                    if resp.result:
                        account_data = self.client.get_account(self.orgno).data
                        self.update_account(account_data)
                        dialog = generate_dialog(resp.message, True)
                        dialog.exec()
                    else:
                        dialog = generate_dialog(resp.message)
                        dialog.exec()
                    return
                except ConnectionError as e:
                    dialog = generate_dialog(f"Could not connect to server {self.client.host}")
                    dialog.exec()
                except Exception as e:
                    dialog = generate_dialog(f"Unknown error")
                    LOGGER.error(f"Unknown error: {e}")
                    dialog.exec()
            else:
                dialog = generate_dialog(f"Invalid account information, please check fields and try again")
                dialog.exec()
        else:
            LOGGER.info(f"Cancel edit: {account.get(FIELD_ORGNO)}")


class MainView(QWidget):
    MIN_WIDTH = 360
    MIN_HEIGHT = 640
    COL_LEFT = 0
    COL_RIGHT = 1

    def __init__(self, host, port):
        super().__init__()
        self.client = ItemClient(host, port)
        self.accounts = {}

        # Set layout properties
        self.grid_row = 0
        self.setMinimumWidth(self.MIN_WIDTH)
        self.setMinimumHeight(self.MIN_HEIGHT)

        # Create the Grid layout
        self._generate_layout()

        # Set up scrolling
        self._scroll_area = QScrollArea()
        self._scroll_area.setWindowTitle("ITEM ACCOUNT MANAGEMENT")
        self._scroll_area.setWidget(self)
        self._scroll_area.setMinimumWidth(self.MIN_WIDTH + self._scroll_area.horizontalScrollBar().size().height())
        self._scroll_area.setMinimumHeight(self.MIN_HEIGHT + self._scroll_area.verticalScrollBar().size().width())
        self._scroll_area.setVisible(True)

        # Populate accounts
        self._populate_accounts()

    def _generate_layout(self):
        self.layout = QGridLayout()
        self.layout.setAlignment(QtCore.Qt.AlignTop)

        # Add an ADD button
        row = self.row
        btn_add = QPushButton("ADD")
        btn_add.clicked.connect(self.handle_add)
        self.layout.addWidget(btn_add, row, self.COL_LEFT, 1, 2)

        # Add an UPDATE button
        row = self.row
        btn_upd = QPushButton("UPDATE")
        btn_upd.clicked.connect(self.update_accounts)
        self.layout.addWidget(btn_upd, row, self.COL_LEFT, 1 , 2)

        # Add a DIVIDER
        row = self.row
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setFrameShadow(QFrame.Sunken)
        self.layout.addWidget(divider, row, self.COL_LEFT, 1, 2)

        # Add title
        row = self.row
        self.layout.addWidget(QLabel(FIELD_NAME.upper()), row, self.COL_LEFT)
        self.layout.addWidget(QLabel(FIELD_ORGNO.upper()), row, self.COL_RIGHT)

        # Set layout
        self.setLayout(self.layout)
        return self.layout

    def _populate_accounts(self):
        try:
            res = self.client.get_accounts()
            accounts_data = res.data if res.result else []
            self.add_accounts(accounts_data)
        except ConnectionError as e:
	        dialog = generate_dialog(f"Could not connect to server {self.client.host}")
	        dialog.exec()
        except Exception as e:
            dialog = generate_dialog(f"Unknown error")
            LOGGER.error(f"Unknown error: {e}")
            dialog.exec()

    @property
    def row(self):
        row = self.grid_row
        self.grid_row += 1
        return row

    def add_account(self, account_data: dict):
        """
        Add a user
        :param dict account: Account as 
        """
        if not validate_account(account_data):
            LOGGER.error(f"Invalid account {account_data}")
            return False

        # Create account and store
        account = Account(account_data, self.client)
        LOGGER.debug(f"Adding account: {account.orgno}")
        self.accounts[account.orgno] = account

        # Set account views
        row = self.row
        self.layout.addWidget(account.get_view_name(), row, self.COL_LEFT)
        self.layout.addWidget(account.get_view_orgno(), row, self.COL_RIGHT)

    def add_accounts(self, accounts_data):
        for account_data in accounts_data:
            self.add_account(account_data)

    def update_accounts(self):
        try:
            LOGGER.info("Updating accounts")
            res = self.client.get_accounts()
            accounts_data = res.data if res.result else []
            for account_data in accounts_data:
                if validate_account(account_data):
                    orgno = account_data.get(FIELD_ORGNO)
                    if orgno in self.accounts:
                        self.accounts[orgno].update_account(account_data)
                    else:
                        self.add_account(account_data)
                else:
                    LOGGER.warning(f"Could not update account {account_data}")
            LOGGER.info("Updated")
        except ConnectionError as e:
            dialog = generate_dialog(f"Could not connect to server {self.client.host}")
            dialog.exec()
        except Exception as e:
            dialog = generate_dialog(f"Unknown error")
            LOGGER.error(f"Unknown error: {e}")
            dialog.exec()

    def handle_add(self):
        try:
            form = AccountFormView("ADD ACCOUNT")
            res = form.exec()
            LOGGER.info(f"res[0]: {res[0]}")
            if res[0]:
                account = res[1]
                if validate_account(res[1]):
                    LOGGER.info(f"Adding account: {account.get(FIELD_ORGNO)}")
                    self.client.add_account(account)
                    self.update_accounts()
                    return
                else:
                    dialog = generate_dialog(f"Invalid account information, please check fields and try again")
                    dialog.exec()
                    return
            else:
                if "error" in res[1]:
                    LOGGER.error(res[1].get("error"))
                    dialog = generate_dialog(res[1].get("error"))
                    dialog.exec()
                else:
                    LOGGER.info("Cancel adding of account")
                return
        except ConnectionError as e:
            dialog = generate_dialog(f"Could not connect to server {self.client.host}")
            dialog.exec()
        except Exception as e:
            dialog = generate_dialog(f"Unknown error")
            LOGGER.error(f"Unknown error: {e}")
            dialog.exec()


def main():
    parser = argparse.ArgumentParser(description="Item's Client")
    parser.add_argument("-v", "--verbose", action="store_true", help="increase log output verbosity")
    parser.add_argument('--ip', '-i', type=str, default="127.0.0.1", help="The Rest API server's ip address")
    parser.add_argument('--port', '-p', type=int, default=8080, help="The Rest API server's port")
    parser.add_argument('--log-file', '-l', type=str, help="Output logs to specified file")
    args = parser.parse_args()

    # Sanitize arguments
    log_level = logging.INFO
    if args.verbose:
        log_level = logging.DEBUG

    if args.log_file:
        # Check if path is valid
        dir_path = os.path.dirname(os.path.abspath(args.log_file))
        if dir_path:
            setup_logging(args.log_file, log_level)
    else:
        setup_logging(level=log_level)

    setup_logging(level=logging.DEBUG)
    app = QApplication(sys.argv)
    try:
        main_view = MainView(args.ip, args.port)
        main_view.show()
    except Exception as e:
        LOGGER.error(f"Could not launch app: {e}")
        dialog = generate_dialog("Could not launch app")
        dialog.exec()
        sys.exit()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
