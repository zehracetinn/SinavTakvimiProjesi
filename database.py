import sqlite3

def create_database():
    conn = sqlite3.connect("sinav_takvimi.db")
    cursor = conn.cursor()

    # Bölümler tablosu
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Bolumler (
        bolum_id INTEGER PRIMARY KEY AUTOINCREMENT,
        bolum_adi TEXT UNIQUE NOT NULL
    );
    """)

    # Kullanıcılar tablosu
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Kullanicilar (
        kullanici_id INTEGER PRIMARY KEY AUTOINCREMENT,
        eposta TEXT UNIQUE NOT NULL,
        sifre TEXT NOT NULL,
        rol TEXT CHECK(rol IN ('Admin', 'Bölüm Koordinatörü')) NOT NULL,
        bolum_id INTEGER,
        FOREIGN KEY(bolum_id) REFERENCES Bolumler(bolum_id)
    );
    """)

    # Derslikler tablosu
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Derslikler (
        derslik_id INTEGER PRIMARY KEY AUTOINCREMENT,
        derslik_kodu TEXT NOT NULL,
        derslik_adi TEXT NOT NULL,
        kapasite INTEGER NOT NULL,
        sira_sayisi INTEGER,
        sutun_sayisi INTEGER,
        bolum_id INTEGER,
        FOREIGN KEY(bolum_id) REFERENCES Bolumler(bolum_id)
    );
    """)

    # Dersler tablosu
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Dersler (
        ders_id INTEGER PRIMARY KEY AUTOINCREMENT,
        ders_kodu TEXT NOT NULL,
        ders_adi TEXT NOT NULL,
        ogretim_uyesi TEXT,
        sinif INTEGER,
        yapi TEXT CHECK(yapi IN ('Zorunlu', 'Seçmeli')),
        bolum_id INTEGER,
        FOREIGN KEY(bolum_id) REFERENCES Bolumler(bolum_id)
    );
    """)

    # Öğrenciler tablosu
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Ogrenciler (
        ogrenci_id INTEGER PRIMARY KEY AUTOINCREMENT,
        ogrenci_no TEXT UNIQUE NOT NULL,
        ad_soyad TEXT NOT NULL
    );
    """)

    # Öğrenci - Ders eşleşmeleri
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Ogrenci_Ders_Kayitlari (
        kayit_id INTEGER PRIMARY KEY AUTOINCREMENT,
        ogrenci_id INTEGER,
        ders_id INTEGER,
        FOREIGN KEY(ogrenci_id) REFERENCES Ogrenciler(ogrenci_id),
        FOREIGN KEY(ders_id) REFERENCES Dersler(ders_id)
    );
    """)

    # Varsayılan admin ekleme
    cursor.execute("""
    INSERT OR IGNORE INTO Kullanicilar (eposta, sifre, rol)
    VALUES ('admin@kocaeli.edu.tr', 'admin123', 'Admin');
    """)

    conn.commit()
    conn.close()
    print("✅ Veritabanı başarıyla oluşturuldu!")

if __name__ == "__main__":
    create_database()

