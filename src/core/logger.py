from datetime import datetime
import sys

class Log:
    """
    Custom logger class with static methods using print.
    """
    
    @staticmethod
    def _timestamp():
        import pytz
        return datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%Y-%m-%d %H:%M:%S')

    @staticmethod
    def _format(level, message, color_code=""):
        time_str = Log._timestamp()
        # ANSI reset code
        RESET = "\033[0m"
        # If color_code is provided, wrap the whole line or just the level. 
        # Let's wrap the level and message for visibility.
        if color_code:
            return f"[{time_str}] {color_code}[{level}]{RESET} {message}"
        return f"[{time_str}] [{level}] {message}"

    @staticmethod
    def info(message):
        # Blue for INFO
        print(Log._format("   INFO", message, "\033[94m"), flush=True)

    @staticmethod
    def success(message):
        # Green for SUCCESS
        print(Log._format("SUCCESS", message, "\033[92m"), flush=True)

    @staticmethod
    def warning(message):
        # Yellow for WARNING
        print(Log._format("WARNING", message, "\033[93m"), flush=True)

    @staticmethod
    def error(message):
        # Red for ERROR
        print(Log._format("  ERROR", message, "\033[91m"), file=sys.stderr, flush=True)

    @staticmethod
    def debug(message):
        # Cyan for DEBUG
        print(Log._format("  DEBUG", message, "\033[96m"), flush=True)
