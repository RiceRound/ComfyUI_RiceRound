import configparser
import hashlib
from io import BytesIO
import os
from pathlib import Path
import random
import string
import sys
import uuid
import torch
import numpy as np
from PIL import Image
import platform
import subprocess


def pil2tensor(images):
    def single_pil2tensor(image):
        np_image = np.array(image).astype(np.float32) / 255.0
        if np_image.ndim == 2:
            return torch.from_numpy(np_image).unsqueeze(0)
        else:
            return torch.from_numpy(np_image).unsqueeze(0)

    if isinstance(images, Image.Image):
        return single_pil2tensor(images)
    else:
        return torch.cat([single_pil2tensor(img) for img in images], dim=0)


def calculate_machine_id():
    system = platform.system()
    if system == "Linux":
        try:
            with open("/etc/machine-id", "r") as f:
                return f.read().strip()
        except FileNotFoundError:
            try:
                with open("/var/lib/dbus/machine-id", "r") as f:
                    return f.read().strip()
            except FileNotFoundError:
                pass
        try:
            output = subprocess.check_output(["cat", "/sys/class/dmi/id/product_uuid"])
            return output.decode().strip()
        except Exception:
            pass
    elif system == "Windows":
        try:
            import winreg

            reg_key = "SOFTWARE\\Microsoft\\Cryptography"
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_key) as key:
                machine_guid, _ = winreg.QueryValueEx(key, "MachineGuid")
                return machine_guid
        except Exception:
            pass
    elif system == "Darwin":
        try:
            output = subprocess.check_output(
                ["ioreg", "-rd1", "-c", "IOPlatformExpertDevice"]
            )
            for line in output.decode().splitlines():
                if "IOPlatformUUID" in line:
                    return line.split("=")[-1].strip().strip('"')
        except Exception:
            pass
    return str(uuid.getnode())


def normalize_machine_id(machine_id):
    salt = "RiceRound"
    trimmed_id = machine_id.strip()
    lowercase_id = trimmed_id.lower()
    salted_id = lowercase_id + salt
    hash_obj = hashlib.md5(salted_id.encode("utf-8"))
    return hash_obj.hexdigest()


def get_local_app_setting_path():
    home = Path.home()
    config_dir = home / "RiceRound"
    return config_dir


def get_machine_id():
    config_dir = get_local_app_setting_path()
    config_file = config_dir / "machine.ini"
    try:
        config_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"Error creating directory '{config_dir}': {e}")
        return ""
    config = configparser.ConfigParser()
    try:
        if config_file.exists():
            config.read(config_file, encoding="utf-8")
            if "Machine" in config and "machine_id" in config["Machine"]:
                return config["Machine"]["machine_id"]
        original_host_id = calculate_machine_id()
        machine_id = normalize_machine_id(original_host_id)
        if "Machine" not in config:
            config.add_section("Machine")
        config.set("Machine", "machine_id", machine_id)
        with open(config_file, "w", encoding="utf-8") as file:
            config.write(file)
        return machine_id
    except Exception as e:
        print(f"Error handling machine ID in '{config_file}': {e}")
        return ""


def restart_comfyui():
    try:
        sys.stdout.close_log()
    except Exception:
        pass
    if "__COMFY_CLI_SESSION__" in os.environ:
        with open(os.path.join(os.environ["__COMFY_CLI_SESSION__"] + ".reboot"), "w"):
            0
        print("Restarting...\n\n")
        exit(0)
    sys_argv = sys.argv.copy()
    if "--windows-standalone-build" in sys_argv:
        sys_argv.remove("--windows-standalone-build")
    if sys.platform.startswith("win32"):
        cmds = ['"' + sys.executable + '"', '"' + sys_argv[0] + '"'] + sys_argv[1:]
    else:
        cmds = [sys.executable] + sys_argv
    print(f"Command: {cmds}", flush=True)
    return os.execv(sys.executable, cmds)


def combine_files(files, password, zip_file_path):
    import pyzipper

    for file_path in files:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"file not found: {file_path}")
    try:
        with pyzipper.AESZipFile(
            zip_file_path,
            "w",
            compression=pyzipper.ZIP_DEFLATED,
            encryption=pyzipper.WZ_AES,
        ) as zipf:
            if isinstance(password, str):
                password = password.encode("utf-8")
            zipf.setpassword(password)
            for index, file_path in enumerate(files, start=1):
                arcname = f"{index}.bin"
                zipf.write(file_path, arcname)
        return True
    except Exception as e:
        print(f"Error creating zip: {str(e)}")
        return False


def generate_random_string(length):
    letters = string.ascii_letters
    return "".join(random.choice(letters) for _ in range(length))
