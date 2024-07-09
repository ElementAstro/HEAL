import subprocess
import sys
import os
from typing import Optional, List, Dict

def is_software_installed(software_name: str) -> bool:
    """
    Check if a software is installed on the system.

    Args:
        software_name (str): The name of the software to check.

    Returns:
        bool: True if the software is installed, False otherwise.
    """
    try:
        if sys.platform == "win32":
            subprocess.run(["where", software_name], check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            subprocess.run(["which", software_name], check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        return False


def get_software_path(software_name: str) -> Optional[str]:
    """
    Get the installation path of the software.

    Args:
        software_name (str): The name of the software.

    Returns:
        Optional[str]: The installation path if found, otherwise None.
    """
    try:
        if sys.platform == "win32":
            result = subprocess.run(
                ["where", software_name], check=True, capture_output=True, text=True)
        else:
            result = subprocess.run(
                ["which", software_name], check=True, capture_output=True, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None


def get_software_version(software_name: str, version_arg: str = "--version") -> Optional[str]:
    """
    Get the version of the installed software.

    Args:
        software_name (str): The name of the software.
        version_arg (str): The argument to get the version, default is '--version'.

    Returns:
        Optional[str]: The version information if found, otherwise None.
    """
    try:
        result = subprocess.run(
            [software_name, version_arg], check=True, capture_output=True, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None


def check_software_permissions(software_path: str) -> Dict[str, bool]:
    """
    Check the permissions of the software.

    Args:
        software_path (str): The path of the software.

    Returns:
        Dict[str, bool]: A dictionary containing the permissions (read, write, execute).
    """
    permissions = {
        'read': os.access(software_path, os.R_OK),
        'write': os.access(software_path, os.W_OK),
        'execute': os.access(software_path, os.X_OK)
    }
    return permissions


def get_software_dependencies(software_name: str) -> Optional[List[str]]:
    """
    Get the dependencies of the software.

    Args:
        software_name (str): The name of the software.

    Returns:
        Optional[List[str]]: A list of dependencies if found, otherwise None.
    """
    try:
        if sys.platform == "win32":
            # Windows: Use 'dumpbin' from Visual Studio to check dependencies
            software_path = get_software_path(software_name)
            if software_path:
                result = subprocess.run(
                    ["dumpbin", "/DEPENDENTS", software_path], check=True, capture_output=True, text=True)
                dependencies = [line.strip() for line in result.stdout.splitlines(
                ) if line.strip().endswith(".dll")]
                return dependencies
            return None
        else:
            # macOS/Linux/Unix: use 'ldd' command
            software_path = get_software_path(software_name)
            if software_path:
                result = subprocess.run(
                    ["ldd", software_path], check=True, capture_output=True, text=True)
                dependencies = [line.split()[0]
                                for line in result.stdout.splitlines() if '=>' in line]
                return dependencies
            return None
    except subprocess.CalledProcessError:
        return None


def get_software_documentation(software_name: str) -> Optional[str]:
    """
    Get the documentation path of the software.

    Args:
        software_name (str): The name of the software.

    Returns:
        Optional[str]: The documentation path if found, otherwise None.
    """
    try:
        if sys.platform == "win32":
            # Windows: No universal command for documentation, return None
            return None
        else:
            # macOS/Linux/Unix: use 'man' command
            result = subprocess.run(
                ["man", "-w", software_name], check=True, capture_output=True, text=True)
            return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None
