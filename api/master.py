import subprocess
import os
import sys
import time
import signal
import logging
from typing import List, Dict
from datetime import datetime

# Set up logging with file output
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

# Define the FastAPI applications and their respective host and port
apps = [
    {"folder": "auction_api", "file": "app.py", "host": "0.0.0.0", "port": 5000},
    {"folder": "bid_api", "file": "main.py", "host": "0.0.0.0", "port": 8000},
    {"folder": "companydetailLinkedin", "file": "main1.py", "host": "0.0.0.0", "port": 8003},
    {"folder": "linkedin_api", "file": "main2.py", "host": "0.0.0.0", "port": 8002},
    {"folder": "userapi", "file": "main3.py", "host": "0.0.0.0", "port": 8006},
]


class FastAPIRunner:
    def __init__(self, apps: List[Dict]):
        self.apps = apps
        self.processes: List[Dict] = []
        self.setup_signal_handlers()

    def setup_signal_handlers(self):
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def signal_handler(self, signum, frame):
        logger.info("Shutdown signal received. Stopping all applications...")
        self.stop_all_apps()
        sys.exit(0)

    def validate_app_config(self, app: Dict) -> bool:
        required_keys = ['folder', 'file', 'host', 'port']
        if not all(key in app for key in required_keys):
            logger.error(f"Missing required configuration for app: {app}")
            return False

        app_dir = os.path.abspath(app['folder'])
        if not os.path.exists(app_dir):
            logger.error(f"Folder not found: {app_dir}")
            return False

        file_path = os.path.join(app_dir, app['file'])
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return False

        return True

    def create_cmd_command(self, app_dir: str, module_path: str, app: Dict) -> str:
        """Create the command string for CMD window"""
        cmd = (
            f'cd /d "{app_dir}" && '
            f'{sys.executable} -m uvicorn {module_path}:app '
            f'--host {app["host"]} --port {app["port"]} --reload'
        )
        return cmd

    def run_app(self, app: Dict) -> Dict:
        """Run a single FastAPI application"""
        if not self.validate_app_config(app):
            return None

        try:
            # Get absolute path and proper module path
            app_dir = os.path.abspath(app['folder'])
            file_name = os.path.splitext(app['file'])[0]
            module_path = f"{app['folder']}.{file_name}".replace(os.path.sep, '.')

            if sys.platform == 'win32':
                # Create a unique title for the CMD window
                window_title = f"FastAPI_{app['folder']}_{app['port']}"
                cmd = self.create_cmd_command(app_dir, module_path, app)

                # Create a batch file for this command
                batch_file = os.path.join(app_dir, f"run_{app['folder']}.bat")
                with open(batch_file, 'w') as f:
                    f.write(f'title {window_title}\n')
                    f.write(f'{cmd}\n')
                    f.write('pause\n')

                # Start the batch file in a new CMD window
                process = subprocess.Popen(
                    ['start', 'cmd', '/c', batch_file],
                    shell=True,
                    cwd=app_dir
                )

            else:  # For Unix-like systems
                if sys.platform == 'darwin':  # macOS
                    script = (f'tell application "Terminal" to do script '
                              f'"cd {app_dir} && {sys.executable} -m uvicorn '
                              f'{module_path}:app --host {app["host"]} '
                              f'--port {str(app["port"])} --reload"')
                    process = subprocess.Popen(['osascript', '-e', script])
                else:  # Linux
                    process = subprocess.Popen([
                        'gnome-terminal', '--',
                        'bash', '-c',
                        f'cd {app_dir} && {sys.executable} -m uvicorn '
                        f'{module_path}:app --host {app["host"]} '
                        f'--port {str(app["port"])} --reload; exec bash'
                    ])

            logger.info(f"Started API: {app['folder']} on {app['host']}:{app['port']}")

            # Create process info dictionary
            process_info = {
                'process': process,
                'app': app,
                'start_time': datetime.now(),
                'port': app['port']
            }

            # Wait a bit to ensure the process starts
            time.sleep(2)
            return process_info

        except Exception as e:
            logger.error(f"Failed to start {app['folder']}: {str(e)}")
            return None

    def start_all_apps(self):
        """Start all FastAPI applications"""
        logger.info("Starting all FastAPI applications...")

        for app in self.apps:
            # Check if an app is already running on this port
            if any(p['port'] == app['port'] for p in self.processes):
                logger.warning(f"Port {app['port']} is already in use. Skipping {app['folder']}")
                continue

            process_info = self.run_app(app)
            if process_info:
                self.processes.append(process_info)
                logger.info(f"Waiting for {app['folder']} to initialize...")
                time.sleep(3)

        if not self.processes:
            logger.error("No applications were started successfully")
            return False

        logger.info(f"Successfully started {len(self.processes)} applications")
        self.log_running_apps()
        return True

    def log_running_apps(self):
        """Log information about all running applications"""
        logger.info("\n=== Running Applications ===")
        for proc_info in self.processes:
            app = proc_info['app']
            start_time = proc_info['start_time']
            uptime = datetime.now() - start_time
            logger.info(f"- {app['folder']}:")
            logger.info(f"  URL: http://{app['host']}:{app['port']}")
            logger.info(f"  Uptime: {uptime}")
        logger.info("========================\n")

    def stop_all_apps(self):
        """Stop all running applications"""
        logger.info("Stopping all applications...")

        for proc_info in self.processes:
            try:
                process = proc_info['process']
                app = proc_info['app']

                if sys.platform == 'win32':
                    # Kill all python processes running on the specific port
                    kill_cmd = f'for /f "tokens=5" %a in (\'netstat -aon ^| findstr "{app["port"]}"\') do taskkill /F /PID %a'
                    subprocess.run(kill_cmd, shell=True)
                else:
                    process.terminate()
                    process.wait(timeout=5)

                logger.info(f"Stopped {app['folder']}")

            except Exception as e:
                logger.error(f"Error stopping {app['folder']}: {str(e)}")

        self.processes.clear()
        logger.info("All applications stopped")

    def monitor_apps(self):
        """Monitor running applications and restart if necessary"""
        while self.processes:
            time.sleep(10)  # Check every 10 seconds
            self.log_running_apps()


def main():
    if not os.path.exists('logs'):
        os.makedirs('logs')

    logger.info("=== FastAPI Runner Starting ===")
    logger.info(f"Log file: {log_file}")

    runner = FastAPIRunner(apps)
    if runner.start_all_apps():
        try:
            runner.monitor_apps()
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        finally:
            runner.stop_all_apps()

    logger.info("=== FastAPI Runner Stopped ===")


if __name__ == "__main__":
    main()