import fetch_data 
import clean_data 
import load_to_mysql 

def main():
    fetch_data.main()
    clean_data.main()
    load_to_mysql.main()

if __name__ == "__main__":
    main()
