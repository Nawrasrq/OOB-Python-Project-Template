# File utility class for handling various file formats (CSV, Excel, TXT)
# Template class for file operations - customize based on your specific file processing needs

import logging

class File:
    def __init__(self, instance_id=None):
        """
        Initialize the File utility.
        
        Parameters
        ----------
        instance_id : int, optional
            The instance ID for logging purposes. If not provided, uses default logger.
        """
        # Logging
        if instance_id:
            logger_name = f"utils.file.instance_{instance_id}"
        else:
            logger_name = "utils.file"
        self.logger = logging.getLogger(logger_name)
        self.logger.info("Initialized File utility")