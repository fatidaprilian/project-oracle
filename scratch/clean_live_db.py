import os
import psycopg
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

def clean_live_database():
    dsn = os.getenv("ORACLE_POSTGRES_DSN")
    
    if not dsn:
        print("❌ Error: ORACLE_POSTGRES_DSN tidak ditemukan di .env")
        return

    print(f"🔗 Menghubungkan ke database...")
    
    try:
        with psycopg.connect(dsn) as conn:
            with conn.cursor() as cur:
                print("🧹 Menghapus data signal_history...")
                cur.execute("TRUNCATE TABLE signal_history CASCADE;")
                
                print("🧹 Menghapus data active_tracking...")
                cur.execute("TRUNCATE TABLE active_tracking CASCADE;")
                
                print("🧹 Menghapus data ignore_list...")
                cur.execute("TRUNCATE TABLE ignore_list CASCADE;")
                
                print("🧹 Menghapus data tracking_alerts...")
                cur.execute("TRUNCATE TABLE tracking_alerts CASCADE;")
                
                conn.commit()
                print("✅ Database live berhasil dibersihkan! (Watchlist tetap aman)")
    except Exception as e:
        print(f"❌ Gagal membersihkan database: {e}")

if __name__ == "__main__":
    confirm = input("⚠️  APAKAH ANDA YAKIN ingin menghapus semua data transaksi/analisa di LIVE DB? (y/n): ")
    if confirm.lower() == 'y':
        clean_live_database()
    else:
        print("🚫 Operasi dibatalkan.")
