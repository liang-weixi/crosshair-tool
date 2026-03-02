import sys
import json
import ctypes
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QSlider, QComboBox,
                             QPushButton, QColorDialog, QGroupBox, QSystemTrayIcon,
                             QMenu, QSpinBox, QCheckBox, QGridLayout, QFrame)
from PyQt5.QtCore import Qt, QPoint, QSettings, QSize
from PyQt5.QtGui import (QPainter, QPen, QColor, QIcon, QFont,
                         QPainterPath, QPixmap, QCursor)

# 确保在高DPI屏幕上正确显示
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except:
    pass


class CrosshairWidget(QWidget):
    """准星显示窗口"""

    def __init__(self):
        super().__init__()
        self.initParams()
        self.setupUI()

    def initParams(self):
        """初始化准星参数"""
        self.line_width = 2
        self.line_length = 20
        self.gap_size = 4
        self.color = QColor(255, 0, 0)  # 红色
        self.style = 0  # 0:十字, 1:十字带点, 2:圆圈
        self.outline = False
        self.outline_color = QColor(0, 0, 0)
        self.opacity = 0.8

    def setupUI(self):
        """设置UI属性"""
        # 设置窗口标志
        self.setWindowFlags(
            Qt.FramelessWindowHint |  # 无边框
            Qt.WindowStaysOnTopHint |  # 置顶
            Qt.Tool |  # 工具窗口，不显示在任务栏
            Qt.X11BypassWindowManagerHint
        )

        # 设置透明背景
        self.setAttribute(Qt.WA_TranslucentBackground)

        # 获取屏幕尺寸
        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(0, 0, screen.width(), screen.height())

        # 默认隐藏
        self.hide()

    def paintEvent(self, event):
        """绘制准星"""
        if not self.isVisible():
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        # 设置透明度
        painter.setOpacity(self.opacity)

        # 获取屏幕中心点
        center = self.rect().center()

        if self.style == 0:  # 十字
            self.drawCrosshair(painter, center)
        elif self.style == 1:  # 十字带中心点
            self.drawCrosshairWithDot(painter, center)
        elif self.style == 2:  # 圆圈
            self.drawCircleCrosshair(painter, center)

    def drawCrosshair(self, painter, center):
        """绘制标准十字"""
        # 绘制外轮廓
        if self.outline:
            outline_pen = QPen(self.outline_color, self.line_width + 2)
            painter.setPen(outline_pen)

            # 水平线轮廓
            painter.drawLine(
                center.x() - self.line_length - self.gap_size - 1,
                center.y(),
                center.x() - self.gap_size + 1,
                center.y()
            )
            painter.drawLine(
                center.x() + self.gap_size - 1,
                center.y(),
                center.x() + self.line_length + self.gap_size + 1,
                center.y()
            )

            # 垂直线轮廓
            painter.drawLine(
                center.x(),
                center.y() - self.line_length - self.gap_size - 1,
                center.x(),
                center.y() - self.gap_size + 1
            )
            painter.drawLine(
                center.x(),
                center.y() + self.gap_size - 1,
                center.x(),
                center.y() + self.line_length + self.gap_size + 1
            )

        # 绘制主要准星
        pen = QPen(self.color, self.line_width)
        painter.setPen(pen)

        # 水平线
        painter.drawLine(
            center.x() - self.line_length - self.gap_size,
            center.y(),
            center.x() - self.gap_size,
            center.y()
        )
        painter.drawLine(
            center.x() + self.gap_size,
            center.y(),
            center.x() + self.line_length + self.gap_size,
            center.y()
        )

        # 垂直线
        painter.drawLine(
            center.x(),
            center.y() - self.line_length - self.gap_size,
            center.x(),
            center.y() - self.gap_size
        )
        painter.drawLine(
            center.x(),
            center.y() + self.gap_size,
            center.x(),
            center.y() + self.line_length + self.gap_size
        )

    def drawCrosshairWithDot(self, painter, center):
        """绘制带中心点的十字"""
        self.drawCrosshair(painter, center)

        # 绘制中心点
        painter.setBrush(QColor(self.color))
        painter.setPen(Qt.NoPen)
        dot_size = self.line_width * 2
        painter.drawEllipse(center, dot_size, dot_size)

    def drawCircleCrosshair(self, painter, center):
        """绘制圆圈准星"""
        # 绘制外轮廓
        if self.outline:
            outline_pen = QPen(self.outline_color, self.line_width + 2)
            painter.setPen(outline_pen)
            painter.setBrush(Qt.NoBrush)
            radius = self.line_length
            painter.drawEllipse(center, radius, radius)

        # 绘制主要圆圈
        pen = QPen(self.color, self.line_width)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        radius = self.line_length
        painter.drawEllipse(center, radius, radius)

        # 绘制十字线（可选）
        if self.gap_size > 0:
            painter.drawLine(
                center.x() - radius, center.y(),
                center.x() - self.gap_size, center.y()
            )
            painter.drawLine(
                center.x() + self.gap_size, center.y(),
                center.x() + radius, center.y()
            )
            painter.drawLine(
                center.x(), center.y() - radius,
                center.x(), center.y() - self.gap_size
            )
            painter.drawLine(
                center.x(), center.y() + self.gap_size,
                center.x(), center.y() + radius
            )


class SettingsWindow(QMainWindow):
    """设置窗口"""

    def __init__(self, crosshair):
        super().__init__()
        self.crosshair = crosshair
        self.settings = QSettings('CrosshairTool', 'Settings')
        self.initUI()
        self.loadSettings()

    def initUI(self):
        """初始化UI"""
        self.setWindowTitle('准星设置')

        # 获取屏幕尺寸并设置自适应窗口大小
        screen = QApplication.primaryScreen().availableGeometry()
        # 窗口宽度为屏幕宽度的30%，但限制在350-500之间
        window_width = min(max(int(screen.width() * 0.3), 350), 500)
        # 窗口高度为屏幕高度的50%，但限制在500-800之间
        window_height = min(max(int(screen.height() * 0.5), 500), 800)
        self.setFixedSize(window_width, window_height)

        # 根据窗口宽度计算基础字体大小和控件大小
        base_font_size = max(int(window_width / 25), 9)  # 基础字体大小
        control_height = max(int(window_height / 25), 25)  # 控件基础高度

        # 设置窗口样式
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: #1e1e2f;
            }}

            /* 所有分组框样式 */
            QGroupBox {{
                font-family: 'Microsoft YaHei', 'Segoe UI', sans-serif;
                font-size: {base_font_size}px;
                font-weight: bold;
                border: 2px solid #3d3d5c;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 12px;
                color: #e0e0e0;
                background-color: #2d2d3f;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px 0 8px;
                color: #b0b0ff;
                background-color: #1e1e2f;
                border-radius: 4px;
            }}

            /* 所有标签样式 */
            QLabel {{
                font-family: 'Microsoft YaHei', 'Segoe UI', sans-serif;
                font-size: {base_font_size}px;
                color: #e0e0e0;
                background: transparent;
                padding: 2px;
            }}

            /* 滑块样式 */
            QSlider::groove:horizontal {{
                height: 4px;
                background: #3d3d5c;
                border-radius: 2px;
            }}
            QSlider::handle:horizontal {{
                background: #7b68ee;
                width: 16px;
                height: 16px;
                margin: -6px 0;
                border-radius: 8px;
            }}
            QSlider::handle:horizontal:hover {{
                background: #9b8aee;
                width: 18px;
                height: 18px;
                margin: -7px 0;
            }}
            QSlider::sub-page:horizontal {{
                background: #7b68ee;
                border-radius: 2px;
            }}

            /* 按钮样式 */
            QPushButton {{
                font-family: 'Microsoft YaHei', 'Segoe UI', sans-serif;
                font-size: {base_font_size}px;
                background-color: #7b68ee;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                min-height: {control_height}px;
                font-weight: normal;
            }}
            QPushButton:hover {{
                background-color: #9b8aee;
            }}
            QPushButton:pressed {{
                background-color: #5a4aaa;
            }}

            /* 颜色按钮特殊样式 */
            QPushButton#colorBtn {{
                background-color: {self.crosshair.color.name()};
                border: 2px solid #7b68ee;
                min-width: {control_height * 2}px;
                max-width: {control_height * 2}px;
                min-height: {control_height}px;
                max-height: {control_height}px;
                padding: 0;
            }}
            QPushButton#colorBtn:hover {{
                border: 2px solid #9b8aee;
            }}

            /* 关闭按钮 */
            QPushButton#closeBtn {{
                background-color: #ff6b6b;
            }}
            QPushButton#closeBtn:hover {{
                background-color: #ff8a8a;
            }}

            /* 保存按钮 */
            QPushButton#saveBtn {{
                background-color: #4ecdc4;
            }}
            QPushButton#saveBtn:hover {{
                background-color: #6edcd3;
            }}

            /* 下拉框样式 */
            QComboBox {{
                font-family: 'Microsoft YaHei', 'Segoe UI', sans-serif;
                font-size: {base_font_size}px;
                background-color: #2d2d3f;
                color: #e0e0e0;
                border: 2px solid #3d3d5c;
                border-radius: 4px;
                padding: 4px 8px;
                min-height: {control_height - 4}px;
                selection-background-color: #7b68ee;
            }}
            QComboBox:hover {{
                border: 2px solid #7b68ee;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 24px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #7b68ee;
                width: 0;
                height: 0;
            }}
            QComboBox QAbstractItemView {{
                background-color: #2d2d3f;
                color: #e0e0e0;
                border: 2px solid #7b68ee;
                selection-background-color: #7b68ee;
                selection-color: white;
                outline: none;
            }}

            /* 复选框样式 */
            QCheckBox {{
                font-family: 'Microsoft YaHei', 'Segoe UI', sans-serif;
                font-size: {base_font_size}px;
                color: #e0e0e0;
                spacing: 8px;
                min-height: {control_height}px;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                background-color: #2d2d3f;
                border: 2px solid #3d3d5c;
                border-radius: 3px;
            }}
            QCheckBox::indicator:checked {{
                background-color: #7b68ee;
                border-color: #7b68ee;
                image: url(check.png);  /* 如果有图片资源可以添加 */
            }}
            QCheckBox::indicator:hover {{
                border: 2px solid #7b68ee;
            }}

            /* 数值标签样式 */
            QLabel#valueLabel {{
                font-family: 'Microsoft YaHei', 'Segoe UI', sans-serif;
                font-size: {base_font_size}px;
                color: #7b68ee;
                font-weight: bold;
                background: #2d2d3f;
                border: 1px solid #3d3d5c;
                border-radius: 3px;
                padding: 2px 6px;
                min-width: 45px;
                max-width: 45px;
                min-height: {control_height - 6}px;
                max-height: {control_height - 6}px;
                qproperty-alignment: AlignCenter;
            }}

            /* 框架样式 */
            QFrame {{
                background-color: #2d2d3f;
                border-radius: 6px;
            }}

            /* 水平线样式 */
            QFrame#line {{
                background-color: #3d3d5c;
                max-height: 1px;
                min-height: 1px;
            }}

            /* 滚动条样式 */
            QScrollBar:vertical {{
                background: #2d2d3f;
                width: 10px;
                border-radius: 5px;
            }}
            QScrollBar::handle:vertical {{
                background: #7b68ee;
                border-radius: 5px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: #9b8aee;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 使用网格布局来更好地控制控件位置
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # 启用/禁用准星
        enable_frame = QFrame()
        enable_frame.setObjectName("enableFrame")
        enable_layout = QHBoxLayout(enable_frame)
        enable_layout.setContentsMargins(10, 5, 10, 5)

        self.enable_check = QCheckBox("显示准星")
        self.enable_check.setChecked(False)
        self.enable_check.stateChanged.connect(self.toggleCrosshair)
        enable_layout.addWidget(self.enable_check)
        enable_layout.addStretch()

        main_layout.addWidget(enable_frame)

        # 线宽设置
        width_group = QGroupBox("线宽设置")
        width_layout = QHBoxLayout()
        width_layout.setContentsMargins(10, 10, 10, 10)

        width_label = QLabel("线宽:")
        width_layout.addWidget(width_label)

        self.width_slider = QSlider(Qt.Horizontal)
        self.width_slider.setRange(1, 10)
        self.width_slider.setValue(self.crosshair.line_width)
        self.width_slider.valueChanged.connect(self.updateWidth)
        width_layout.addWidget(self.width_slider)

        self.width_label = QLabel(f"{self.crosshair.line_width} px")
        self.width_label.setObjectName("valueLabel")
        width_layout.addWidget(self.width_label)

        width_group.setLayout(width_layout)
        main_layout.addWidget(width_group)

        # 长度设置
        length_group = QGroupBox("长度设置")
        length_layout = QHBoxLayout()
        length_layout.setContentsMargins(10, 10, 10, 10)

        length_label = QLabel("长度:")
        length_layout.addWidget(length_label)

        self.length_slider = QSlider(Qt.Horizontal)
        self.length_slider.setRange(5, 50)
        self.length_slider.setValue(self.crosshair.line_length)
        self.length_slider.valueChanged.connect(self.updateLength)
        length_layout.addWidget(self.length_slider)

        self.length_label = QLabel(f"{self.crosshair.line_length} px")
        self.length_label.setObjectName("valueLabel")
        length_layout.addWidget(self.length_label)

        length_group.setLayout(length_layout)
        main_layout.addWidget(length_group)

        # 间隙设置
        gap_group = QGroupBox("间隙设置")
        gap_layout = QHBoxLayout()
        gap_layout.setContentsMargins(10, 10, 10, 10)

        gap_label = QLabel("间隙:")
        gap_layout.addWidget(gap_label)

        self.gap_slider = QSlider(Qt.Horizontal)
        self.gap_slider.setRange(0, 20)
        self.gap_slider.setValue(self.crosshair.gap_size)
        self.gap_slider.valueChanged.connect(self.updateGap)
        gap_layout.addWidget(self.gap_slider)

        self.gap_label = QLabel(f"{self.crosshair.gap_size} px")
        self.gap_label.setObjectName("valueLabel")
        gap_layout.addWidget(self.gap_label)

        gap_group.setLayout(gap_layout)
        main_layout.addWidget(gap_group)

        # 透明度设置
        opacity_group = QGroupBox("透明度设置")
        opacity_layout = QHBoxLayout()
        opacity_layout.setContentsMargins(10, 10, 10, 10)

        opacity_label = QLabel("透明度:")
        opacity_layout.addWidget(opacity_label)

        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(10, 100)
        self.opacity_slider.setValue(int(self.crosshair.opacity * 100))
        self.opacity_slider.valueChanged.connect(self.updateOpacity)
        opacity_layout.addWidget(self.opacity_slider)

        self.opacity_label = QLabel(f"{int(self.crosshair.opacity * 100)}%")
        self.opacity_label.setObjectName("valueLabel")
        opacity_layout.addWidget(self.opacity_label)

        opacity_group.setLayout(opacity_layout)
        main_layout.addWidget(opacity_group)

        # 颜色和轮廓设置
        color_group = QGroupBox("颜色设置")
        color_layout = QHBoxLayout()
        color_layout.setContentsMargins(10, 10, 10, 10)
        color_layout.setSpacing(15)

        color_label = QLabel("准星:")
        color_layout.addWidget(color_label)

        self.color_btn = QPushButton()
        self.color_btn.setObjectName("colorBtn")
        self.color_btn.clicked.connect(self.chooseColor)
        color_layout.addWidget(self.color_btn)

        self.outline_check = QCheckBox("外轮廓")
        self.outline_check.setChecked(self.crosshair.outline)
        self.outline_check.stateChanged.connect(self.toggleOutline)
        color_layout.addWidget(self.outline_check)

        color_layout.addStretch()
        color_group.setLayout(color_layout)
        main_layout.addWidget(color_group)

        # 样式选择
        style_group = QGroupBox("准星样式")
        style_layout = QHBoxLayout()
        style_layout.setContentsMargins(10, 10, 10, 10)

        style_label = QLabel("选择样式:")
        style_layout.addWidget(style_label)

        self.style_combo = QComboBox()
        self.style_combo.addItems(["标准十字", "十字带点", "圆圈"])
        self.style_combo.setCurrentIndex(self.crosshair.style)
        self.style_combo.currentIndexChanged.connect(self.updateStyle)
        style_layout.addWidget(self.style_combo)
        style_layout.addStretch()

        style_group.setLayout(style_layout)
        main_layout.addWidget(style_group)

        # 添加分隔线
        line = QFrame()
        line.setObjectName("line")
        line.setFrameShape(QFrame.HLine)
        main_layout.addWidget(line)

        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        save_btn = QPushButton("保存设置")
        save_btn.setObjectName("saveBtn")
        save_btn.clicked.connect(self.saveSettings)
        button_layout.addWidget(save_btn)

        close_btn = QPushButton("关闭窗口")
        close_btn.setObjectName("closeBtn")
        close_btn.clicked.connect(self.hide)
        button_layout.addWidget(close_btn)

        button_layout.addStretch()
        main_layout.addLayout(button_layout)

        # 添加弹性空间
        main_layout.addStretch()

    def updateColorButton(self):
        """更新颜色按钮样式"""
        self.color_btn.setStyleSheet(f"""
            QPushButton#colorBtn {{
                background-color: {self.crosshair.color.name()};
                border: 2px solid #ffffff;
            }}
            QPushButton#colorBtn:hover {{
                border: 2px solid #4CAF50;
            }}
        """)

    def toggleCrosshair(self, state):
        """切换准星显示"""
        if state == Qt.Checked:
            self.crosshair.show()
        else:
            self.crosshair.hide()

    def updateWidth(self, value):
        """更新线宽"""
        self.crosshair.line_width = value
        self.width_label.setText(f"{value} px")
        self.crosshair.update()

    def updateLength(self, value):
        """更新长度"""
        self.crosshair.line_length = value
        self.length_label.setText(f"{value} px")
        self.crosshair.update()

    def updateGap(self, value):
        """更新间隙"""
        self.crosshair.gap_size = value
        self.gap_label.setText(f"{value} px")
        self.crosshair.update()

    def updateOpacity(self, value):
        """更新透明度"""
        self.crosshair.opacity = value / 100.0
        self.opacity_label.setText(f"{value}%")
        self.crosshair.update()

    def chooseColor(self):
        """选择颜色"""
        color = QColorDialog.getColor(self.crosshair.color, self, "选择准星颜色")
        if color.isValid():
            self.crosshair.color = color
            self.updateColorButton()
            self.crosshair.update()

    def toggleOutline(self, state):
        """切换外轮廓"""
        self.crosshair.outline = (state == Qt.Checked)
        self.crosshair.update()

    def updateStyle(self, index):
        """更新样式"""
        self.crosshair.style = index
        self.crosshair.update()

    def saveSettings(self):
        """保存设置"""
        self.settings.setValue('line_width', self.crosshair.line_width)
        self.settings.setValue('line_length', self.crosshair.line_length)
        self.settings.setValue('gap_size', self.crosshair.gap_size)
        self.settings.setValue('color', self.crosshair.color.name())
        self.settings.setValue('style', self.crosshair.style)
        self.settings.setValue('outline', self.crosshair.outline)
        self.settings.setValue('opacity', self.crosshair.opacity)

    def loadSettings(self):
        """加载设置"""
        self.crosshair.line_width = self.settings.value('line_width', 2, type=int)
        self.crosshair.line_length = self.settings.value('line_length', 20, type=int)
        self.crosshair.gap_size = self.settings.value('gap_size', 4, type=int)
        color_name = self.settings.value('color', '#ff0000')
        self.crosshair.color = QColor(color_name)
        self.crosshair.style = self.settings.value('style', 0, type=int)
        self.crosshair.outline = self.settings.value('outline', False, type=bool)
        self.crosshair.opacity = self.settings.value('opacity', 0.8, type=float)

        # 更新UI显示
        self.width_slider.setValue(self.crosshair.line_width)
        self.length_slider.setValue(self.crosshair.line_length)
        self.gap_slider.setValue(self.crosshair.gap_size)
        self.opacity_slider.setValue(int(self.crosshair.opacity * 100))
        self.style_combo.setCurrentIndex(self.crosshair.style)
        self.outline_check.setChecked(self.crosshair.outline)
        self.updateColorButton()


class CrosshairApp:
    """主应用程序"""

    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)

        # 创建准星窗口
        self.crosshair = CrosshairWidget()

        # 创建设置窗口
        self.settings_window = SettingsWindow(self.crosshair)

        # 创建系统托盘
        self.setupTrayIcon()

    def setupTrayIcon(self):
        """设置系统托盘图标"""
        self.tray_icon = QSystemTrayIcon(self.app)

        # 创建图标
        icon = QPixmap(64, 64)
        icon.fill(Qt.transparent)

        # 绘制简单的准星图标
        painter = QPainter(icon)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(Qt.red, 4))

        center = QPoint(32, 32)
        painter.drawLine(center.x() - 15, center.y(), center.x() - 5, center.y())
        painter.drawLine(center.x() + 5, center.y(), center.x() + 15, center.y())
        painter.drawLine(center.x(), center.y() - 15, center.x(), center.y() - 5)
        painter.drawLine(center.x(), center.y() + 5, center.x(), center.y() + 15)
        painter.end()

        self.tray_icon.setIcon(QIcon(icon))
        self.tray_icon.setToolTip("准星工具")

        # 创建托盘菜单
        tray_menu = QMenu()

        show_action = tray_menu.addAction("显示设置")
        show_action.triggered.connect(self.showSettings)

        toggle_action = tray_menu.addAction("显示/隐藏准星")
        toggle_action.triggered.connect(self.toggleCrosshair)

        tray_menu.addSeparator()

        quit_action = tray_menu.addAction("退出")
        quit_action.triggered.connect(self.quit)

        self.tray_icon.setContextMenu(tray_menu)

        # 双击托盘图标显示设置窗口
        self.tray_icon.activated.connect(self.trayIconActivated)

        self.tray_icon.show()

    def trayIconActivated(self, reason):
        """托盘图标激活事件"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.showSettings()

    def showSettings(self):
        """显示设置窗口"""
        self.settings_window.show()
        self.settings_window.raise_()
        self.settings_window.activateWindow()

    def toggleCrosshair(self):
        """切换准星显示"""
        if self.crosshair.isVisible():
            self.crosshair.hide()
            # 更新复选框状态
            self.settings_window.enable_check.setChecked(False)
        else:
            self.crosshair.show()
            self.settings_window.enable_check.setChecked(True)

    def quit(self):
        """退出程序"""
        self.settings_window.saveSettings()
        self.tray_icon.hide()
        self.app.quit()

    def run(self):
        """运行应用"""
        return self.app.exec_()


if __name__ == '__main__':
    app = CrosshairApp()
    sys.exit(app.run())