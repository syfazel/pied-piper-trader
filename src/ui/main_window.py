# src/ui/main_window.py
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QPushButton, QLabel, QTabWidget, QTextEdit, QSplitter, 
                               QLineEdit, QMessageBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from src.ui.worker import AnalysisWorker
from src.ui.widgets import NewsMonitorWidget, DataMatrixWidget, AdvancedChartWidget, AIPerformanceWidget
from src.reporting.scientific import ScientificReporter 

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pied Piper Next-Gen (Stable Core)")
        self.resize(1400, 950)
        
        self.setStyleSheet("""
            QMainWindow { background-color: #121212; color: white; font-family: 'Segoe UI'; }
            QTabWidget::pane { border: 1px solid #333; background: #121212; }
            QTabBar::tab { background: #1E1E1E; color: #AAA; padding: 12px 25px; margin-right: 2px; border-top-left-radius: 4px; border-top-right-radius: 4px; }
            QTabBar::tab:selected { background: #2962FF; color: white; font-weight: bold; border-bottom: 2px solid #2962FF; }
            QTabBar::tab:hover { background: #333; }
            QSplitter::handle { background-color: #333; }
            QTextEdit { background-color: #0F0F0F; color: #00E676; border: 1px solid #333; border-radius: 5px; padding: 10px; }
            QLineEdit { background-color: #1E1E1E; color: white; border: 1px solid #444; padding: 5px; border-radius: 4px; font-weight: bold;}
        """)

        # --- FIX: حذف تایمر QTimer (چون Worker خودش لوپ دارد) ---
        self.worker = None 

        self.setup_ui()

    def setup_ui(self):
        # ... (همان کدهای UI قبلی بدون تغییر) ...
        # (برای خلاصه شدن کد، فقط بخش‌های تغییر یافته را می‌نویسم)
        
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        header = QHBoxLayout()
        title = QLabel("ALGO TRADER")
        title.setStyleSheet("color: #2962FF; font-weight: 900; font-size: 18px; margin-right: 10px;")
        self.input_symbol = QLineEdit("ETHTMN")
        self.input_symbol.setFixedWidth(100)
        self.input_symbol.setAlignment(Qt.AlignCenter)
        
        # دکمه تغییر کرده است
        self.btn_run = QPushButton("🚀 START SYSTEM") 
        self.btn_run.setCursor(Qt.PointingHandCursor)
        self.btn_run.setCheckable(True)
        self.btn_run.setStyleSheet("""
            QPushButton { background-color: #2962FF; color: white; padding: 10px 25px; font-weight: bold; border-radius: 5px; border: none; font-size: 13px; }
            QPushButton:hover { background-color: #1E88E5; }
            QPushButton:checked { background-color: #D32F2F; } 
        """)
        self.btn_run.clicked.connect(self.toggle_system) # اتصال به متد جدید
        
        # ... (بقیه دکمه‌ها و لیبل‌ها مثل قبل) ...
        self.btn_report = QPushButton("📑 SCI-REPORT")
        self.btn_report.setCursor(Qt.PointingHandCursor)
        self.btn_report.setStyleSheet("QPushButton { background-color: #6C5CE7; color: white; padding: 10px 15px; font-weight: bold; border-radius: 5px; border: none; font-size: 13px; } QPushButton:hover { background-color: #5649B9; }")
        self.btn_report.clicked.connect(self.generate_scientific_report)
        
        self.lbl_status = QLabel("System Ready")
        self.lbl_status.setStyleSheet("color: gray; margin-left: 15px; font-size: 13px;")
        self.lbl_macro = QLabel("Waiting...")
        self.lbl_macro.setStyleSheet("color: #FFD700; font-weight: bold; font-size: 14px;")
        
        header.addWidget(title)
        header.addWidget(self.input_symbol)
        header.addWidget(self.btn_run)
        header.addWidget(self.btn_report)
        header.addWidget(self.lbl_status)
        header.addStretch()
        header.addWidget(self.lbl_macro)
        layout.addLayout(header)

        # تب‌ها (بدون تغییر)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        self.tab_dashboard = QWidget()
        self.setup_dashboard_tab()
        self.tabs.addTab(self.tab_dashboard, "📊 DASHBOARD")

        self.widget_matrix = DataMatrixWidget()
        self.tabs.addTab(self.widget_matrix, "🔢 DATA MATRIX")

        self.widget_news = NewsMonitorWidget()
        self.tabs.addTab(self.widget_news, "🌍 NEWS MONITOR")
        
        self.widget_ai_history = AIPerformanceWidget()
        self.tabs.addTab(self.widget_ai_history, "⚖️ AI VALIDATION")

    def setup_dashboard_tab(self):
        # ... (بدون تغییر) ...
        layout = QVBoxLayout(self.tab_dashboard)
        layout.setContentsMargins(0, 10, 0, 0)
        splitter = QSplitter(Qt.Vertical)
        splitter.setHandleWidth(2)
        self.chart_widget = AdvancedChartWidget()
        splitter.addWidget(self.chart_widget)
        self.report_view = QTextEdit()
        self.report_view.setReadOnly(True)
        self.report_view.setFont(QFont("Consolas", 10))
        self.report_view.setPlaceholderText("Waiting for analysis report...")
        splitter.addWidget(self.report_view)
        splitter.setSizes([700, 300])
        layout.addWidget(splitter)

    def toggle_system(self, checked):
        """مدیریت روشن/خاموش کردن ترد"""
        if checked:
            self.btn_run.setText("⏹ STOP SYSTEM")
            self.btn_run.setStyleSheet("background-color: #D32F2F; color: white; padding: 10px 25px; font-weight: bold; border-radius: 5px; border: none;")
            self.input_symbol.setEnabled(False)
            self.start_worker()
        else:
            self.btn_run.setText("🚀 START SYSTEM")
            self.btn_run.setStyleSheet("background-color: #2962FF; color: white; padding: 10px 25px; font-weight: bold; border-radius: 5px; border: none;")
            self.input_symbol.setEnabled(True)
            self.stop_worker()

    def start_worker(self):
        symbol = self.input_symbol.text().upper()
        self.worker = AnalysisWorker(symbol)
        
        # اتصال سیگنال‌های جدید
        self.worker.log.connect(self.update_status)
        self.worker.error.connect(self.on_error)
        self.worker.data_ready.connect(self.on_data_ready) # <--- سیگنال اصلی
        
        self.worker.start()

    def stop_worker(self):
        if self.worker:
            self.lbl_status.setText("Stopping...")
            self.worker.stop()
            self.worker.wait() # صبر تا ترد کامل بسته شود
            self.lbl_status.setText("System Stopped")

    def update_status(self, msg):
        self.lbl_status.setText(msg)

    def on_error(self, err):
        # فقط ارور را نشان بده اما دکمه را خاموش نکن (چون ورکر خودش تلاش مجدد می‌کند)
        self.lbl_status.setText(f"⚠️ {err}")
        self.lbl_status.setStyleSheet("color: #FF5252;")

    def on_data_ready(self, result):
        """دریافت داده از حلقه ورکر"""
        self.lbl_status.setText("✅ Live Monitoring")
        self.lbl_status.setStyleSheet("color: #00E676;")
        
        # آپدیت تمام بخش‌ها (مثل قبل)
        macro = result.get('macro', {})
        usdt = macro.get('USDT_IRT', 0)
        gold = macro.get('GOLD_IRT', 0)
        if usdt > 0:
            self.lbl_macro.setText(f"🇺🇸 USDT: {usdt:,.0f} T | 🏆 GOLD: {gold:,.0f} T")
        
        if 'dataframe' in result:
            self.chart_widget.plot(result['dataframe'])
            self.widget_matrix.update_data(result['dataframe'])
        
        if 'report' in result:
            self.report_view.setText(result['report'])
        
        if 'sentiment' in result:
            sentiment_data = result['sentiment']
            if 'news_list' in sentiment_data and sentiment_data['news_list']:
                self.widget_news.update_news(sentiment_data['news_list'])
                
        if 'history' in result:
            hist = result['history']
            self.widget_ai_history.update_history(hist['df'], hist['accuracy'])

    def generate_scientific_report(self):
        # ... (بدون تغییر) ...
        reporter = ScientificReporter()
        filename, content = reporter.generate_full_report()
        if content == "Error":
            QMessageBox.critical(self, "Report Error", filename)
        elif content == "Empty":
            QMessageBox.warning(self, "No Data", "No trading history found.")
        else:
            msg = QMessageBox()
            msg.setWindowTitle("Scientific Report Generated")
            msg.setText(f"Report saved successfully!\n\nFile: {filename}")
            msg.setIcon(QMessageBox.Information)
            msg.exec()
            try:
                import os
                os.startfile(filename)
            except: pass

if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    app.setStyle("Fusion") 
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())