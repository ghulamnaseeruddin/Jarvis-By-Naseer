"""
dashboard/auth.py — accounts for the remote dashboard (email + password, Google).

Design
------
The dashboard lets a phone control this computer, so an account here is a key to
the machine. Two rules follow from that:

1. Creating an account needs the DEVICE CODE that the desktop app shows under
   "Remote Control". Somebody on the same Wi-Fi cannot register themselves —
   they would have to be looking at the computer. It is the same idea as
   linking a TV app: prove you are in front of the device once, then sign in
   normally from then on (no code needed).
2. Passwords are stored as salted scrypt hashes (standard library, no new
   dependency). Google accounts are verified server-side against Google's
   public keys; the page never gets to just claim "I am alice@gmail.com".

This module knows nothing about FastAPI. Every method takes plain dicts and
returns ``(http_status, payload_dict)`` so it can be tested without a server.
The server turns a successful result into a session (see DashboardServer).

Storage: config/accounts.json (git-ignored), written atomically.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import threading
import time
from pathlib import Path
from typing import Callable

# ── tunables ──────────────────────────────────────────────────────────────────

_SCRYPT_N, _SCRYPT_R, _SCRYPT_P = 2 ** 14, 8, 1     # ~16 MB, ~50 ms per hash
_MIN_PW, _MAX_PW = 8, 128
_MAX_NAME        = 60

_FAIL_WINDOW     = 300      # seconds an attempt is remembered
_FAIL_LIMIT_ID   = 6        # wrong tries per (ip, email) inside the window
_FAIL_LIMIT_IP   = 25       # wrong tries per ip in the window, any email/code

_EMAIL_RE = re.compile(r"^[^@\s]{1,64}@[^@\s]{1,190}\.[^@\s.]{2,}$")

_COMMON_PASSWORDS = frozenset({
    "password", "password1", "12345678", "123456789", "1234567890",
    "qwertyui", "qwerty123", "iloveyou", "admin123", "letmein12",
    "11111111", "00000000", "abc12345", "jarvis123", "welcome1",
})

# A real hash of a random value, used to burn the same time when the account
# does not exist — so response time does not reveal which emails are registered.
_DUMMY_HASH: str | None = None


# ── password hashing ──────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.scrypt(password.encode("utf-8"), salt=salt,
                        n=_SCRYPT_N, r=_SCRYPT_R, p=_SCRYPT_P, dklen=32)
    return "scrypt${}${}${}${}${}".format(
        _SCRYPT_N, _SCRYPT_R, _SCRYPT_P,
        base64.b64encode(salt).decode(), base64.b64encode(dk).decode())


def verify_password(password: str, stored: str | None) -> bool:
    """Constant-time check. Always spends the hashing time, even with no hash."""
    global _DUMMY_HASH
    if not stored:
        if _DUMMY_HASH is None:
            _DUMMY_HASH = hash_password(secrets.token_urlsafe(12))
        stored = _DUMMY_HASH
        password_ok_possible = False
    else:
        password_ok_possible = True
    try:
        scheme, n, r, p, salt_b64, dk_b64 = stored.split("$")
        if scheme != "scrypt":
            return False
        salt, want = base64.b64decode(salt_b64), base64.b64decode(dk_b64)
        got = hashlib.scrypt(password.encode("utf-8"), salt=salt,
                             n=int(n), r=int(r), p=int(p), dklen=len(want))
        return hmac.compare_digest(got, want) and password_ok_possible
    except Exception:
        return False


# ── account store ─────────────────────────────────────────────────────────────

class AccountStore:
    """Tiny JSON-file user table, keyed by lower-cased email."""

    def __init__(self, path: Path):
        self._path = Path(path)
        self._lock = threading.RLock()
        self._users: dict[str, dict] | None = None      # lazy — no I/O at import

    def _load(self) -> dict[str, dict]:
        if self._users is not None:
            return self._users
        users: dict[str, dict] = {}
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
            if isinstance(raw, dict) and isinstance(raw.get("users"), dict):
                users = raw["users"]
        except FileNotFoundError:
            pass
        except Exception:
            # Unreadable file: keep it for inspection instead of overwriting it.
            try:
                self._path.replace(self._path.with_suffix(
                    f".corrupt-{int(time.time())}.json"))
                print("[Auth] accounts.json was unreadable — moved aside, starting fresh.")
            except Exception:
                pass
        self._users = users
        return users

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._path.with_suffix(".tmp")
        tmp.write_text(json.dumps({"users": self._users}, indent=2), encoding="utf-8")
        try:
            os.chmod(tmp, 0o600)          # best effort — largely a no-op on Windows
        except Exception:
            pass
        os.replace(tmp, self._path)

    def count(self) -> int:
        with self._lock:
            return len(self._load())

    def by_email(self, email: str) -> dict | None:
        with self._lock:
            return self._load().get(email.lower())

    def by_google_sub(self, sub: str) -> dict | None:
        with self._lock:
            for u in self._load().values():
                if u.get("google_sub") and u["google_sub"] == sub:
                    return u
        return None

    def create(self, user: dict) -> bool:
        """False when the email is already taken."""
        with self._lock:
            users = self._load()
            key = user["email"].lower()
            if key in users:
                return False
            users[key] = user
            self._save()
            return True

    def update(self, email: str, **fields) -> None:
        with self._lock:
            u = self._load().get(email.lower())
            if u is not None:
                u.update(fields)
                self._save()


def public_user(u: dict) -> dict:
    """What the browser is allowed to see about an account."""
    return {"name": u.get("name", ""), "email": u.get("email", ""),
            "picture": u.get("picture") or ""}


# ── the service ───────────────────────────────────────────────────────────────

class AuthService:
    """
    code_valid(code) -> bool   is this a live device code? (does not use it up)
    code_take(code)  -> bool   use the code up
    get_client_id()  -> str    the Google OAuth client id, or ""
    verify_google    -> optional override, (credential, client_id) -> claims dict
    """

    def __init__(self, store_path: Path,
                 code_valid: Callable[[str], bool],
                 code_take: Callable[[str], bool],
                 get_client_id: Callable[[], str],
                 verify_google: Callable[[str, str], dict] | None = None):
        self.store         = AccountStore(store_path)
        self._code_valid   = code_valid
        self._code_take    = code_take
        self._get_client   = get_client_id
        self._verify_g     = verify_google or _verify_google_credential
        self._fails: dict[str, list[float]] = {}
        self._flock        = threading.Lock()

    # ── throttling ────────────────────────────────────────────────────────

    def _recent(self, key: str) -> int:
        now = time.time()
        with self._flock:
            hits = [t for t in self._fails.get(key, []) if now - t < _FAIL_WINDOW]
            if hits:
                self._fails[key] = hits
            else:
                self._fails.pop(key, None)
            if len(self._fails) > 5000:                 # bound memory
                self._fails.clear()
            return len(hits)

    def _fail(self, *keys: str) -> None:
        now = time.time()
        with self._flock:
            for k in keys:
                self._fails.setdefault(k, []).append(now)

    def _clear(self, key: str) -> None:
        with self._flock:
            self._fails.pop(key, None)

    def _blocked(self, ip: str, email: str = "") -> bool:
        if self._recent(f"ip|{ip}") >= _FAIL_LIMIT_IP:
            return True
        return bool(email) and self._recent(f"id|{ip}|{email}") >= _FAIL_LIMIT_ID

    @staticmethod
    def _too_many():
        return 429, {"ok": False,
                     "error": "Too many attempts. Wait a few minutes and try again."}

    # ── public surface ────────────────────────────────────────────────────

    def config(self) -> dict:
        cid = (self._get_client() or "").strip()
        return {
            "google_client_id": cid,
            "google_ready":     bool(cid) and _google_lib_available(),
            "has_accounts":     self.store.count() > 0,
        }

    def signup(self, body: dict, ip: str) -> tuple[int, dict]:
        name  = _clean_name(body.get("name"))
        email = _clean_email(body.get("email"))
        pw    = body.get("password")
        code  = str(body.get("device_code") or "").strip().upper()

        if self._blocked(ip, email or ""):
            return self._too_many()
        if not name:
            return 400, {"ok": False, "field": "name", "error": "Enter your name."}
        if not email:
            return 400, {"ok": False, "field": "email", "error": "Enter a valid email address."}
        bad = _password_problem(pw, email)
        if bad:
            return 400, {"ok": False, "field": "password", "error": bad}
        if self.store.by_email(email):
            return 409, {"ok": False, "field": "email",
                         "error": "An account with this email already exists. Try signing in."}
        if not self._code_valid(code):
            self._fail(f"ip|{ip}")
            return 401, {"ok": False, "field": "device_code",
                         "error": "That device code is invalid or has expired. "
                                  "Press Remote Control in the desktop app for a new one."}

        user = {"name": name, "email": email, "pw": hash_password(pw),
                "google_sub": None, "picture": "", "created": int(time.time())}
        if not self.store.create(user):                      # lost a race
            return 409, {"ok": False, "field": "email",
                         "error": "An account with this email already exists. Try signing in."}
        self._code_take(code)
        return 200, {"ok": True, "user": public_user(user)}

    def login(self, body: dict, ip: str) -> tuple[int, dict]:
        email = _clean_email(body.get("email"))
        pw    = body.get("password")
        pw    = pw if isinstance(pw, str) else ""
        if self._blocked(ip, email or ""):
            return self._too_many()

        user = self.store.by_email(email) if email else None
        ok   = verify_password(pw, user.get("pw") if user else None)
        if not (user and ok):
            self._fail(f"ip|{ip}", f"id|{ip}|{email or ''}")
            return 401, {"ok": False, "error": "Incorrect email or password."}
        self._clear(f"id|{ip}|{email}")
        return 200, {"ok": True, "user": public_user(user)}

    def google(self, body: dict, ip: str) -> tuple[int, dict]:
        client_id  = (self._get_client() or "").strip()
        credential = body.get("credential")
        code       = str(body.get("device_code") or "").strip().upper()

        if not client_id or not _google_lib_available():
            return 503, {"ok": False,
                         "error": "Google sign-in is not set up on this computer yet."}
        if self._blocked(ip):
            return self._too_many()
        if not isinstance(credential, str) or not (20 < len(credential) < 8192):
            return 400, {"ok": False, "error": "Google sign-in failed. Please try again."}

        try:
            info = self._verify_g(credential, client_id)
            email = _clean_email(info.get("email"))
            sub   = str(info.get("sub") or "")
            if not email or not sub or info.get("email_verified") is not True:
                raise ValueError("unverified")
        except Exception:
            self._fail(f"ip|{ip}")
            return 401, {"ok": False, "error": "Google sign-in failed. Please try again."}

        name    = _clean_name(info.get("name")) or email.split("@")[0]
        picture = str(info.get("picture") or "")[:500]

        user = self.store.by_google_sub(sub) or self.store.by_email(email)
        if user:                                             # returning user
            fields = {}
            if not user.get("google_sub"):
                fields["google_sub"] = sub
            if picture and picture != user.get("picture"):
                fields["picture"] = picture
            if fields:
                self.store.update(user["email"], **fields)
                user.update(fields)
            return 200, {"ok": True, "user": public_user(user)}

        # New account — must be authorised from the computer, exactly once.
        profile = {"name": name, "email": email, "picture": picture}
        if not code:
            return 403, {"ok": False, "need_code": True, "profile": profile,
                         "error": "Enter the device code shown in the desktop app "
                                  "to finish creating your account."}
        if not self._code_valid(code):
            self._fail(f"ip|{ip}")
            return 401, {"ok": False, "need_code": True, "profile": profile,
                         "error": "That device code is invalid or has expired."}

        user = {"name": name, "email": email, "pw": None, "google_sub": sub,
                "picture": picture, "created": int(time.time())}
        if not self.store.create(user):
            return 409, {"ok": False, "error": "Could not create the account. Try signing in."}
        self._code_take(code)
        return 200, {"ok": True, "user": public_user(user)}


# ── helpers ───────────────────────────────────────────────────────────────────

def _clean_name(v) -> str:
    if not isinstance(v, str):
        return ""
    v = re.sub(r"[\x00-\x1f\x7f<>]", "", v)               # no control chars / tags
    return re.sub(r"\s+", " ", v).strip()[:_MAX_NAME]


def _clean_email(v) -> str:
    if not isinstance(v, str):
        return ""
    v = v.strip().lower()
    return v if len(v) <= 254 and _EMAIL_RE.match(v) else ""


def _password_problem(pw, email: str) -> str:
    if not isinstance(pw, str) or len(pw) < _MIN_PW:
        return f"Use at least {_MIN_PW} characters."
    if len(pw) > _MAX_PW:
        return f"Use at most {_MAX_PW} characters."
    if pw.lower() in _COMMON_PASSWORDS or pw.lower() == email.split("@")[0]:
        return "That password is too easy to guess. Pick something less common."
    return ""


def _google_lib_available() -> bool:
    try:
        import google.oauth2.id_token          # noqa: F401
        import google.auth.transport.requests  # noqa: F401
        return True
    except Exception:
        return False


def _verify_google_credential(credential: str, client_id: str) -> dict:
    """Check signature, expiry, issuer and audience of a Google ID token."""
    from google.oauth2 import id_token
    from google.auth.transport import requests as g_requests
    return id_token.verify_oauth2_token(credential, g_requests.Request(), client_id)
