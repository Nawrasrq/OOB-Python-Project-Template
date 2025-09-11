# Entry point for the ETL or other automation scripts
# Basic script used to initialize the child class and run the main method(s)

from scripts.child import Child

def main():
    """
    Main function
    """
    child_1 = Child('child/child_1.log')
    child_1.main()
    child_1.dispose()

    child_2 = Child('child/child_2.log')
    child_2.main()    
    child_2.dispose()

if __name__ == "__main__":
    main()