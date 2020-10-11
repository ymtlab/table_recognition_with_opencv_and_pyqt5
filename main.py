# -*- coding: utf-8 -*-
import cv2
import numpy as np
import sys
from pathlib import Path
from PyQt5 import QtWidgets, QtCore, QtGui

from mainwindow import Ui_MainWindow
from model import Model
from item import Item
from delegate import Delegate
from column import Column
from table_recognition import recognition_table_from_image_file

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, app):
        super().__init__()

        self.copied_items = None
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.model = Model( self, Item(), Column(['File name']) )
        self.model_2 = Model( self, Item(), Column(['column']) )
        
        self.ui.tableView.setModel(self.model)
        self.ui.tableView.setItemDelegate( Delegate() )
        self.ui.tableView.clicked.connect(self.tableview_clicked)
        
        self.ui.listView.setModel(self.model_2)
        self.ui.listView.setItemDelegate( Delegate() )
        self.ui.listView.customContextMenuRequested.connect(self.context_menu_listview)
        self.ui.listView.clicked.connect(self.listview_clicked)

        self.ui.toolButton.clicked.connect(self.rect_back)
        self.ui.toolButton_2.clicked.connect(self.rect_next)

        self.ui.range_slider.setRangeLimit(0, 110000)
        self.ui.range_slider.setRange(100, 100000)
        
        self.ui.graphicsView.setScene( QtWidgets.QGraphicsScene(self.ui.graphicsView) )

        self.ui.range_slider.slider_changed.connect(self.range_slider_changed)
        self.range_slider_changed()

    def listview_clicked(self, index):
        print('listview_clicked')

    def range_slider_changed(self):
        lower, upper = self.ui.range_slider.getRange()
        self.ui.lineEdit.setText( str(lower) )
        self.ui.lineEdit_2.setText( str(upper) )
        self.recognition_files()
        self.update_graphics_view()

    def context_menu_listview(self, point):
        menu = QtWidgets.QMenu(self)
        menu.addAction('AAA', self.aaa)
        menu.exec( self.focusWidget().mapToGlobal(point) )

    def open_files(self):
        file_names, selectedFilter = QtWidgets.QFileDialog.getOpenFileNames(self, 'Open files', '', 'Image Files (*.png)')
        if len(file_names) == 0:
            return

        files = [ Path(f) for f in file_names ]
        self.model.insertRows(0, len(files))
        for r, f in enumerate(files):
            item = self.model.root().child(r)
            item.data('File name', f.name)
            item.data('file_path', f)

    def recognition_files(self):
        
        area_range = self.ui.range_slider.getRange()

        for r in range(self.model.rowCount()):

            item = self.model.root().child(r)
            filename = item.data('file_path')

            data = recognition_table_from_image_file(filename, area_range)

            height, width, dim = data['rgb_image'].shape
            bytesPerLine = dim * width
            
            data['qimage'] = QtGui.QImage(data['rgb_image'].data, width, height, bytesPerLine, QtGui.QImage.Format_RGB888)
            data['qpixmap'] = QtGui.QPixmap().fromImage(data['qimage'])
            
            lower, upper = self.ui.range_slider.getRange()

            rect_items = []
            rect_alpha_items = []
            for rect in data['rects']:

                if not lower < rect[2] < upper:
                    continue

                rect_item = QtWidgets.QGraphicsRectItem()
                rect_item.setRect( rect[0], rect[1], rect[2], rect[3] )
                pen = QtGui.QPen(QtGui.QColor(255, 0, 0))
                pen.setWidth(10)
                rect_item.setPen(pen)
                rect_items.append(rect_item)

                rect_item_a = QtWidgets.QGraphicsRectItem()
                rect_item_a.setRect( rect[0], rect[1], rect[2], rect[3] )
                pen_a = QtGui.QPen(QtGui.QColor(0, 0, 255, 100))
                pen_a.setWidth(6)
                rect_item_a.setPen(pen_a)
                rect_alpha_items.append(rect_item_a)
            
            data['rect_items'] = rect_items
            data['rect_alpha_items'] = rect_alpha_items
            data['rect_items_index'] = 0
            
            for key in data:
                item.data(key, data[key])

    def rect_change(self, increase):
        selected_indexes = self.ui.tableView.selectedIndexes()
        if len(selected_indexes) == 0:
            return
        selected_item = self.model.root().child( selected_indexes[0].row() )

        index = selected_item.data('rect_items_index') + increase
        rect_items = selected_item.data('rect_items')
        
        if index < 0:
            index = len(rect_items) - 1
        elif index > len(rect_items) - 1:
            index = 0
        
        selected_item.data('rect_items_index', index)

        self.update_graphics_view()
        self.ui.lineEdit_3.setText( str(selected_item.data('rect_items_index')) )

    def rect_back(self):
        self.rect_change(-1)
        
    def rect_next(self):
        self.rect_change(1)
        
    def update_graphics_view(self):
        selected_indexes = self.ui.tableView.selectedIndexes()
        if len(selected_indexes) == 0:
            return
        selected_index = selected_indexes[0].row() 
        selected_item = self.model.root().child(selected_index)

        scene = self.ui.graphicsView.scene()

        for item in scene.items():
            scene.removeItem(item)

        scene.setSceneRect( QtCore.QRectF(selected_item.data('qpixmap').rect()) )

        scene.addPixmap( selected_item.data('qpixmap') )

        rect_items = selected_item.data('rect_items')
        rect_items_index = selected_item.data('rect_items_index')
        if len(rect_items) > 0:
            scene.addItem( selected_item.data('rect_items')[rect_items_index] )

        for item in selected_item.data('rect_alpha_items'):
            scene.addItem(item)
        
        item = self.model_2.root().child(rect_items_index)
        index = self.model_2.createIndex(rect_items_index, 0, item)
        self.ui.listView.setCurrentIndex(index)

    def tableview_clicked(self, index):
        clicked_item = index.internalPointer()
        clicked_item.data('rect_items_index', 0)
        self.recognition_files()
        self.update_graphics_view()
        self.ui.graphicsView.fitInView(self.ui.graphicsView.scene().sceneRect(), QtCore.Qt.KeepAspectRatio)

        if self.model_2.rowCount() > 0:
            self.model_2.removeRows(0, self.model_2.rowCount())

        rect_items = clicked_item.data('rect_items')
        self.model_2.insertRows( 0, len(rect_items) )

        for r, (rect_item, list_item) in enumerate(zip(rect_items, self.model_2.root().children())):
            list_item.data('column', 'Rect'+str(r))
            list_item.data('rect_item', rect_item)

def main():
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow(app)
    window.show()
    app.exec()

if __name__ == '__main__':
    main()
