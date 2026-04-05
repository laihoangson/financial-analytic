import fetch_data
import clean_data

def main():
    print("--- PHASE 1: Fetch & Clean Data ---")
    fetch_data.main()
    clean_data.main()
    print("Phase 1 Complete. Dashboard data is ready!")

if __name__ == "__main__":
    main()