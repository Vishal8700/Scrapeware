import subprocess
import os
import sys
import time
import signal
import logging
from typing import List, Dict
from datetime import datetime

# Set up logging
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

log_file = os.path.join(log_dir, f"fastapi_runner_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class FastAPIRunner:
    def __init__(self, base_directory: str):
        self.base_directory = base_directory
        self.apps = []
        self.processes: List[subprocess.Popen] = []
        self.setup_signal_handlers()
        self.discover_apps()

    def setup_signal_handlers(self):
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def signal_handler(self, signum, frame):
        logger.info("Shutdown signal received. Stopping all applications...")
        self.stop_all_apps()
        sys.exit(0)

    def discover_apps(self):
        """Automatically discovers app.py files in subdirectories."""
        apps = []
        for root, _, files in os.walk(self.base_directory):
            if "app.py" in files:
                app_folder = os.path.relpath(root, self.base_directory)
                folder_name = os.path.basename(app_folder)

                # Assign specific ports for known apps
                port_mapping = {
                    "auction_api": 5000,
                    "bid_api": 8000,
                    "linkedin_api": 8002,
                    "userapi": 8006,
                    "companydetailLinkedin": 8003,
                }

                port = port_mapping.get(folder_name)
                if port is None:
                    logger.warning(f"No predefined port for {folder_name}. Skipping...")
                    continue

                apps.append({
                    "folder": app_folder,
                    "file": "app.py",
                    "host": "0.0.0.0",
                    "port": port
                })

        self.apps = apps
        logger.info(f"Discovered applications: {self.apps}")

    def run_app(self, app: Dict) -> subprocess.Popen:
        """Run a single FastAPI application."""
        app_dir = os.path.abspath(os.path.join(self.base_directory, app['folder']))
        file_name = os.path.splitext(app['file'])[0]
        module_path = f"{app['folder'].replace(os.path.sep, '.')}.{file_name}"

        if not os.path.exists(app_dir):
            logger.error(f"Directory not found: {app_dir}")
            return None
        if not os.path.exists(os.path.join(app_dir, app['file'])):
            logger.error(f"File not found: {os.path.join(app_dir, app['file'])}")
            return None

        cmd = [
            sys.executable, "-m", "uvicorn",
            f"{module_path}:app",  # Updated to include the correct module path
            "--host", app["host"],
            "--port", str(app["port"]),
            "--reload"
        ]

        logger.info(f"Starting {app['folder']} on {app['host']}:{app['port']}...")

        try:
            process = subprocess.Popen(
                cmd, cwd=app_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            time.sleep(2)  # Allow some time for the app to start

            # Check if the process started successfully by checking its PID
            if process.pid is None:
                logger.error(f"Failed to start {app['folder']}. No PID returned.")
                return None

            return process

        except Exception as e:
            logger.error(f"Error starting {app['folder']}: {e}")
            return None

    def start_all_apps(self):
        """Start all FastAPI applications."""
        for app in self.apps:
            process = self.run_app(app)
            if process:
                self.processes.append((process, app))
                logger.info(f"Started {app['folder']} on {app['host']}:{app['port']}")

    def stop_all_apps(self):
        """Stop all running FastAPI applications."""
        for process, app in self.processes:
            logger.info(f"Stopping {app['folder']}...")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning(f"{app['folder']} did not terminate in time. Force killing...")
                process.kill()

        self.processes.clear()
        logger.info("All applications stopped.")

    def monitor_apps(self):
        """Monitor applications for any issues."""
        try:
            while True:
                time.sleep(10)
                for process, app in list(self.processes):
                    if process.poll() is not None:  # Process has terminated
                        logger.warning(f"{app['folder']} has stopped. Restarting...")
                        self.processes.remove((process, app))
                        new_process = self.run_app(app)
                        if new_process:
                            self.processes.append((new_process, app))
                            logger.info(f"Restarted {app['folder']} on {app['host']}:{app['port']}")

        except KeyboardInterrupt:
            self.signal_handler(None, None)


def main():
    base_directory = os.getcwd()  # Root directory containing subfolders with app.py
    runner = FastAPIRunner(base_directory)
    logger.info("=== FastAPI Runner Starting ===")
    runner.start_all_apps()
    runner.monitor_apps()
    logger.info("=== FastAPI Runner Stopped ===")


if __name__ == "__main__":
    main()
