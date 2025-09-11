# Entry point for the ETL or other automation scripts
# Basic script used to initialize the child class and run the main method(s)

from tools.tool import Tool

def main():
    """
    Main function
    """
    tool = Tool("tool/tool.log")
    tool.run()
    tool.dispose()

if __name__ == "__main__":
    main()