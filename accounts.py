from sqlite3 import connect
from enum import IntEnum
from bcrypt import hashpw, gensalt, checkpw
from os import environ
from uuid import uuid4
from base64 import b64encode, b64decode
from typing import Union
from fastapi.exceptions import HTTPException
from fastapi.params import Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials


security = HTTPBasic()


class AccessLevel(IntEnum):
    READ_ONLY = 0
    """This user only has access to the dashboard, and cannot do anything with said access."""

    MODERATOR = 1
    """This user can reload cogs and other non-destructive actions."""

    ADMINISTRATOR = 2
    """This user can reboot the bot, but cannot do any modifications."""

    DEVELOPER = 3
    """This user has full control."""


class Account:
    def __init__(self, uuid: str, username: str, password: str, access_level: int) -> None:
        self.uuid = uuid
        self.username = username
        self.password = password
        self.access_level = AccessLevel(access_level)
    
    @classmethod
    def create(cls, username: str, password: str, access_level: AccessLevel):
        assert cls.get(username) is None, "Account already exists."
        pw = hashpw(password.encode(), gensalt()).decode()
        uuid = str(uuid4())

        db.execute(
            """
            INSERT INTO accounts (uuid, username, password, access_level)
            VALUES (?, ?, ?, ?);
            """,
            (uuid, username, pw, access_level.value)
        )
        db.commit()

        return cls(uuid, username, password, access_level)
    
    @classmethod
    def get(cls, username: str):
        cursor = db.execute("SELECT uuid, username, password, access_level FROM accounts WHERE username=?", (username,))
        row = cursor.fetchone()
        if row:
            return cls(*row)
    
    def edit(self, *, username: str = None, password: str = None, access_level: AccessLevel = ...):
        if username is not ... and environ["ALLOW_USERNAME_CHANGES"].lower() == "false":
            raise PermissionError(403, "Username changes are disabled.")
        if password is not ... and environ["ALLOW_PASSWORD_CHANGES"].lower() == "false":
            raise PermissionError(403, "Password changes are disabled.")
        elif password:
            password = hashpw(password, gensalt()).decode()
        
        db.execute(
            """
            UPDATE accounts
            SET username=?, password=?, access_level=?
            WHERE uuid=?;
            """,
            (username or self.username, password or self.password, (access_level or self.access_level).value)
        )
        db.commit()
    
    def delete(self):
        db.execute(
            """
            DELETE FROM accounts WHERE uuid=?;
            """,
            (self.uuid,)
        )
        db.commit()
    
    def authenticate(self, *, username: str = ..., password: str) -> bool:
        if username is not ...:
            if username != self.username:
                return False
        return checkpw(password.encode(), self.password.encode())


db = connect("./main.db", check_same_thread=False)
db.execute(
    """
    CREATE TABLE IF NOT EXISTS accounts (
        uuid TEXT NOT NULL UNIQUE PRIMARY KEY,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        access_level INTEGER NOT NULL DEFAULT 1
    );
    """
)
try:
    Account.create(environ["ADMIN_USERNAME"], environ["ADMIN_PASSWORD"], AccessLevel.DEVELOPER)
except AssertionError:
    pass  # already exists.

def login(realm: str = None, access_level: AccessLevel = AccessLevel.READ_ONLY):
    def call(c: HTTPBasicCredentials = Depends(security)):
        target = Account.get(c.username)
        if not target:
            raise HTTPException(
                401,
                "Invalid Account Name",
                {
                    "WWW-Authenticate": "Basic realm=\"{!s}\"".format(realm)
                }
            )
        authorised = target.authenticate(password=c.password)
        if not authorised:
            raise HTTPException(
                401,
                "Invalid Account Password",
                {
                    "WWW-Authenticate": "Basic realm=\"{!s}\"".format(realm)
                }
            )
        if target.access_level.value < access_level.value:
            raise HTTPException(
                403,
                "Invalid access level. You need {!s} or above.".format(access_level.value)
            )
        return target
    return call
