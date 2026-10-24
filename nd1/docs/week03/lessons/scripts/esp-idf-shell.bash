# Internal Bash initialization file used by start-esp-idf.sh on macOS/Linux.
# Do not run or source this file directly.
if [ -z "${ND69_IDF_PATH:-}" ]; then
    echo 'Use bash start-esp-idf.sh to open the ESP-IDF shell.' >&2
    exit 1
fi
# Load the user's normal interactive Bash settings before activating ESP-IDF.
if [ -f "$HOME/.bashrc" ]; then . "$HOME/.bashrc"; fi
if [ "${ND69_INSTALL_TOOLS:-0}" = 1 ]; then
    if ! bash "$ND69_IDF_PATH/install.sh" "$ND69_TARGET"; then
        echo 'Tool installation failed. Resolve the installer error and retry.' >&2
        exit 1
    fi
fi
if ! . "$ND69_IDF_PATH/export.sh"; then
    echo 'ESP-IDF activation failed. Check prerequisites and install tools with --install-tools.' >&2
    exit 1
fi
if ! command -v idf.py >/dev/null 2>&1 || ! idf.py --version; then
    echo 'ESP-IDF verification failed. Review activation output above.' >&2
    exit 1
fi
cd -- "$ND69_PROJECT_PATH" || exit 1
unset ND69_IDF_PATH ND69_PROJECT_PATH ND69_INSTALL_TOOLS ND69_TARGET
printf 'ESP-IDF ready in %s\nRun idf.py build from a project directory. Type exit to close this session.\n' "$PWD"
