import sqlite3
from PyQt6 import QtGui, QtWidgets


from PyQt6.QtWidgets import (
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QSpinBox,
    QComboBox,
)
from PyQt6.QtCore import Qt
import sys, traceback


def excepthook(type, value, tb):
    print("".join(traceback.format_exception(type, value, tb)))
    sys.__excepthook__(type, value, tb)


sys.excepthook = excepthook
def fade_image(pixmap, opacity=0.1, blur_radius=8):
    """Resmi silikleştirip hafif blur uygular"""
    img = QtGui.QImage(pixmap.size(), QtGui.QImage.Format.Format_ARGB32)
    img.fill(QtGui.QColor(255, 255, 255, 0))
    painter = QtGui.QPainter(img)
    painter.setOpacity(opacity)
    painter.drawPixmap(0, 0, pixmap)
    painter.end()

    # 🔹 Blur efekti (Qt6 uyumlu)
    blur = QtWidgets.QGraphicsBlurEffect()
    blur.setBlurRadius(blur_radius)
    scene = QtWidgets.QGraphicsScene()
    item = QtWidgets.QGraphicsPixmapItem(QtGui.QPixmap.fromImage(img))
    item.setGraphicsEffect(blur)
    scene.addItem(item)

    result = QtGui.QImage(img.size(), QtGui.QImage.Format.Format_ARGB32)
    result.fill(QtGui.QColor(255, 255, 255, 0))
    painter = QtGui.QPainter(result)
    scene.render(painter)
    painter.end()
    return QtGui.QPixmap.fromImage(result)



class DerslikWindow(QWidget):
    def __init__(self, bolum_id):
        super().__init__()
        self.bolum_id = bolum_id
        self.setWindowTitle("🏫 Derslik Yönetimi")
        self.setGeometry(450, 200, 800, 500)
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        title = QLabel("Derslik Yönetimi")
        title.setObjectName("titleLabel")
        bolum_label = QLabel(f"Bölüm ID: {self.bolum_id}")
        bolum_label.setObjectName("subLabel")
        bolum_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bolum_label.setStyleSheet("font-size:14px; color:#555; margin-bottom:8px;")

        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size:18px; font-weight:bold;")

        # Derslik Bilgi Girişi
        self.kod_input = QLineEdit()
        self.kod_input.setPlaceholderText("Derslik Kodu (örnek: B101)")

        self.ad_input = QLineEdit()
        self.ad_input.setPlaceholderText("Derslik Adı (örnek: Yazılım Lab 1)")

        self.kapasite_input = QSpinBox()
        self.kapasite_input.setRange(1, 300)
        self.kapasite_input.setPrefix("Kapasite: ")

        self.sira_input = QSpinBox()
        self.sira_input.setRange(1, 30)
        self.sira_input.setPrefix("Boyuna sıra: ")

        self.sutun_input = QSpinBox()
        self.sutun_input.setRange(1, 30)
        self.sutun_input.setPrefix("Enine sıra: ")

        self.duzen_box = QComboBox()
        self.duzen_box.addItems(["2'li", "3'lü"])

        # Butonlar
        self.add_btn = QPushButton("➕ Ekle / Güncelle")
        self.add_btn.setStyleSheet(
            "background-color:#27ae60; color:white; font-weight:bold;"
        )
        self.add_btn.clicked.connect(self.add_or_update_derslik)

        self.del_btn = QPushButton("🗑️ Sil")
        self.del_btn.setObjectName("deleteBtn")
        self.del_btn.setStyleSheet(
            "background-color:#c0392b; color:white; font-weight:bold;"
        )
        self.del_btn.clicked.connect(self.delete_derslik)

        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Kodu", "Adı", "Kapasite", "Sıra", "Sütun", "Düzen"]
        )

        self.table.cellClicked.connect(self.select_row)

        # Layout
        form_layout = QVBoxLayout()
        form_layout.addWidget(title)
        form_layout.addWidget(bolum_label)
        form_layout.addWidget(self.kod_input)
        form_layout.addWidget(self.ad_input)
        form_layout.addWidget(self.kapasite_input)
        form_layout.addWidget(self.sira_input)
        form_layout.addWidget(self.sutun_input)
        form_layout.addWidget(self.duzen_box)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Derslik kodu veya ID ara...")

        self.search_btn = QPushButton("🔍 Ara")
        self.search_btn.setObjectName("searchBtn") 

        self.search_btn.setStyleSheet(
            "background-color:#2980b9; color:white; font-weight:bold;"
        )
        self.search_btn.clicked.connect(self.search_derslik)
        search_layout = QHBoxLayout()
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_btn)
        form_layout.addLayout(search_layout)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.del_btn)

        form_layout.addLayout(btn_layout)
        form_layout.addWidget(self.table)
        self.setLayout(form_layout)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setDefaultSectionSize(120)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(False)
        self.table.setShowGrid(True)
        # --- Arka plan resmi ekleme ---
        background = QtGui.QPixmap("kou.jpg")
        background = background.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation
        )
        background = fade_image(background, opacity=0.15)  # 💡 silikleştir

        palette = self.palette()
        palette.setBrush(self.backgroundRole(), QtGui.QBrush(background))
        self.setPalette(palette)
        self.setAutoFillBackground(True)

        # === GLOBAL THEME (KOU tarzı) ===
        self.setStyleSheet(
            """
           
    
        QWidget {
            background: #f2f4f7;
            font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
            font-size: 14px;
            color: #1d2939;
    }

         /* Başlıklar */
         QLabel#titleLabel {
             font-size: 24px;
            font-weight: 700;
            color: #1f4d2c; /* koyu yeşil ton */
            letter-spacing: 0.2px;
    }
    QLabel#subLabel {
        font-size: 14px;
        color: #667085;
    }

    /* Metin girişleri */
    QLineEdit, QSpinBox, QComboBox {
        background: #ffffff;
        border: 1px solid #d0d5dd;
        border-radius: 8px;
        padding: 8px 10px;
        min-height: 34px;
    }
    QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
        border: 1px solid #2e7d32; /* ana yeşil */
        box-shadow: none;
    }

    /* Butonlar – temel */
    QPushButton {
        background: #2e7d32;      /* ana yeşil */
        color: #ffffff;
        font-weight: 600;
        border: none;
        border-radius: 10px;
        padding: 8px 14px;
        min-height: 36px;
    }
    QPushButton:hover {
        background: #256a29;
    }
    QPushButton:disabled {
        background: #a6b8a7;
        color: #eef3ee;
    }

    /* Ara butonu – ikincil/düz renk */
    QPushButton#searchBtn {
        background: #1f4d2c;   /* daha koyu yeşil */
    }
    QPushButton#searchBtn:hover {
        background: #183f24;
    }

    /* Sil butonu – uyarı */
    QPushButton#deleteBtn {
        background: #b42318;  /* kırmızı */
    }
    QPushButton#deleteBtn:hover {
        background: #9a1e16;
    }

    /* Tablo */
    QTableWidget {
        background: #ffffff;
        border: 1px solid #d0d5dd;
        border-radius: 10px;
        gridline-color: #e4e7ec;
    }
    QHeaderView::section {
        background: #2e7d32;
        color: white;
        font-weight: 700;
        padding: 8px;
        border: none;
    }
    QTableWidget::item {
        padding: 6px;
    }
""")
      


        

    def load_data(self):
        conn = sqlite3.connect("sinav_takvimi.db")
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT derslik_id, derslik_kodu, derslik_adi, kapasite, sira_sayisi, sutun_sayisi, duzen_tipi
            FROM Derslikler
            WHERE bolum_id = ?
        """,
            (self.bolum_id,),
        )

        data = cursor.fetchall()
        conn.close()

        self.table.setRowCount(len(data))
        for row_idx, row_data in enumerate(data):
            for col_idx, col_data in enumerate(row_data):
                self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(col_data)))

    def add_or_update_derslik(self):
        kod = self.kod_input.text().strip()
        ad = self.ad_input.text().strip()
        kapasite = self.kapasite_input.value()
        sira = self.sira_input.value()
        sutun = self.sutun_input.value()

        if not kod or not ad:
            QMessageBox.warning(self, "Uyarı", "Lütfen tüm alanları doldurun.")
            return

        conn = sqlite3.connect("sinav_takvimi.db")
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT derslik_id FROM Derslikler WHERE derslik_kodu = ? AND bolum_id = ?
        """,
            (kod, self.bolum_id),
        )
        existing = cursor.fetchone()

        if existing:
            duzen_tipi = self.duzen_box.currentText()
            cursor.execute(
                """
                UPDATE Derslikler
                SET derslik_adi = ?, kapasite = ?, sira_sayisi = ?, sutun_sayisi = ?, duzen_tipi = ?
                WHERE derslik_kodu = ? AND bolum_id = ?
            """,
                (ad, kapasite, sira, sutun, duzen_tipi, kod, self.bolum_id),
            )
            QMessageBox.information(self, "Güncellendi", f"{kod} güncellendi.")
        else:
            duzen_tipi = self.duzen_box.currentText()
            cursor.execute(
                """
                INSERT INTO Derslikler (derslik_kodu, derslik_adi, kapasite, sira_sayisi, sutun_sayisi, duzen_tipi, bolum_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (kod, ad, kapasite, sira, sutun, duzen_tipi, self.bolum_id),
            )
            QMessageBox.information(self, "Eklendi", f"{kod} başarıyla eklendi.")

        conn.commit()
        conn.close()
        self.load_data()

    def delete_derslik(self):
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Uyarı", "Silmek için bir satır seçin.")
            return

        derslik_id = self.table.item(selected, 0).text()

        conn = sqlite3.connect("sinav_takvimi.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Derslikler WHERE derslik_id = ?", (derslik_id,))
        conn.commit()
        conn.close()

        QMessageBox.information(self, "Silindi", "Derslik başarıyla silindi.")
        self.load_data()

    def select_row(self, row, col):

        try:
            self.kod_input.setText(self.table.item(row, 1).text())
            self.ad_input.setText(self.table.item(row, 2).text())
            self.kapasite_input.setValue(int(self.table.item(row, 3).text()))
            self.sira_input.setValue(int(self.table.item(row, 4).text()))
            self.sutun_input.setValue(int(self.table.item(row, 5).text()))
            duzen = self.table.item(row, 6)
            if duzen:
                ix = self.duzen_box.findText(duzen.text())
                if ix >= 0:
                    self.duzen_box.setCurrentIndex(ix)
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Satır seçme hatası:\n{e}")

    def search_derslik(self):
        print("arama yapılıyor ...")
        text = self.search_input.text().strip()
        if not text:
            self.load_data()
            return

        conn = sqlite3.connect("sinav_takvimi.db")
        cursor = conn.cursor()

        # Arama sorgusunu derslik adı ve ID'yi daha güvenilir bir şekilde arayacak şekilde güncelledik.
        query = """
            SELECT derslik_id, derslik_kodu, derslik_adi, kapasite, sira_sayisi, sutun_sayisi, duzen_tipi
            FROM Derslikler
            WHERE (derslik_kodu LIKE ? OR derslik_adi LIKE ? OR derslik_id || '' LIKE ?) AND bolum_id = ?
        """

        # Sorgudaki '?' sayısı arttığı için parametreleri de güncelledik.
        search_term = f"%{text}%"
        cursor.execute(query, (search_term, search_term, search_term, self.bolum_id))

        data = cursor.fetchall()
        conn.close()

        self.table.setRowCount(len(data))
        for row_idx, row_data in enumerate(data):
            for col_idx, col_data in enumerate(row_data):
                self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(col_data)))
                

    def resizeEvent(self, event):
        background = QtGui.QPixmap("kou.jpg")
        background = background.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation
    )
        background = fade_image(background, opacity=0.1, blur_radius=10)
        palette = self.palette()
        palette.setBrush(self.backgroundRole(), QtGui.QBrush(background))
        self.setPalette(palette)
        self.setAutoFillBackground(True)
        super().resizeEvent(event)


