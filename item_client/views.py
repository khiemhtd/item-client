import logging
import sys
from PySide6.QtCore import Qt

from PySide6.QtWidgets import QApplication, QDialog, QDialogButtonBox, QLineEdit, QPushButton, QVBoxLayout
from item_client.client import ItemClient

from item_client.config import setup_logging
from item_client.constants import *

LOGGER = logging.getLogger(__name__)

class AccountFormView(QDialog):
    """
    Displays a form for user to fill in account information.
    """
    def __init__(self, text, account={}):
        super().__init__()
        self.setWindowTitle(text)
        self.layout = QVBoxLayout()

        # Add input fields for account
        self.q_name = QLineEdit(account.get(FIELD_NAME, FIELD_NAME.upper()))
        self.q_orgno = QLineEdit(str(account.get(FIELD_ORGNO, FIELD_ORGNO.upper())))
        self.q_leader_title = QLineEdit(account.get(FIELD_LEADER_TITLE, FIELD_LEADER_TITLE.upper().replace("_", " ")))
        self.q_leader_name = QLineEdit(account.get(FIELD_LEADER_NAME, FIELD_LEADER_NAME.upper().replace("_", " ")))
        self.q_type = QLineEdit(account.get(FIELD_TYPE, FIELD_TYPE.upper()))

        # Add accept/reject buttons
        self.btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.btns.accepted.connect(self.accept)
        self.btns.rejected.connect(self.reject)

        # Add all widgets to layout and set the layout for showing
        self.layout.addWidget(self.q_name)
        self.layout.addWidget(self.q_orgno)
        self.layout.addWidget(self.q_leader_title)
        self.layout.addWidget(self.q_leader_name)
        self.layout.addWidget(self.q_type)
        self.layout.addWidget(self.btns)
        self.setLayout(self.layout)

    def exec(self):
        res = super().exec()
        if not res:
            return (0, {})

        account = {}
        try:
            account[FIELD_ORGNO] = int(self.q_orgno.text())
        except ValueError:
            LOGGER.error(f"Invalid orgno passed: {self.q_orgno.text()}")
            return (0, {"error" : f"Invalid orgno passed: {self.q_orgno.text()}"})
        account[FIELD_NAME] = self.q_name.text()
        account[FIELD_LEADER_TITLE] = self.q_leader_title.text()
        account[FIELD_LEADER_NAME] = self.q_leader_name.text()
        account[FIELD_TYPE] = self.q_type.text()
        return (res, account)

# For testing purposes
def main():
    setup_logging()
    app = QApplication(sys.argv)
    form_add = AccountFormView("EDIT ACCOUNT")
    res = form_add.exec()
    if res[0]:
        LOGGER.info(f"Account: {res[1]}")
    else:
        LOGGER.info("Cancelled")
    sys.exit()

if __name__ == "__main__":
    main()
