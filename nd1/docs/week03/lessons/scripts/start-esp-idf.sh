#!/usr/bin/env bash
# Execute with bash; do not source this launcher.
set -e
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
case "$(uname -s)" in
    MINGW*|MSYS*|CYGWIN*)
        # Use PowerShell parameter names, e.g. -IdfPath 'D:\dev\esp\v6.1\esp-idf'.
        exec env -u MSYSTEM powershell.exe -NoLogo -NoProfile -NoExit -File "$(cygpath -w "$script_dir/start-esp-idf.ps1")" "$@"
        ;;
esac
idf_path=${IDF_PATH:-"$HOME/esp/esp-idf"}
project_path=$PWD
install_tools=0
target=esp32s3
while [ "$#" -gt 0 ]; do
    case "$1" in
        --idf-path|--project-path|--target)
            if [ "$#" -lt 2 ] || [ -z "$2" ]; then echo "Missing value for $1" >&2; exit 2; fi
            case "$1" in
                --idf-path) idf_path=$2 ;;
                --project-path) project_path=$2 ;;
                --target) target=$2 ;;
            esac
            shift 2 ;;
        --install-tools) install_tools=1; shift ;;
        *) echo "Unknown argument: $1. Use --idf-path PATH, --project-path PATH, --install-tools, --target CHIP." >&2; exit 2 ;;
    esac
done
if [ ! -f "$idf_path/export.sh" ] || [ ! -f "$idf_path/tools/idf.py" ]; then
    echo "ESP-IDF not found at '$idf_path'. Supply --idf-path /path/to/esp-idf." >&2
    exit 1
fi
if [ ! -d "$project_path" ]; then echo "Project directory does not exist: $project_path" >&2; exit 1; fi
export KMUTT_IDF_PATH KMUTT_PROJECT_PATH KMUTT_INSTALL_TOOLS KMUTT_TARGET
KMUTT_IDF_PATH=$(cd -- "$idf_path" && pwd)
KMUTT_PROJECT_PATH=$(cd -- "$project_path" && pwd)
KMUTT_INSTALL_TOOLS=$install_tools
KMUTT_TARGET=$target
exec bash --noprofile --rcfile "$script_dir/esp-idf-shell.bash" -i
