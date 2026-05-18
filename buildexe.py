import os
import subprocess
import sys


def main() -> int:
    version = input("Enter version (e.g., v1.1.0): ").strip()
    if not version:
        print("Version is required.")
        return 1

    exe_name = f"Sigma_Judge-{version}"
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconsole",
        "--onefile",
        "--name",
        exe_name,
        "run.py",
    ]

    print("Running:", " ".join(cmd))
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print("Build failed.")
        return result.returncode

    print(f"Build complete: dist{os.sep}{exe_name}.exe")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
