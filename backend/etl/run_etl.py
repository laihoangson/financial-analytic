from fetch_data import fetch_data
from clean_data import clean_data

def main():
    print("Running ETL...")
    fetch_data()
    clean_data()
    print("ETL done.")

if __name__ == "__main__":
    main()