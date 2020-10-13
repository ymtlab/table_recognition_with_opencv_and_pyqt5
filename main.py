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
from table_recognition import recognition_table_from_image_file, crop_margin

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, app):
        super().__init__()

        self.copied_items = None
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.model = Model( self, Item(), Column(['File name', 'Resolution']) )
        self.model_2 = Model( self, Item(), Column(['column']) )
        
        self.ui.tableView.setModel(self.model)
        self.ui.tableView.setItemDelegate( Delegate() )
        self.ui.tableView.clicked.connect(self.tableview_clicked)
        
        self.ui.listView.setModel(self.model_2)
        self.ui.listView.setItemDelegate( Delegate() )
        self.ui.listView.customContextMenuRequested.connect(self.context_menu_listview)
        self.ui.listView.clicked.connect(self.listview_clicked)

        self.ui.toolButton.clicked.connect(lambda : self.rect_change(-1))
        self.ui.toolButton_2.clicked.connect(lambda : self.rect_change(1))
        self.ui.toolButton_4.clicked.connect(self.split_cells)
        self.ui.toolButton_5.clicked.connect(self.graphics_view_update)
        self.ui.toolButton_6.clicked.connect(self.graphics_view_update)
        self.ui.toolButton_7.clicked.connect(self.graphics_view_update)

        self.ui.lineEdit.returnPressed.connect(self.range_slider_update)
        self.ui.lineEdit_2.returnPressed.connect(self.range_slider_update)

        self.ui.range_slider.setRangeLimit(3, 110000)
        self.ui.range_slider.setRange(100, 100000)
        
        self.ui.graphicsView.setScene( QtWidgets.QGraphicsScene(self.ui.graphicsView) )

        self.ui.range_slider.slider_changed.connect(self.range_slider_changed)
        self.range_slider_changed()

    def range_slider_update(self):
        self.ui.range_slider.setRange(
            int(self.ui.lineEdit.text()), 
            int(self.ui.lineEdit_2.text())
        )
        self.ui.range_slider.update()

    def range_slider_changed(self):
        lower, upper = self.ui.range_slider.getRange()
        self.ui.lineEdit.setText( str(lower) )
        self.ui.lineEdit_2.setText( str(upper) )

        selected_item = self.tableview_selected_item()
        if selected_item is None:
            return
        
        self.recognition_file( selected_item.row() )
        self.graphics_view_update()
        self.listview_update(selected_item)

    def context_menu_listview(self, point):
        menu = QtWidgets.QMenu(self)
        menu.addAction('Delete', self.listview_delete_selected_item)
        menu.exec( self.focusWidget().mapToGlobal(point) )

    def open_files(self):

        return_value = QtWidgets.QFileDialog.getOpenFileNames(self, 'Open files', '', 'Image Files (*.png)')
        if len(return_value[0]) == 0:
            return
        files = [ Path(f) for f in return_value[0] ]
        self.model.insertRows(0, len(files))

        for r, f in enumerate(files):
            item = self.model.root().child(r)
            item.data('File name', f.name)
            item.data('file_path', f)
            item.data('qimage', QtGui.QImage( str(f) ) )
            item.data('qpixmap', QtGui.QPixmap( str(f) ) )
            h, w = item.data('qpixmap').rect().height(), item.data('qpixmap').rect().width()
            item.data('Resolution', str(h) + 'x' + str(w) )

    def recognition(self):
        selected_item = self.tableview_selected_item()
        if selected_item is None:
            return
        self.recognition_file( selected_item.row() )
        self.graphics_view_update()
        self.ui.graphicsView.fitInView(self.ui.graphicsView.scene().sceneRect(), QtCore.Qt.KeepAspectRatio)
        self.listview_update(selected_item)
        self.listview_set_current_index( selected_item.data('rect_items_index') )

    def recognition_file(self, row):

        def rect_to_rect_item(rect, color, pen_width):
            rect_item = QtWidgets.QGraphicsRectItem()
            rect_item.setRect( rect[0], rect[1], rect[2], rect[3] )
            pen = QtGui.QPen(color)
            pen.setWidth(pen_width)
            rect_item.setPen(pen)
            return rect_item

        model_item = self.model.root().child(row)

        data = recognition_table_from_image_file(
            model_item.data('file_path'), 
            self.ui.range_slider.getRange()
        )

        rect_items, rect_alpha_items, rect_alpha_items_2 = [], [], []
        for rect, crop in zip(data['rects'], data['crops']):
            rect_items.append( rect_to_rect_item(rect, QtGui.QColor(255, 0, 0), 10) )
            rect_alpha_items.append( rect_to_rect_item(rect, QtGui.QColor(0, 0, 255, 100), 6) )
            rect_alpha_items_2.append( rect_to_rect_item(crop, QtGui.QColor(0, 255, 0, 100), 6) )

        data['rect_items'] = rect_items
        data['rect_alpha_items'] = rect_alpha_items
        data['rect_alpha_items_2'] = rect_alpha_items_2
        data['rect_items_index'] = 0
        
        for key in data:
            model_item.data( key, data[key] )

    def recognition_files(self):
        for r in range(self.model.rowCount()):
            self.recognition_file(r)
        
    def rect_change(self, increase):
        selected_item = self.tableview_selected_item()
        if selected_item is None:
            return

        index = selected_item.data('rect_items_index') + increase
        rect_items = selected_item.data('rect_items')
        
        if index < 0:
            index = len(rect_items) - 1
        elif index > len(rect_items) - 1:
            index = 0
        
        selected_item.data('rect_items_index', index)
        self.graphics_view_update()
        self.listview_set_current_index( selected_item.data('rect_items_index') )

    def graphics_view_update(self):
        selected_item = self.tableview_selected_item()
        if selected_item is None:
            return

        scene = self.ui.graphicsView.scene()

        for item in scene.items():
            scene.removeItem(item)

        if self.ui.toolButton_5.isChecked():
            edge = selected_item.data('edge')
            if not edge is None:
                qpixmap = self.cv2_image_to_qpixmap( selected_item.data('edge') )
                scene.setSceneRect( QtCore.QRectF(qpixmap.rect()) )
                scene.addPixmap(qpixmap)
        else:
            scene.setSceneRect( QtCore.QRectF(selected_item.data('qpixmap').rect()) )
            scene.addPixmap( selected_item.data('qpixmap') )

        if self.ui.toolButton_6.isChecked():
            rect_alpha_items = selected_item.data('rect_alpha_items')
            if not rect_alpha_items is None:
                for item in selected_item.data('rect_alpha_items'):
                    scene.addItem(item)
                
        if self.ui.toolButton_7.isChecked():
            rect_alpha_items_2 = selected_item.data('rect_alpha_items_2')
            if not rect_alpha_items_2 is None:
                for item in selected_item.data('rect_alpha_items_2'):
                    scene.addItem(item)
        
        rect_items = selected_item.data('rect_items')
        if not rect_items is None and len(rect_items) > 0:
            rect_items_index = selected_item.data('rect_items_index')
            scene.addItem( selected_item.data('rect_items')[rect_items_index] )

    def listview_update(self, model_item):

        rect_items = model_item.data('rect_items')
        if rect_items is None:
            return

        if self.model_2.rowCount() > 0:
            self.model_2.removeRows(0, self.model_2.rowCount())

        self.model_2.insertRows( 0, len(rect_items) )
        children = self.model_2.root().children()
        for r, (rect_item, list_item) in enumerate(zip(rect_items, children)):
            list_item.data('column', 'Rect'+str(r))
            list_item.data('rect_item', rect_item)

    def listview_set_current_index(self, row):
        if self.model_2.rowCount() == 0:
            return
        index = self.model_2.createIndex( row, 0, self.model_2.root().child(row) )
        self.ui.listView.setCurrentIndex(index)

    def listview_clicked(self, index):
        selected_item = self.tableview_selected_item()
        selected_item.data('rect_items_index', index.row())
        self.graphics_view_update()

    def listview_delete_selected_item(self):
        selected_indexes = self.ui.listView.selectedIndexes()

        if len(selected_indexes) == 0:
            return

        selected_row = selected_indexes[0].row()

        self.model_2.removeRow(selected_row)
        selected_item = self.tableview_selected_item()
        
        del selected_item.data('rect_items')[selected_row]
        del selected_item.data('rect_alpha_items')[selected_row]
        del selected_item.data('rect_alpha_items_2')[selected_row]
        del selected_item.data('rects')[selected_row]
        del selected_item.data('crops')[selected_row]

        if selected_row - 1 < 0:
            row = 0
        else:
            row = selected_row - 1
        
        selected_item.data('rect_items_index', row)

        self.graphics_view_update()
        
    def tableview_clicked(self, index):
        self.graphics_view_update()
        self.ui.graphicsView.fitInView(self.ui.graphicsView.scene().sceneRect(), QtCore.Qt.KeepAspectRatio)

        clicked_item = index.internalPointer()
        self.listview_update(clicked_item)

        rect_items_index = clicked_item.data('rect_items_index')
        if rect_items_index is None:
            clicked_item.data('rect_items_index', 0)
            self.listview_set_current_index(0)
        else:
            self.listview_set_current_index(rect_items_index)

    def tableview_selected_item(self):
        selected_indexes = self.ui.tableView.selectedIndexes()
        if len(selected_indexes) == 0:
            return None
        return self.model.root().child( selected_indexes[0].row() )
    
    def split_cells(self):

        selected_item = self.tableview_selected_item()
        if selected_item is None:
            return
        rect_items = selected_item.data('rect_alpha_items_2')
        if rect_items is None or len(rect_items) == 0:
            return
        rect_counts = len(rect_items)
        qpixmap = selected_item.data('qpixmap')

        for i, rect_item in enumerate(rect_items):
            r = rect_item.rect()
            rect = QtCore.QRect( int(r.x()), int(r.y()), int(r.width()), int(r.height()) )
            cropped_qpixmap = qpixmap.copy(rect)
            selected_item.data('Rect'+str(i), cropped_qpixmap)
        
        column_count = self.model.columnCount()
        columns = [ self.model.headerData(c, QtCore.Qt.Horizontal) for c in range(column_count) ]
        append_columns = [ 'Rect'+str(i) for i in range(rect_counts) if not 'Rect'+str(i) in columns ]

        self.model.insertColumns(column_count, len(append_columns))
        for c, column in enumerate(append_columns):
            self.model.setHeaderData(column_count + c, QtCore.Qt.Horizontal, column)

    def cv2_image_to_qpixmap(self, cv2_image):
        h, w = cv2_image.shape[:2]

        if len(cv2_image.shape) == 3:
            qimg_format = QtGui.QImage.Format_RGB888
        else:
            qimg_format = QtGui.QImage.Format_Indexed8

        qimage = QtGui.QImage(cv2_image.flatten(), w, h, qimg_format)
        qpixmap = QtGui.QPixmap(qimage)
        return qpixmap

def main():
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow(app)
    window.show()
    app.exec()

if __name__ == '__main__':
    main()
