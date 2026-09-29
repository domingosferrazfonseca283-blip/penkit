import os, sys

def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from boot import run as boot_run
    boot_run()
    from dashboard import run as dashboard_run
    dashboard_run()

if __name__ == "__main__":
    main()
