#!/usr/bin/env bash
# Sync a public knowledge-vault repo to a local cache and print its path.
# Public repo => no token, no credentials, no MCP server.
#
# Usage: sync-vault.sh <owner/repo>
#   e.g. sync-vault.sh t-labs-buy/abap-wiki
#
# Output (key=value lines):
#   VAULT_PATH=<absolute path to the local clone>
#   STATUS=cloned | updated | repaired | offline (using cached copy)
#   LATEST=<short sha> <date> — <subject>
#   PAGES=<number of vault pages, excluding raw/>
#
# Always exits 0 when a usable copy exists, so a network blip never blocks an
# answer. Exits 1 only when there is no usable copy at all.

set -uo pipefail

REPO="${1:?usage: sync-vault.sh <owner/repo>}"
NAME="${REPO##*/}"
DEST="${HOME}/.cache/claude-vaults/${NAME}"
URL="https://github.com/${REPO}.git"

# Never prompt for credentials: a public clone must not hang waiting for input.
export GIT_TERMINAL_PROMPT=0
# Abort a stalled transfer instead of hanging forever behind a proxy/blackhole.
GIT_OPTS=(-c credential.helper= -c core.askPass=
          -c http.lowSpeedLimit=1000 -c http.lowSpeedTime=20)

git_q() { git "${GIT_OPTS[@]}" "$@" 2>/dev/null; }

# A cache is usable only if it is a valid git repo AND looks like a vault.
cache_ok() {
  [ -d "${DEST}/.git" ] &&
  git_q -C "${DEST}" rev-parse --git-dir >/dev/null &&
  [ -f "${DEST}/meta/index.md" ]
}

do_clone() {
  rm -rf "${DEST}"
  mkdir -p "$(dirname "${DEST}")"
  git_q clone --depth 1 -q "${URL}" "${DEST}"
}

STATUS=""

if [ -e "${DEST}" ] && ! cache_ok; then
  # Leftover or corrupted directory — rebuild it from scratch.
  if do_clone; then
    STATUS="repaired"
  else
    echo "ERROR: local copy at ${DEST} is unusable and re-cloning failed." >&2
    echo "Check that you are online, then delete ${DEST} and retry." >&2
    exit 1
  fi
elif [ ! -e "${DEST}" ]; then
  if do_clone; then
    STATUS="cloned"
  else
    echo "ERROR: could not clone ${URL}" >&2
    echo "Check the repo name and that you are online." >&2
    exit 1
  fi
else
  if git_q -C "${DEST}" fetch --depth 1 -q origin HEAD &&
     git_q -C "${DEST}" reset --hard -q FETCH_HEAD; then
    STATUS="updated"
  else
    STATUS="offline (using cached copy)"
  fi
fi

COMMIT=$(git_q -C "${DEST}" log -1 --format='%h %cd — %s' --date=short)
# Count only the four content zones (01-… 04-…): excludes raw/, meta/, .git and CI files.
PAGES=$(find "${DEST}"/0*/ -name '*.md' 2>/dev/null | wc -l | tr -d ' ')

echo "VAULT_PATH=${DEST}"
echo "STATUS=${STATUS}"
echo "LATEST=${COMMIT:-unknown}"
echo "PAGES=${PAGES}"
