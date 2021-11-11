import argparse
import ipaddress
import json
import logging
import os
import requests
import sys

from item_client.config import setup_logging

LOGGER = logging.getLogger(__name__)
"""
        self.app.router.add_get("/api/v1/test", self.test)
        self.app.router.add_get("/api/v1/account/{account_id}", self.get_account)
        self.app.router.add_get("/api/v1/accounts", self.get_accounts)
        self.app.router.add_get("/api/v1/accounts/{number}", self.get_accounts)
        self.app.router.add_post("/api/v1/accounts/add", self.add_contact)
        self.app.router.add_put("/api/v1/accounts/edit/{account_id}", self.edit_contact)
        self.app.router.add_delete("/api/v1/accounts/delete/{account_id}", self.delete_contact)
"""

URL_ACCOUNT = "{}/api/v1/account/{}"
URL_ACCOUNTS = "{}/api/v1/accounts/{}"
URL_ADD = "{}/api/v1/accounts/add"
URL_EDIT = "{}/api/v1/accounts/edit/{}"
URL_DELETE = "{}/api/v1/accounts/delete/{}"

class ItemClient():
    def __init__(self, ip, port):
        self.host = self._validate_ip(ip)
        self.port = self._validate_port(port)

    def _validate_ip(self, ip):
        try:
            ipaddress.ip_address(ip)
            return ip
        except ValueError:
            raise

    def _validate_port(self, port):
        if 1 <= port <= 65535:
            return port
        raise ValueError("Invalid port number")

    @property
    def url_prefix(self):
        return "http://{}:{}".format(self.host, self.port)

    def test(self):
        return requests.get("{}/api/v1/test".format(self.url_prefix))

    def get_account(self, account_id):
        return requests.get(f"{self.url_prefix}/api/v1/account/{account_id}")

    def get_accounts(self, n=0):
        return requests.get(f"{self.url_prefix}/api/v1/accounts/{n}")

    def add_account(self, account_info):
        return requests.post(f"{self.url_prefix}/api/v1/accounts/add", data=json.dumps(account_info))

    def edit_account(self, account_info):
        account_id = account_info.get("orgno")
        return requests.put(f"{self.url_prefix}/api/v1/accounts/edit/{account_id}", data=json.dumps(account_info))

    def delete_account(self, account_id):
        return requests.delete(f"{self.url_prefix}/api/v1/accounts/delete/{account_id}")

def main():
    parser = argparse.ArgumentParser(description="Item's Client")
    parser.add_argument("-v", "--verbose", action="store_true", help="increase log output verbosity")
    parser.add_argument('--ip', '-i', type=str, default="127.0.0.1", help="The Rest API server's ip address")
    parser.add_argument('--port', '-p', type=int, default=8080, help="The Rest API server's port")
    parser.add_argument('--log-file', '-l', type=str, help="Output logs to specified file")

    subparsers = parser.add_subparsers(title="command", dest="command", help="Command Type")

    parser_test = subparsers.add_parser("test", help="Simple test, useful for checking connection")

    parser_account = subparsers.add_parser("account", help="Given account id, get account info")
    parser_account.add_argument("--account-id", "-a", type=int, required=True, help="Account ID")

    parser_accounts = subparsers.add_parser("accounts", help="Get all accounts or get n accounts if n is provided, accounts will be in alphabetical order")
    parser_accounts.add_argument("--number", "-n", help="Number of accounts to retrieve")

    parser_add = subparsers.add_parser("add", help="Add an account")
    parser_add.add_argument("--data", "-d", type=str, help="Account information in json format")
    parser_add.add_argument("--file-path", "-f", type=str, help="Account information as json file")

    parser_edit = subparsers.add_parser("edit", help="Edit an account")
    parser_edit.add_argument("--data", "-d", help="Account information in json format")
    parser_edit.add_argument("--file-path", "-f", help="Account information as json file")

    parser_delete = subparsers.add_parser("delete", help="Given account id, delete account info")
    parser_delete.add_argument("--account-id", "-a", type=int, required=True, help="Account ID")

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

    if args.ip:
        try:
            ipaddress.ip_address(args.ip)
        except ValueError as e:
            LOGGER.error(f"Invalid IP address: {e}")
            sys.exit(1)
    if args.port:
        if not (1 <= args.port <= 65535):
            LOGGER.error(f"Invalid port: {args.port}")
            sys.exit(1)

    client = ItemClient(args.ip, args.port)
    if args.command == "test":
        LOGGER.info(client.test().text)
    elif args.command == "account":
        LOGGER.info(client.get_account(args.account_id).json())
    elif args.command == "accounts":
        if args.number:
            LOGGER.info(client.get_accounts(args.number).json())
        else:
            LOGGER.info(client.get_accounts().json())
    elif args.command == "add":
        if args.data:
            LOGGER.info(client.add_account(json.loads(args.data)).json())
        elif args.file_path:
            data = None
            with open(args.file_path) as json_file:
                data = json.load(json_file)
            LOGGER.info(client.add_account(data).json())
    elif args.command == "edit":
        if args.data:
            LOGGER.info(client.edit_account(json.loads(args.data)).text)
        elif args.file_path:
            data = None
            with open(args.file_path) as json_file:
                data = json.load(json_file)
            LOGGER.info(client.edit_account(data).json())
    elif args.command == "delete":
        LOGGER.info(client.delete_account(args.account_id).json())


if __name__ == "__main__":
    main()