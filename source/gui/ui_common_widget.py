"""
Basic widgets for VN Trader.
"""

import csv
from enum import Enum
from typing import Any
import psutil
from PyQt5 import QtCore, QtGui, QtWidgets,QtWebEngineWidgets
import yaml
from typing import TextIO
from datetime import datetime
from pathlib import Path
import csv,json
from copy import copy
import webbrowser

from ..common.constant import *
from ..common.datastruct import *
from ..engine.iengine import EventEngine
from source.data import database_manager
from ..common.utility import load_json, save_json
from ..common.config import SETTING_FILENAME, SETTINGS
from ..api.ctp_constant import THOST_FTDC_PT_Net

from .ui_basic import *

class WebWindow(QtWidgets.QFrame):


    def __init__(self):
        super(WebWindow, self).__init__()

        ## member variables
        self.init_gui()

    def init_gui(self):
        self.setFrameShape(QtWidgets.QFrame.StyledPanel) 
        weblayout = QtWidgets.QFormLayout()

        self.web =  QtWebEngineWidgets.QWebEngineView()
        self.web.setSizePolicy(QtWidgets.QSizePolicy.Expanding,QtWidgets.QSizePolicy.Expanding)
        self.web.setMinimumHeight(1000)
        # self.web.setSizePolicy(QtWidgets.QSizePolicy.Expanding,QtWidgets.QSizePolicy.Expanding)
        # self.web.setMinimumWidth(1000)
        self.web.load(QtCore.QUrl("http://localhost:8888"))

        self.web_addr = QtWidgets.QLineEdit()
        self.web_btn_jn = QtWidgets.QPushButton('Jupyter Notebook') 
        self.web_btn_jn.clicked.connect(lambda:self.web.load(QtCore.QUrl("http://localhost:8888")))
        self.web_btn_go = QtWidgets.QPushButton('Go') 
        self.web_btn_go.clicked.connect(lambda:self.web.load(QtCore.QUrl(self.web_addr.text())))
        
        webhboxlayout1 = QtWidgets.QHBoxLayout()
        webhboxlayout1.addWidget(self.web_btn_jn)
        webhboxlayout1.addWidget(QtWidgets.QLabel('Web'))
        webhboxlayout1.addWidget(self.web_addr)
        webhboxlayout1.addWidget(self.web_btn_go)

        weblayout.addRow(webhboxlayout1)
        weblayout.addRow(self.web)
        self.setLayout(weblayout)


class CsvLoaderWidget(QtWidgets.QWidget):
    """"""

    def __init__(self):
        """"""
        super().__init__()

        self.init_ui()

    def init_ui(self):
        """"""
        self.setWindowTitle("CSV载入")
        self.setFixedWidth(300)

        self.setWindowFlags(
            (self.windowFlags() | QtCore.Qt.CustomizeWindowHint)
            & ~QtCore.Qt.WindowMaximizeButtonHint)

        file_button = QtWidgets.QPushButton("选择文件")
        file_button.clicked.connect(self.select_file)

        load_button = QtWidgets.QPushButton("载入数据")
        load_button.clicked.connect(self.load_data)

        self.file_edit = QtWidgets.QLineEdit()
        self.symbol_edit = QtWidgets.QLineEdit()

        self.exchange_combo = QtWidgets.QComboBox()
        for i in Exchange:
            self.exchange_combo.addItem(str(i.name), i)

        self.interval_combo = QtWidgets.QComboBox()
        for i in Interval:
            self.interval_combo.addItem(str(i.name), i)

        self.datetime_edit = QtWidgets.QLineEdit("Datetime")
        self.open_edit = QtWidgets.QLineEdit("Open")
        self.high_edit = QtWidgets.QLineEdit("High")
        self.low_edit = QtWidgets.QLineEdit("Low")
        self.close_edit = QtWidgets.QLineEdit("Close")
        self.volume_edit = QtWidgets.QLineEdit("Volume")

        self.format_edit = QtWidgets.QLineEdit("%Y-%m-%d %H:%M:%S")

        info_label = QtWidgets.QLabel("合约信息")
        info_label.setAlignment(QtCore.Qt.AlignCenter)

        head_label = QtWidgets.QLabel("表头信息")
        head_label.setAlignment(QtCore.Qt.AlignCenter)

        format_label = QtWidgets.QLabel("格式信息")
        format_label.setAlignment(QtCore.Qt.AlignCenter)

        form = QtWidgets.QFormLayout()
        form.addRow(file_button, self.file_edit)
        form.addRow(QtWidgets.QLabel())
        form.addRow(info_label)
        form.addRow("代码", self.symbol_edit)
        form.addRow("交易所", self.exchange_combo)
        form.addRow("周期", self.interval_combo)
        form.addRow(QtWidgets.QLabel())
        form.addRow(head_label)
        form.addRow("时间戳", self.datetime_edit)
        form.addRow("开盘价", self.open_edit)
        form.addRow("最高价", self.high_edit)
        form.addRow("最低价", self.low_edit)
        form.addRow("收盘价", self.close_edit)
        form.addRow("成交量", self.volume_edit)
        form.addRow(QtWidgets.QLabel())
        form.addRow(format_label)
        form.addRow("时间格式", self.format_edit)
        form.addRow(QtWidgets.QLabel())
        form.addRow(load_button)

        self.setLayout(form)

    def select_file(self):
        """"""
        result: str = QtWidgets.QFileDialog.getOpenFileName(
            self, filter="CSV (*.csv)")
        filename = result[0]
        if filename:
            self.file_edit.setText(filename)

    def load_data(self):
        """"""
        file_path = self.file_edit.text()
        symbol = self.symbol_edit.text()
        exchange = self.exchange_combo.currentData()
        interval = self.interval_combo.currentData()
        datetime_head = self.datetime_edit.text()
        open_head = self.open_edit.text()
        low_head = self.low_edit.text()
        high_head = self.high_edit.text()
        close_head = self.close_edit.text()
        volume_head = self.volume_edit.text()
        datetime_format = self.format_edit.text()

        start, end, count = self.load(
            file_path,
            symbol,
            exchange,
            interval,
            datetime_head,
            open_head,
            high_head,
            low_head,
            close_head,
            volume_head,
            datetime_format
        )

        msg = f"\
        CSV载入成功\n\
        代码：{symbol}\n\
        交易所：{exchange.value}\n\
        周期：{interval.value}\n\
        起始：{start}\n\
        结束：{end}\n\
        总数量：{count}\n\
        "
        QtWidgets.QMessageBox.information(self, "载入成功！", msg)

    def load_by_handle(
        self,
        f: TextIO,
        symbol: str,
        exchange: Exchange,
        interval: Interval,
        datetime_head: str,
        open_head: str,
        high_head: str,
        low_head: str,
        close_head: str,
        volume_head: str,
        datetime_format: str,
    ):
        """
        load by text mode file handle
        """
        reader = csv.DictReader(f)

        bars = []
        start = None
        count = 0
        for item in reader:
            if datetime_format:
                dt = datetime.strptime(item[datetime_head], datetime_format)
            else:
                dt = datetime.fromisoformat(item[datetime_head])

            bar = BarData(
                symbol=symbol,
                exchange=exchange,
                datetime=dt,
                interval=interval,
                volume=item[volume_head],
                open_price=item[open_head],
                high_price=item[high_head],
                low_price=item[low_head],
                close_price=item[close_head],
                gateway_name="DB",
            )

            bars.append(bar)

            # do some statistics
            count += 1
            if not start:
                start = bar.datetime
        end = bar.datetime

        # insert into database
        database_manager.save_bar_data(bars)
        return start, end, count

    def load(
        self,
        file_path: str,
        symbol: str,
        exchange: Exchange,
        interval: Interval,
        datetime_head: str,
        open_head: str,
        high_head: str,
        low_head: str,
        close_head: str,
        volume_head: str,
        datetime_format: str,
    ):
        """
        load by filename
        """
        with open(file_path, "rt") as f:
            return self.load_by_handle(
                f,
                symbol=symbol,
                exchange=exchange,
                interval=interval,
                datetime_head=datetime_head,
                open_head=open_head,
                high_head=high_head,
                low_head=low_head,
                close_head=close_head,
                volume_head=volume_head,
                datetime_format=datetime_format,
            )


class RecorderManager(QtWidgets.QWidget):
    """"""

    signal_log = QtCore.pyqtSignal(Event)
    signal_recorder_update = QtCore.pyqtSignal(Event)
    signal_recorder_out = QtCore.pyqtSignal(Event)
    signal_contract = QtCore.pyqtSignal(Event)

    def __init__(self, contracts: dict = {}):
        super().__init__()
        self.full_symbols = [c for c in contracts.keys()]
        self.init_ui()
        self.register_event()
        self.engineid = ''

    def init_ui(self):
        """"""
        self.setWindowTitle("行情记录")
        self.resize(800, 600)

        # Create widgets
        self.engine_status = QtWidgets.QLineEdit()
        self.engine_status.setMaximumWidth(100)
        self.engine_status.setReadOnly(True)
        self.engine_status.setText('False')
        self.engine_pid = QtWidgets.QLineEdit()
        self.engine_pid.setReadOnly(True)
        self.engine_pid.setMaximumWidth(100)
        refresh_button = QtWidgets.QPushButton("refresh")
        refresh_button.clicked.connect(self.refresh_status)

        start_button = QtWidgets.QPushButton("订阅所有合约")
        start_button.clicked.connect(self.start_engine)
        stop_button = QtWidgets.QPushButton("清空所有合约")
        stop_button.clicked.connect(self.stop_engine)


        self.symbol_line = QtWidgets.QLineEdit()
        self.symbol_line.setMaximumWidth(300)
        # self.symbol_line.setFixedHeight(
        #     self.symbol_line.sizeHint().height() * 2)

        self.symbol_completer = QtWidgets.QCompleter(self.full_symbols)
        self.symbol_completer.setFilterMode(QtCore.Qt.MatchContains)
        self.symbol_completer.setCompletionMode(
            self.symbol_completer.PopupCompletion)
        self.symbol_line.setCompleter(self.symbol_completer)

        self.record_choice = QtWidgets.QComboBox()
        self.record_choice.addItems(['tick', 'bar'])        
        add_button = QtWidgets.QPushButton("添加")
        add_button.clicked.connect(self.add_recording)

        remove_button = QtWidgets.QPushButton("移除")
        remove_button.clicked.connect(self.remove_recording)

        # add_tick_button = QtWidgets.QPushButton("添加")
        # add_tick_button.clicked.connect(self.add_tick_recording)

        # remove_tick_button = QtWidgets.QPushButton("移除")
        # remove_tick_button.clicked.connect(self.remove_tick_recording)

        self.bar_recording_edit = QtWidgets.QTextEdit()
        self.bar_recording_edit.setReadOnly(True)

        self.tick_recording_edit = QtWidgets.QTextEdit()
        self.tick_recording_edit.setReadOnly(True)

        self.log_edit = QtWidgets.QTextEdit()
        self.log_edit.setReadOnly(True)

        # Set layout
        statusbox = QtWidgets.QHBoxLayout()
        statusbox.addWidget(refresh_button)
        statusbox.addWidget(QtWidgets.QLabel("Recorder PID"))
        statusbox.addWidget(self.engine_pid)
        statusbox.addWidget(QtWidgets.QLabel("Alive"))
        statusbox.addWidget(self.engine_status)
        statusbox.addWidget(start_button)
        statusbox.addWidget(stop_button)

        # grid = QtWidgets.QGridLayout()
        # grid.addWidget(QtWidgets.QLabel("Bar记录"), 0, 0)
        # grid.addWidget(add_bar_button, 0, 1)
        # grid.addWidget(remove_bar_button, 0, 2)
        # grid.addWidget(QtWidgets.QLabel("Tick记录"), 1, 0)
        # grid.addWidget(add_tick_button, 1, 1)
        # grid.addWidget(remove_tick_button, 1, 2)

        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(QtWidgets.QLabel("代码全称"))
        hbox.addWidget(self.symbol_line)
        hbox.addWidget(QtWidgets.QLabel("记录选项"))
        hbox.addWidget(self.record_choice)
        hbox.addWidget(add_button)
        hbox.addWidget(remove_button)
        # hbox.addStretch()

        grid2 = QtWidgets.QGridLayout()
        grid2.addWidget(QtWidgets.QLabel("Bar记录列表"), 0, 0)
        grid2.addWidget(QtWidgets.QLabel("Tick记录列表"), 0, 1)
        grid2.addWidget(self.bar_recording_edit, 1, 0)
        grid2.addWidget(self.tick_recording_edit, 1, 1)
        grid2.addWidget(self.log_edit, 2, 0, 1, 2)

        vbox = QtWidgets.QVBoxLayout()
        vbox.addLayout(statusbox)
        vbox.addLayout(hbox)
        vbox.addLayout(grid2)
        self.setLayout(vbox)

    def register_event(self):
        """"""
        self.signal_log.connect(self.process_log_event)
        self.signal_contract.connect(self.process_contract_event)
        self.signal_recorder_update.connect(self.process_update_event)

    def start_engine(self):
        m = Event(type=EventType.RECORDER_CONTROL,
            des='@' + self.engineid,
            src='0',            
            msgtype=MSG_TYPE.MSG_TYPE_RECORDER_START
        )
        self.signal_recorder_out.emit(m)

    def stop_engine(self):
        m = Event(type=EventType.RECORDER_CONTROL,
            des='@' + self.engineid,
            src='0',            
            msgtype=MSG_TYPE.MSG_TYPE_RECORDER_STOP
        )
        self.signal_recorder_out.emit(m)

    def refresh_status(self):
        self.engine_pid.setText('')
        self.engine_status.setText('False')
        self.engineid = ''
        self.bar_recording_edit.clear()
        self.tick_recording_edit.clear()
        m = Event(type=EventType.RECORDER_CONTROL,
            des='@*',
            src='0',            
            msgtype=MSG_TYPE.MSG_TYPE_RECORDER_STATUS
        )
        self.signal_recorder_out.emit(m)

    def process_log_event(self, event: Event):
        """"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        msg = f"{timestamp}\t{event.data}"
        self.log_edit.append(msg)

    def process_update_event(self, event: Event):
        """"""
        data = event.data
        msgtype = event.msg_type
        if msgtype == MSG_TYPE.MSG_TYPE_RECORDER_STATUS:
            self.engine_pid.setText(event.source)
            self.engine_status.setText(data)
            self.engineid = event.source
        elif msgtype == MSG_TYPE.MSG_TYPE_RECORDER_RTN_DATA:
            data = json.loads(data)
            self.bar_recording_edit.clear()
            bar_text = "\n".join(data["bar"])
            self.bar_recording_edit.setText(bar_text)

            self.tick_recording_edit.clear()
            tick_text = "\n".join(data["tick"])
            self.tick_recording_edit.setText(tick_text)

    def process_contract_event(self, event: Event):
        """"""
        contract = event.data
        self.full_symbols.append(contract.full_symbol)

        model = self.symbol_completer.model()
        model.setStringList(self.full_symbols)

    def add_recording(self):
        if self.engine_status.text() == 'False' or self.engine_pid.text() == '': 
            QtWidgets.QMessageBox().information(None, 'Error','RecorderEngine is not running!',QtWidgets.QMessageBox.Ok)
            return
        if self.record_choice.currentText() == 'tick':
            self.add_tick_recording()
        elif self.record_choice.currentText() == 'bar':
            self.add_bar_recording()

    def remove_recording(self):
        if self.engine_status.text() == 'False' or self.engine_pid.text() == '': 
            QtWidgets.QMessageBox().information(None, 'Error','RecorderEngine is not running!',QtWidgets.QMessageBox.Ok)
            return
        if self.record_choice.currentText() == 'tick':
            self.remove_tick_recording()
        elif self.record_choice.currentText() == 'bar':
            self.remove_bar_recording()

    def add_bar_recording(self):
        """"""
        full_symbol = self.symbol_line.text()

        m = Event(type=EventType.RECORDER_CONTROL,
            des='@' + self.engineid,
            src='0',
            data=full_symbol,            
            msgtype=MSG_TYPE.MSG_TYPE_RECORDER_ADD_BAR
        )
        self.signal_recorder_out.emit(m)

    def add_tick_recording(self):
        """"""
        full_symbol = self.symbol_line.text()
        m = Event(type=EventType.RECORDER_CONTROL,
            des='@' + self.engineid,
            src='0', 
            data=full_symbol,           
            msgtype=MSG_TYPE.MSG_TYPE_RECORDER_ADD_TICK
        )
        self.signal_recorder_out.emit(m)

    def remove_bar_recording(self):
        """"""
        full_symbol = self.symbol_line.text()
        m = Event(type=EventType.RECORDER_CONTROL,
            des='@' + self.engineid,
            src='0',
            data=full_symbol,          
            msgtype=MSG_TYPE.MSG_TYPE_RECORDER_REMOVE_BAR
        )
        self.signal_recorder_out.emit(m)

    def remove_tick_recording(self):
        """"""
        full_symbol = self.symbol_line.text()
        m = Event(type=EventType.RECORDER_CONTROL,
            des='@' + self.engineid,
            src='0', 
            data=full_symbol,           
            msgtype=MSG_TYPE.MSG_TYPE_RECORDER_REMOVE_TICK
        )
        self.signal_recorder_out.emit(m)




















class ContractManager(QtWidgets.QWidget):
    """
    Query contract data available to trade in system.
    """

    headers = {
        "full_symbol":"全称",
        "symbol": "代码",
        "exchange": "交易所",
        "name": "名称",
        "product": "合约分类",
        "size": "合约乘数",
        "pricetick": "价格跳动",
        "min_volume": "最小委托量",
        "net_position":"是否净持仓",
        "long_margin_ratio":"多仓保证金率",
        "short_margin_ratio":"空仓保证金率"
    }

    def __init__(self):
        super(ContractManager, self).__init__()

        self.contracts = {}
        self.load_contract()


        self.init_ui()

    def load_contract(self):
        contractfile = Path.cwd().joinpath("etc/ctpcontract.yaml")
        with open(contractfile, encoding='utf8') as fc: 
            contracts = yaml.load(fc)
        print('loading contracts, total number:',len(contracts))
        for sym, data in contracts.items():
            contract = ContractData(
                symbol=data["symbol"],
                exchange=Exchange(data["exchange"]),
                name=data["name"],
                product=PRODUCT_CTP2VT[str(data["product"])],
                size=data["size"],
                pricetick=data["pricetick"],
                net_position = True if str(data["positiontype"]) == THOST_FTDC_PT_Net else False,
                long_margin_ratio = data["long_margin_ratio"],
                short_margin_ratio = data["short_margin_ratio"],
                full_symbol = data["full_symbol"]
            )            
            # For option only
            if contract.product == Product.OPTION:
                contract.option_underlying = data["option_underlying"],
                contract.option_type = OPTIONTYPE_CTP2VT.get(str(data["option_type"]), None),
                contract.option_strike = data["option_strike"],
                contract.option_expiry = datetime.strptime(str(data["option_expiry"]), "%Y%m%d"),
            self.contracts[contract.full_symbol] = contract      

    def init_ui(self):
        """"""
        self.setWindowTitle("合约查询")
        self.resize(1000, 600)

        self.filter_line = QtWidgets.QLineEdit()
        self.filter_line.setPlaceholderText("输入全称字段（交易所,类别，产品代码，合约编号），留空则查询所有合约")
        self.filter_line.returnPressed.connect(self.show_contracts)
        self.button_show = QtWidgets.QPushButton("查询")
        self.button_show.clicked.connect(self.show_contracts)

        labels = []
        for name, display in self.headers.items():
            label = f"{display}\n{name}"
            labels.append(label)

        self.contract_table = QtWidgets.QTableWidget()
        self.contract_table.setColumnCount(len(self.headers))
        self.contract_table.setHorizontalHeaderLabels(labels)
        self.contract_table.verticalHeader().setVisible(False)
        self.contract_table.setEditTriggers(self.contract_table.NoEditTriggers)
        self.contract_table.setAlternatingRowColors(True)

        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(self.filter_line)
        hbox.addWidget(self.button_show)

        vbox = QtWidgets.QVBoxLayout()
        vbox.addLayout(hbox)
        vbox.addWidget(self.contract_table)

        self.setLayout(vbox)

    def show_contracts(self):
        """
        Show contracts by symbol
        """
        flt = str(self.filter_line.text()).upper()


        if flt:
            contracts = [
                contract for contract in self.contracts.values() if flt in contract.full_symbol
            ]
        else:
            contracts = self.contracts

        self.contract_table.clearContents()
        self.contract_table.setRowCount(len(contracts))

        for row, contract in enumerate(contracts):
            for column, name in enumerate(self.headers.keys()):
                value = getattr(contract, name)
                if isinstance(value, Enum):
                    cell = EnumCell(value, contract)
                else:
                    cell = BaseCell(value, contract)
                self.contract_table.setItem(row, column, cell)

        self.contract_table.resizeColumnsToContents()
    
    def on_contract(self,contract):
        self.contracts[contract.full_symbol] = contract



class StatusThread(QtCore.QThread):
    status_update = QtCore.pyqtSignal(str)

    def __init__(self):
        QtCore.QThread.__init__(self)

    def run(self):
        while True:
            cpuPercent = psutil.cpu_percent()
            memoryPercent = psutil.virtual_memory().percent
            self.status_update.emit('CPU Usage: ' + str(cpuPercent) + '% Memory Usage: ' + str(memoryPercent) + '%')
            self.sleep(2)




class GlobalDialog(QtWidgets.QDialog):
    """
    Start connection of a certain gateway.
    """

    def __init__(self):
        """"""
        super().__init__()

        self.widgets = {}

        self.init_ui()

    def init_ui(self):
        """"""
        self.setWindowTitle("Python进程相关配置")
        self.setMinimumWidth(800)

        settings = copy(SETTINGS)
        settings.update(load_json(SETTING_FILENAME))

        # Initialize line edits and form layout based on setting.
        form = QtWidgets.QFormLayout()

        for field_name, field_value in settings.items():
            field_type = type(field_value)
            widget = QtWidgets.QLineEdit(str(field_value))

            form.addRow(f"{field_name} <{field_type.__name__}>", widget)
            self.widgets[field_name] = (widget, field_type)

        button = QtWidgets.QPushButton("确定")
        button.clicked.connect(self.update_setting)
        form.addRow(button)

        self.setLayout(form)

    def update_setting(self):
        """
        Get setting value from line edits and update global setting file.
        """
        settings = {}
        for field_name, tp in self.widgets.items():
            widget, field_type = tp
            value_text = widget.text()

            if field_type == bool:
                if value_text == "True":
                    field_value = True
                else:
                    field_value = False
            else:
                field_value = field_type(value_text)

            settings[field_name] = field_value

        QtWidgets.QMessageBox.information(
            self,
            "注意",
            "配置的修改需要重启后才会生效！",
            QtWidgets.QMessageBox.Ok
        )

        save_json(SETTING_FILENAME, settings)
        self.accept()


class TextEditDialog(QtWidgets.QDialog):
    """
    Start connection of a certain gateway.
    """

    def __init__(self,filename:str):
        """"""
        super().__init__()
        self.filename = filename
        self.setWindowTitle("配置编辑文件")
        self.setMinimumWidth(800)
        self.setMinimumHeight(800)
        self.textedit = QtWidgets.QTextEdit()
        self.textedit.setFont(QtGui.QFont('Microsoft Sans Serif', 12) )
        self.init_ui()

    def init_ui(self):
        """"""
        form = QtWidgets.QVBoxLayout()
        savebutton = QtWidgets.QPushButton("save")
        savebutton.clicked.connect(self.update_file)
        form.addWidget(self.textedit)
        form.addWidget(savebutton)
        self.setLayout(form)
        with open(self.filename,'r') as f:
            my_txt=f.read()
            self.textedit.setText(my_txt)       

    def update_file(self):
        """
        .
        """


        my_text=self.textedit.toPlainText()
        with open(self.filename,'w+') as f:            
            f.write(my_text)   
        QtWidgets.QMessageBox.information(
            self,
            "注意",
            "配置的修改需要重启后才会生效！",
            QtWidgets.QMessageBox.Ok
        )          
        self.accept()





class AboutWidget(QtWidgets.QDialog):
    #----------------------------------------------------------------------
    def __init__(self, parent=None):
        """Constructor"""
        super(AboutWidget, self).__init__(parent)

        self.initUi()
    #----------------------------------------------------------------------
    def initUi(self):
        """"""
        self.setWindowTitle('About StarQuant')

        text = u"""
            StarQuant
            易数交易系统
            Lightweight Algorithmic Trading System            
            Language: C++,Python
            Contact: dr.wb@qq.com
            License：MIT

            莫道交易如浪深，莫言策略似沙沉。
            千回万测虽辛苦，实盘验后始得金。
     
            """
        label = QtWidgets.QLabel()
        label.setText(text)
        label.setMinimumWidth(300)
        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(label)
        button = QtWidgets.QPushButton("源代码网址")
        button.clicked.connect(self.open_code)
        vbox.addWidget(button)
        self.setLayout(vbox)  

    def open_code(self):

        webbrowser.open("https://www.github.com/physercoe/starquant")