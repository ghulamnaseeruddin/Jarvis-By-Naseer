"""
Single source of truth for the app version.

* `python main.py --version` and the phone dashboard read it from here.
* The installers, the release workflow and the website all take the version
  from the git tag (v1.2.3) — bump this to match when you cut a release.
* GITHUB_REPO ("owner/name") is where the "update available" check and the
  website's download buttons look for releases. Set it once with
  `python website/tools/configure.py`.
"""

__version__ = "1.0.0"

APP_NAME    = "JARVIS"
PRODUCT     = "Mark LIV"
GITHUB_REPO = "ghulamnaseeruddin/Jarvis-By-Naseer"
