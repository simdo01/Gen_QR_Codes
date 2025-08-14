import sys
import os
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QTextEdit, QPushButton, QVBoxLayout, QHBoxLayout, QFileDialog, QFrame
)
from PySide6.QtGui import QPixmap, QPainter, QFont, QPalette, QColor
from PySide6.QtCore import Qt
import qrcode
from io import BytesIO

# Helper to load styles.qss from the same directory as this script or from resources

def resource_path(relative_path):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Try resources directory first
    resources_dir = os.path.join(script_dir, "resources")
    qss_path = os.path.join(resources_dir, relative_path)
    if os.path.exists(qss_path):
        return qss_path
    # Fallback to script directory
    return os.path.join(script_dir, relative_path)

class CustomTitleBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(60)
        self.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 8px 8px 0px 0px;
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 10, 20, 10)
        
        # Title
        self.title_label = QLabel("QR Code Generator")
        self.title_label.setObjectName("headerTitle")
        self.title_label.setStyleSheet("""
            QLabel {
                color: black;
                font-size: 24px;
                font-weight: bold;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """)
        layout.addWidget(self.title_label)
        layout.addStretch()
        
        # Exit button
        self.exit_btn = QPushButton("✕")
        self.exit_btn.setFixedSize(32, 32)
        self.exit_btn.setStyleSheet("""
            QPushButton {
                border: none;
                background: rgba(255, 255, 255, 0.2);
                border-radius: 16px;
                color: white;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.3);
            }
            QPushButton:pressed {
                background: rgba(255, 255, 255, 0.4);
            }
        """)
        self.exit_btn.clicked.connect(self.close_app)
        layout.addWidget(self.exit_btn)
        
        # For dragging
        self._drag_active = False
        self._drag_pos = None

    def close_app(self):
        self.window().close()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_active = True
            self._drag_pos = event.globalPosition().toPoint() - self.window().frameGeometry().topLeft()
            event.accept()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_active and event.buttons() & Qt.LeftButton:
            self.window().move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_active = False
        super().mouseReleaseEvent(event)

class QRCodeApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("")  # Hide system title bar text
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
        self.setMinimumWidth(500)
        self.setMinimumHeight(900)
        self.setStyleSheet("""
            QWidget {
                background-color: #f5f5f5;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 20)
        main_layout.setSpacing(0)

        # Custom title bar
        self.title_bar = CustomTitleBar(self)
        main_layout.addWidget(self.title_bar)

        # Main content area with padding
        content_widget = QWidget()
        content_widget.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 0px 0px 8px 8px;
            }
        """)
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(30, 15, 30, 30)
        content_layout.setSpacing(15)
        main_layout.addWidget(content_widget)

        # Message input section
        input_frame = QFrame()
        input_frame.setStyleSheet("""
            QFrame {
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                background-color: white;
            }
            QFrame:focus-within {
                border-color: #4a90e2;
            }
        """)
        input_layout = QVBoxLayout(input_frame)
        input_layout.setContentsMargins(15, 15, 15, 15)
        input_layout.setSpacing(8)
        
        self.message_label = QLabel("Enter your message or URL:")
        self.message_label.setStyleSheet("""
            QLabel {
                font-weight: bold;
                font-size: 14px;
                color: #333;
                margin-bottom: 5px;
            }
        """)
        input_layout.addWidget(self.message_label)
        
        self.message_input = QTextEdit()
        self.message_input.setPlaceholderText("Type your message here...")
        self.message_input.setMaximumHeight(100)
        self.message_input.setStyleSheet("""
            QTextEdit {
                border: none;
                background-color: transparent;
                font-size: 13px;
                color: #333;
                selection-background-color: #4a90e2;
            }
            QTextEdit:focus {
                outline: none;
            }
        """)
        input_layout.addWidget(self.message_input)
        content_layout.addWidget(input_frame)

        # Generate button
        self.generate_btn = QPushButton("Generate QR Code")
        self.generate_btn.setFixedSize(180, 40)
        self.generate_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4a90e2, stop:1 #357abd);
                border: none;
                border-radius: 8px;
                color: white;
                font-size: 14px;
                font-weight: bold;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #357abd, stop:1 #2d6da3);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2d6da3, stop:1 #245a8f);
            }
            QPushButton:disabled {
                background: #cccccc;
                color: #666666;
            }
        """)
        self.generate_btn.clicked.connect(self.generate_qr)
        generate_layout = QHBoxLayout()
        generate_layout.addStretch()
        generate_layout.addWidget(self.generate_btn)
        generate_layout.addStretch()
        content_layout.addLayout(generate_layout)

        # QR code preview section
        preview_frame = QFrame()
        preview_frame.setStyleSheet("""
            QFrame {
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                background-color: white;
            }
        """)
        preview_layout = QVBoxLayout(preview_frame)
        preview_layout.setContentsMargins(15, 40, 20, 40)
        preview_layout.setSpacing(10)
        
        preview_label = QLabel("QR Code Preview")
        preview_label.setStyleSheet("""
            QLabel {
                font-weight: bold;
                font-size: 14px;
                color: #333;
                text-align: center;
            }
        """)
        preview_label.setAlignment(Qt.AlignCenter)
        preview_layout.addWidget(preview_label)
        
        self.qr_label = QLabel()
        self.qr_label.setAlignment(Qt.AlignCenter)
        self.qr_label.setFixedSize(300, 300)
        self.qr_label.setStyleSheet("""
            QLabel {
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                background-color: white;
            }
        """)
        preview_layout.addWidget(self.qr_label, alignment=Qt.AlignCenter)
        content_layout.addWidget(preview_frame)

        # Save button
        self.save_btn = QPushButton("Save QR Code")
        self.save_btn.setFixedSize(180, 40)
        self.save_btn.setEnabled(False)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #28a745, stop:1 #218838);
                border: none;
                border-radius: 8px;
                color: white;
                font-size: 14px;
                font-weight: bold;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #218838, stop:1 #1e7e34);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1e7e34, stop:1 #1c7430);
            }
            QPushButton:disabled {
                background: #cccccc;
                color: #666666;
            }
        """)
        self.save_btn.clicked.connect(self.save_png)
        save_layout = QHBoxLayout()
        save_layout.addStretch()
        save_layout.addWidget(self.save_btn)
        save_layout.addStretch()
        content_layout.addLayout(save_layout)

        # Exit button
        self.exit_btn = QPushButton("Exit")
        self.exit_btn.setFixedSize(180, 40)
        self.exit_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #dc3545, stop:1 #c82333);
                border: none;
                border-radius: 8px;
                color: white;
                font-size: 14px;
                font-weight: bold;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #c82333, stop:1 #a71e2a);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #a71e2a, stop:1 #8c1a24);
            }
        """)
        self.exit_btn.clicked.connect(self.close)
        exit_layout = QHBoxLayout()
        exit_layout.addStretch()
        exit_layout.addWidget(self.exit_btn)
        exit_layout.addStretch()
        content_layout.addLayout(exit_layout)

        # Status message area
        self.status_label = QLabel("Ready to generate QR code")
        self.status_label.setObjectName("messageLabel")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #666;
                font-size: 12px;
                text-align: center;
                padding: 10px;
                background-color: #f8f9fa;
                border-radius: 6px;
                border: 1px solid #e9ecef;
            }
        """)
        self.status_label.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(self.status_label)

        self.qr_img = None

    def generate_qr(self):
        text = self.message_input.toPlainText().strip()
        if not text:
            self.status_label.setText("Please enter a message to generate a QR code.")
            self.status_label.setStyleSheet("""
                QLabel {
                    color: #721c24;
                    font-size: 12px;
                    text-align: center;
                    padding: 10px;
                    background-color: #f8d7da;
                    border-radius: 6px;
                    border: 1px solid #f5c6cb;
                }
            """)
            self.save_btn.setEnabled(False)
            self.qr_label.clear()
            self.qr_img = None
            return
            
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_M,
                box_size=8,
                border=2,
            )
            qr.add_data(text)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
            
            # Convert PIL image to QPixmap
            img_qt = self.pil2pixmap(img)
            if not img_qt or img_qt.isNull():
                self.qr_label.clear()
                self.status_label.setText("Error: Could not display QR code preview.")
                self.status_label.setStyleSheet("""
                    QLabel {
                        color: #721c24;
                        font-size: 12px;
                        text-align: center;
                        padding: 10px;
                        background-color: #f8d7da;
                        border-radius: 6px;
                        border: 1px solid #f5c6cb;
                    }
                """)
                self.save_btn.setEnabled(False)
                self.qr_img = None
                return
                
            self.qr_label.setPixmap(img_qt.scaled(300, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            self.qr_img = img
            self.save_btn.setEnabled(True)
            self.status_label.setText("QR code generated successfully! You can now save it.")
            self.status_label.setStyleSheet("""
                QLabel {
                    color: #155724;
                    font-size: 12px;
                    text-align: center;
                    padding: 10px;
                    background-color: #d4edda;
                    border-radius: 6px;
                    border: 1px solid #c3e6cb;
                }
            """)
        except Exception as e:
            self.status_label.setText(f"Error generating QR code: {str(e)}")
            self.status_label.setStyleSheet("""
                QLabel {
                    color: #721c24;
                    font-size: 12px;
                    text-align: center;
                    padding: 10px;
                    background-color: #f8d7da;
                    border-radius: 6px;
                    border: 1px solid #f5c6cb;
                }
            """)
            self.save_btn.setEnabled(False)
            self.qr_img = None

    def save_png(self):
        if self.qr_img is None:
            return
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Save QR Code", 
            "qr_code.png", 
            "PNG Files (*.png);;All Files (*)"
        )
        if file_path:
            try:
                self.qr_img.save(file_path, "PNG")
                self.status_label.setText(f"QR code saved successfully to: {os.path.basename(file_path)}")
                self.status_label.setStyleSheet("""
                    QLabel {
                        color: #155724;
                        font-size: 12px;
                        text-align: center;
                        padding: 10px;
                        background-color: #d4edda;
                        border-radius: 6px;
                        border: 1px solid #c3e6cb;
                    }
                """)
            except Exception as e:
                self.status_label.setText(f"Error saving file: {str(e)}")
                self.status_label.setStyleSheet("""
                    QLabel {
                        color: #721c24;
                        font-size: 12px;
                        text-align: center;
                        padding: 10px;
                        background-color: #f8d7da;
                        border-radius: 6px;
                        border: 1px solid #f5c6cb;
                    }
                """)

    @staticmethod
    def pil2pixmap(im):
        buf = BytesIO()
        im.save(buf, format="PNG")
        qt_pixmap = QPixmap()
        qt_pixmap.loadFromData(buf.getvalue(), "PNG")
        return qt_pixmap

def main():
    app = QApplication(sys.argv)
    # Load styles.qss for consistent look
    try:
        with open(resource_path("styles.qss")) as f:
            app.setStyleSheet(f.read())
    except Exception:
        pass
    window = QRCodeApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 