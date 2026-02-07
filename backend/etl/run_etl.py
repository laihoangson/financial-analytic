import fetch_data
import clean_data

def main():
    print("Running ETL...")
    fetch_data.main()
    clean_data.main()
    print("ETL done.")

if __name__ == "__main__":
    main()