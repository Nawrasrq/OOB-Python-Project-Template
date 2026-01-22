# Tool class used to create a GUI to manually operate ETLs, automation scripts or related processes.
# Typically includes uploaders, downloaders, managers, etc.
# Does not necessarily need to inherit a child class, that is in the case we want to manually operate the child class logic.
# The tool can contain its own logic or a new script (should still be a class even if doesnt inherit child or base class) can be created in scripts to be inherited and used by the tool.

import logging
import os
import tkinter as tk
from typing import Optional

from scripts.child import Child


class Tool:
    def __init__(self, log_file_path: str = "tool/tool.log"):
        """
        Initialize the tool class

        Parameters
        ----------
        log_file_path : str, optional
            The path to the log file including the file name, relative to logs directory.
            Defaults to "tool/tool.log".
        """
        try:
            # Logging
            self.log_file_path = log_file_path
            log_dir = os.path.dirname(log_file_path)
            if log_dir:
                full_log_dir = os.path.join("logs", log_dir)
                os.makedirs(full_log_dir, exist_ok=True)

            # Initialize child class
            self.child = Child(log_file_path)
            tool_logger_name = f"tools.tool.instance_{self.child.instance_id}"
            self.logger = logging.getLogger(tool_logger_name)

            # GUI
            self.root: Optional[tk.Tk] = None
            self.create_gui()
            self.logger.info("Initialized Tool class")

        except Exception as e:
            if hasattr(self, "logger") and self.logger:
                self.logger.error(f"Failed to initialize Tool class: {e}")
            else:
                print(f"Failed to initialize Tool class: {e}")
            raise

    def main(self) -> None:
        """
        Main function
        """
        try:
            self.child.main()
        except Exception as e:
            self.logger.error(f"Error in main: {e}")
            raise

    def create_gui(self) -> None:
        """
        Create the GUI
        """
        try:
            self.logger.info("Creating GUI")
            self.root = tk.Tk()
            self.root.title("Tool GUI")
        except Exception as e:
            self.logger.error(f"Failed to create GUI: {e}")
            raise

    def run(self) -> None:
        """
        Run the tool
        """
        try:
            self.logger.info("Running tool")
            self.main()
        except Exception as e:
            self.logger.error(f"Error running tool: {e}")
            raise

    def dispose(self) -> None:
        """
        Dispose of the tool's resources
        """
        try:
            self.logger.info("Disposing of Tool class")

            # Destroy GUI if it exists
            if self.root:
                self.root.destroy()
                self.root = None

            # Dispose of child resources
            if hasattr(self, "child") and self.child:
                self.child.dispose()

        except Exception as e:
            self.logger.error(f"Error disposing Tool class: {e}")
            raise


if __name__ == "__main__":
    tool = Tool()
    try:
        tool.run()
    finally:
        tool.dispose()
