# src/ui/widgets.py
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, 
                               QHeaderView, QListWidget, QListWidgetItem, QLabel)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
import pyqtgraph as pg
import pandas as pd

class NewsMonitorWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        self.lbl_title = QLabel("📡 LIVE NEWS FEED (CoinTelegraph RSS)")
        self.lbl_title.setStyleSheet("color: #AAA; font-weight: bold; margin-bottom: 5px;")
        layout.addWidget(self.lbl_title)
        self.news_list = QListWidget()
        self.news_list.setStyleSheet("""
            QListWidget { background-color: #1E1E1E; border: 1px solid #333; border-radius: 5px; }
            QListWidget::item { padding: 10px; border-bottom: 1px solid #2A2A2A; }
        """)
        layout.addWidget(self.news_list)

    def update_news(self, news_data):
        self.news_list.clear()
        for item in news_data:
            text = f"{item.get('time', '')} | {item.get('source', '')}\n{item.get('title', '')}"
            list_item = QListWidgetItem(text)
            list_item.setFont(QFont("Segoe UI", 10))
            
            sentiment = item.get('sentiment', 'neutral')
            if sentiment == 'positive': list_item.setForeground(QColor("#00E676"))
            elif sentiment == 'negative': list_item.setForeground(QColor("#FF5252"))
            else: list_item.setForeground(QColor("#DDDDDD"))
                
            self.news_list.addItem(list_item)

class DataMatrixWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        self.table = QTableWidget()
        self.table.setStyleSheet("""
            QTableWidget { background-color: #1E1E1E; gridline-color: #333; color: #DDD; border: none; }
            QHeaderView::section { background-color: #252525; color: #AAA; padding: 5px; }
        """)
        layout.addWidget(self.table)

    def update_data(self, df):
        if df is None or df.empty: return
        
        # ستون‌هایی که می‌خواهیم نمایش دهیم
        cols_to_show = ['close', 'rsi', 'macd_hist', 'sma_50', 'obv', 'atr']
        valid_cols = [c for c in cols_to_show if c in df.columns]
        
        self.table.setColumnCount(len(valid_cols))
        self.table.setHorizontalHeaderLabels([c.upper() for c in valid_cols])
        self.table.setRowCount(len(df))
        
        for i in range(len(df)):
            row_idx = len(df) - 1 - i
            row_data = df.iloc[row_idx]
            for j, col in enumerate(valid_cols):
                val = row_data[col]
                # فرمت دهی زیبا برای اعداد بزرگ (تومان)
                if col in ['close', 'obv', 'sma_50']:
                    text = f"{val:,.0f}"
                else:
                    text = f"{val:.2f}"
                
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(i, j, item)
        
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

class AdvancedChartWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        self.win = pg.GraphicsLayoutWidget()
        self.win.setBackground('#1E1E1E')
        layout.addWidget(self.win)
        
        # Price Chart
        self.p_price = self.win.addPlot(row=0, col=0)
        self.p_price.showGrid(x=True, y=True, alpha=0.2)
        self.p_price.setLabel('left', 'Price (TMN)')
        
        # RSI Chart
        self.p_rsi = self.win.addPlot(row=1, col=0)
        self.p_rsi.setMaximumHeight(150)
        self.p_rsi.showGrid(x=True, y=True, alpha=0.2)
        self.p_rsi.setLabel('left', 'RSI')
        self.p_rsi.setXLink(self.p_price)

    def plot(self, df):
        self.p_price.clear()
        self.p_rsi.clear()
        
        if df is None or df.empty: return
        
        # رسم خطوط RSI
        self.p_rsi.addItem(pg.InfiniteLine(pos=70, angle=0, pen=pg.mkPen('#FF5252', style=Qt.DashLine)))
        self.p_rsi.addItem(pg.InfiniteLine(pos=30, angle=0, pen=pg.mkPen('#00E676', style=Qt.DashLine)))

        # رسم نمودار قیمت (فقط 100 کندل آخر برای سرعت)
        plot_data = df.tail(100)
        self.p_price.plot(plot_data['close'].values, pen=pg.mkPen('c', width=2))
        
        if 'bb_upper' in plot_data.columns:
            self.p_price.plot(plot_data['bb_upper'].values, pen=pg.mkPen('#555'))
            self.p_price.plot(plot_data['bb_lower'].values, pen=pg.mkPen('#555'))
            
        if 'rsi' in plot_data.columns:
            self.p_rsi.plot(plot_data['rsi'].values, pen=pg.mkPen('#FFD700', width=2))

class AIPerformanceWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        self.lbl_stats = QLabel("🎯 AI ACCURACY: Calculating...")
        self.lbl_stats.setStyleSheet("color: #FFD700; font-size: 16px; font-weight: bold; margin: 10px;")
        layout.addWidget(self.lbl_stats)
        self.table = QTableWidget()
        self.table.setStyleSheet("""
            QTableWidget { background-color: #1E1E1E; gridline-color: #333; color: #DDD; border: none; }
            QHeaderView::section { background-color: #252525; color: #AAA; padding: 5px; }
        """)
        cols = ["Time", "Signal", "Entry Price", "Status", "Current"]
        self.table.setColumnCount(len(cols))
        self.table.setHorizontalHeaderLabels(cols)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)

    def update_history(self, df, accuracy):
        self.lbl_stats.setText(f"🎯 AI ACCURACY: {accuracy:.1f}%")
        self.table.setRowCount(len(df))
        for i in range(len(df)):
            row_idx = len(df) - 1 - i
            row_data = df.iloc[row_idx]
            self.table.setItem(i, 0, QTableWidgetItem(str(row_data['timestamp'])))
            
            sig_text = f"{row_data['predicted_direction']} ({row_data['confidence']})"
            sig_item = QTableWidgetItem(sig_text)
            sig_item.setForeground(QColor("#00E676") if row_data['predicted_direction'] == "BUY" else QColor("#FF5252"))
            self.table.setItem(i, 1, sig_item)
            
            self.table.setItem(i, 2, QTableWidgetItem(f"{row_data['entry_price']:,.0f}"))
            
            status = row_data['status']
            stat_item = QTableWidgetItem(status)
            if status == "CORRECT": stat_item.setForeground(QColor("#00E676"))
            elif status == "WRONG": stat_item.setForeground(QColor("#FF5252"))
            else: stat_item.setForeground(QColor("#FFD700"))
            self.table.setItem(i, 3, stat_item)
            
            self.table.setItem(i, 4, QTableWidgetItem(f"{row_data['actual_result']:,.0f}"))