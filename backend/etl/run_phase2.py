import load_to_supabase
import export_queries

def main():
    print("--- PHASE 2: Push to Supabase & Export Queries ---")
    load_to_supabase.main()
    export_queries.main()
    print("Phase 2 Complete. SQL Queries are updated!")

if __name__ == "__main__":
    main()