# FILE: test_lib.py
# VERSION: 1.1.0
# START_MODULE_CONTRACT:
# PURPOSE: Verify environment — check Python version and installed library versions.
# SCOPE: Environment diagnostics before implementation. Run inside Docker container.
# KEYWORDS: [PATTERN(3): EnvironmentCheck; CONCEPT(2): Diagnostics; TECH(1): Docker]
# END_MODULE_CONTRACT
#
# START_CHANGE_SUMMARY:
# LAST_CHANGE: v1.1.0 — Added Docker-awareness and container detection.
# END_CHANGE_SUMMARY

import sys
import platform
import os
import importlib.metadata


# START_FUNCTION_check_versions
def check_versions():
    """
    Check and display Python version, platform info, container status, and
    installed library versions. This script should be run inside the Docker
    container before implementation to verify that the development environment
    matches the expected configuration from requirements.txt.
    """
    # START_BLOCK_SYSTEM_INFO: Display system and container info
    print(f"Python version: {sys.version}")
    print(f"Platform: {platform.platform()}")
    print(f"Executable: {sys.executable}")

    in_docker = os.path.exists("/.dockerenv") or os.environ.get("DOCKER_CONTAINER", False)
    print(f"Docker container: {'YES' if in_docker else 'NO (consider running inside container)'}")
    print("---")
    # END_BLOCK_SYSTEM_INFO

    # START_BLOCK_CHECK_LIBS: Read requirements.txt and check each library
    try:
        with open("requirements.txt", "r") as f:
            lines = f.readlines()
    except FileNotFoundError:
        print("requirements.txt not found!")
        return

    installed = 0
    missing = 0
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        lib_name = line.split("==")[0].split(">=")[0].split("<=")[0].strip()
        try:
            version = importlib.metadata.version(lib_name)
            print(f"  OK  {lib_name}=={version}")
            installed += 1
        except importlib.metadata.PackageNotFoundError:
            print(f"  MISSING  {lib_name}")
            missing += 1

    print("---")
    print(f"Installed: {installed}, Missing: {missing}")
    if missing > 0:
        print("ACTION: Run `pip install -r requirements.txt` inside container.")
    # END_BLOCK_CHECK_LIBS


# END_FUNCTION_check_versions


if __name__ == "__main__":
    check_versions()
