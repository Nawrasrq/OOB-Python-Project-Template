# Tool class used to create a GUI to manually operate ETLs, automation scripts or related processes.
# Typically includes uploaders, downloaders, managers, etc.
# Does not necessarily need to inherit a child class, that is in the case we want to manually operate the child class logic.
# The tool can contain its own logic or a new script (should still be a class even if doesnt inherit child or base class) can be created in scripts to be inherited and used by the tool.

import logging
import os

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
        # Logging
        self.log_file_path = log_file_path
        log_dir = os.path.dirname(log_file_path)
        if log_dir:
            full_log_dir = os.path.join("logs", log_dir)
            os.makedirs(full_log_dir, exist_ok=True)

        self.child = Child(log_file_path)
        tool_logger_name = f"tools.tool.instance_{self.child.instance_id}"
        self.logger = logging.getLogger(tool_logger_name)
        
        # GUI
        self.create_gui()
        self.logger.info("Initialized Tool class")

    def main(self):
        """
        Main function
        """
        self.child.main()

    def create_gui(self):
        """
        Create the GUI
        """
        self.logger.info("Creating GUI")

    def run(self):
        """
        Run the tool
        """
        self.logger.info("Running tool")
        self.main()

    def dispose(self):
        """
        Dispose of the tool's resources
        """
        self.logger.info("Disposing of Tool class")
        if hasattr(self, 'child') and self.child:
            self.child.dispose()

if __name__ == "__main__":
    tool = Tool()
    tool.run()