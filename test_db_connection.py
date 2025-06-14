#!/usr/bin/env python
"""
Test script to verify connection to PostgreSQL database.
"""
import os
import sys
import psycopg2
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get database connection parameters from environment variables
DB_NAME = os.getenv('DB_NAME', 'reservehub')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'Bhargav@2002')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')

def test_connection():
    """Attempt to connect to the PostgreSQL database and print result."""
    print(f"Attempting to connect to PostgreSQL at {DB_HOST}:{DB_PORT}...")
    
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        
        # Create a cursor
        cur = conn.cursor()
        
        # Check connection by executing a simple query
        cur.execute('SELECT version();')
        version = cur.fetchone()
        
        print("\nConnection successful!")
        print(f"PostgreSQL server version: {version[0]}")
        
        # List all tables
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        tables = cur.fetchall()
        
        if tables:
            print("\nTables in database:")
            for table in tables:
                print(f"  - {table[0]}")
        else:
            print("\nNo tables found in database.")
        
        cur.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"\nConnection failed: {e}")
        
        # Print troubleshooting suggestions
        print("\nTroubleshooting suggestions:")
        print("1. Ensure PostgreSQL is installed and running on your machine")
        print("2. Verify the database credentials in your .env file")
        print("3. Check that PostgreSQL is accepting connections on port 5432")
        print("4. Make sure any firewall allows connections to PostgreSQL")
        print("5. Verify that the database 'reservehub' exists")
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)