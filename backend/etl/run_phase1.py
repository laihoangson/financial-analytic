import fetch_data
import clean_data
import generate_insights

def main():
    print("--- PHASE 1: Fetch & Clean Data ---")
    fetch_data.main()
    clean_data.main()
    generate_insights.main()
    print("Phase 1 Complete. Dashboard data is ready!")

if __name__ == "__main__":
    main()