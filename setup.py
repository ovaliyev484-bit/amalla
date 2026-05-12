import argparse
import subprocess
import sys
MIN_PYTHON = (3, 10)
def _check_python() -> None:
    if sys.version_info < MIN_PYTHON:
        raise SystemExit(
            f"Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+ required, found {sys.version.split()[0]}"
        )
def _run(cmd: list[str], title: str) -> None:
    print(f"\n{title}")
    print(">", " ".join(cmd))
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        raise SystemExit(f"Setup failed while running: {' '.join(cmd)}\nError: {e}") from e
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Setup Malika assistant dependencies and optional browser binaries."
    )
    parser.add_argument(
        "--skip-playwright",
        action="store_true",
        help="Skip Playwright browser installation."
    )
    args = parser.parse_args()

    _check_python()

    _run([sys.executable, "-m", "pip", "install", "--upgrade", "pip", "--break-system-packages"], "Upgrading pip...")
    _run(
        [sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "--break-system-packages"],
        "Installing requirements..."
    )
    if not args.skip_playwright:
        _run(
            [sys.executable, "-m", "playwright", "install"],
            "Installing Playwright browsers..."
        )
    else:
        print("\nSkipping Playwright browser install by request.")

    print("\nSetup complete. Run 'python main.py' to start Malika.")
if __name__ == "__main__":
    main()
