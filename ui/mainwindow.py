# -*- coding: utf-8 -*-
from pathlib import Path
from PyQt5 import QtWidgets, QtCore, QtGui

from .mainwindow_ui import Ui_MainWindow
from model import Model
from item import Item
from delegate import Delegate
from column import Column
from poppler import Poppler
from image_process import ImageProcess
from .toolbar_ui import Ui_Form
from tesseract import Tesseract

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, app):
        super().__init__()

        self.copy_data = None
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.resize(800, 600)

        self.model = Model( self, Item(), Column(['File name', 'Resolution', 'Settings']) )
        
        self.ui.tableView.setModel(self.model)
        self.ui.tableView.setItemDelegate( Delegate() )
        self.ui.tableView.clicked.connect(self.tableview_clicked)
        self.ui.tableView.customContextMenuRequested.connect(self.context_menu_tableview)

        self.tool_bar = ToolBar(self.ui.toolBar)
        self.ui.toolBar.addWidget(self.tool_bar)

        self.tool_bar.ui.toolButton.clicked.connect(self.open_files)
        self.tool_bar.ui.toolButton_3.clicked.connect(self.ui.image_view.recognize)
        self.tool_bar.ui.toolButton_4.clicked.connect(self.split_cells)
        self.tool_bar.ui.toolButton_5.clicked.connect(self.ui.image_view.graphics_view_update)
        self.tool_bar.ui.toolButton_6.clicked.connect(self.ui.image_view.graphics_view_update)
        self.tool_bar.ui.toolButton_7.clicked.connect(self.ui.image_view.graphics_view_update)
        self.tool_bar.ui.toolButton_8.clicked.connect(self.ocr)

    def context_menu_tableview(self, point):
        menu = QtWidgets.QMenu(self)
        menu.addAction('Open files', self.open_files)
        menu.addAction('Remove all items', lambda : self.model.removeRows(0, self.model.rowCount()))
        menu.addAction('Copy setting', lambda : self.copy_setting)
        menu.exec( self.focusWidget().mapToGlobal(point) )

    def copy_setting(self):
        item = self.tableview_selected_item()
        self.copy_data = {
            'rects' : item.data('rects'),
            'crops' : item.data('crops')
        }

    def ocr(self):
        for item in self.model.root().children():
            i = 0
            while i < 1000:
                rect = item.data( 'Rect'+str(i) )
                if rect is None:
                    break
                item.data( 'Text'+str(i), Tesseract().OCR(rect).strip() )
                i = i + 1
        
        columns = list( range( self.model.columnCount() ) )[::-1]
        for c in columns:
            column = self.model.headerData(c, QtCore.Qt.Horizontal)
            if not 'Rect' in column:
                continue

            replace = column.replace('Rect', 'Text')
            if self.model.headerData(c + 1, QtCore.Qt.Horizontal) == replace:
                continue

            self.model.insertColumn(c + 1)
            self.model.setHeaderData(c + 1, QtCore.Qt.Horizontal, replace)

    def open_files(self):
        return_value = QtWidgets.QFileDialog.getOpenFileNames(self, 'Open files', '', 'Support Files (*.png *.pdf)')
        if len(return_value[0]) == 0:
            return
        
        column_count = self.model.columnCount()
        if column_count > 3:
            self.model.removeColumns(3, column_count-3)

        self.model.removeRows(0, self.model.rowCount())
        files = [ Path(f) for f in return_value[0] ]
        self.model.insertRows(0, len(files))

        for r, f in enumerate(files):
            item = self.model.root().child(r)
            item.data('File name', f.name)
            item.data('file_path', f)

            if f.suffix == '.pdf':
                output_path = Poppler().pdftocairo(f, Path('__temp__.png'), 300)
                item.data('qpixmap', QtGui.QPixmap(str(output_path)))
                output_path.unlink()
            else:
                item.data('qpixmap', QtGui.QPixmap( str(f) ) )
            h, w = item.data('qpixmap').rect().height(), item.data('qpixmap').rect().width()
            item.data('Resolution', str(h) + 'x' + str(w) )

    def rect_to_rect_item(self, rect, color, pen_width):
        rect_item = QtWidgets.QGraphicsRectItem()
        rect_item.setRect( rect[0], rect[1], rect[2], rect[3] )
        pen = QtGui.QPen(color)
        pen.setWidth(pen_width)
        rect_item.setPen(pen)
        return rect_item

    def split_cells(self):
        selected_item = self.tableview_selected_item()
        if selected_item is None:
            return

        crops = selected_item.data('crops')
        if crops is None or len(crops) == 0:
            return

        qpixmap = selected_item.data('qpixmap')
        for i, c in enumerate(crops):
            cropped_qpixmap = qpixmap.copy( QtCore.QRect( c[0], c[1], c[2], c[3] ) )
            selected_item.data('Rect'+str(i), cropped_qpixmap)
        
        column_count = self.model.columnCount()
        columns = [ self.model.headerData(c, QtCore.Qt.Horizontal) for c in range(column_count) ]
        append_columns = [ 'Rect'+str(i) for i in range(len(crops)) if not 'Rect'+str(i) in columns ]

        self.model.insertColumns(column_count, len(append_columns))
        for c, column in enumerate(append_columns):
            self.model.setHeaderData(column_count + c, QtCore.Qt.Horizontal, column)

    def tableview_clicked(self, index):

        clicked_item = index.internalPointer()

        if clicked_item.data('edge') is None:
            self.ui.image_view.recognize()
        rects_index = clicked_item.data('rects_index')
        if rects_index is None:
            clicked_item.data('rects_index', 0)
            self.ui.image_view.set_current_index(0)
        else:
            self.ui.image_view.set_current_index(rects_index)
        
        self.ui.image_view.update_rows()
        self.ui.image_view.graphics_view_update()
        self.ui.image_view.graphics_view_fit()

    def tableview_selected_item(self):
        selected_indexes = self.ui.tableView.selectedIndexes()
        if len(selected_indexes) == 0:
            return None
        return self.model.root().child( selected_indexes[0].row() )

class ToolBar(QtWidgets.QWidget):
    def __init__(self, parent):
        super().__init__(parent)

        self.ui = Ui_Form()
        self.ui.setupUi(self)
