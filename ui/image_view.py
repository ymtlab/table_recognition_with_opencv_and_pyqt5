# -*- coding: utf-8 -*-
from PyQt5 import QtWidgets, QtCore, QtGui
from .image_view_ui import Ui_Form
from model import Model
from item import Item
from delegate import Delegate
from column import Column
from image_process import ImageProcess

class ImageView(QtWidgets.QWidget):
    def __init__(self, parent):
        super().__init__(parent)

        self.ui = Ui_Form()
        self.ui.setupUi(self)

        self.model = Model( self, Item(), Column(['column']) )

        self.ui.listView.setModel(self.model)
        self.ui.listView.setItemDelegate( Delegate() )
        self.ui.listView.clicked.connect(self.listview_clicked)
        self.ui.listView.customContextMenuRequested.connect(self.context_menu)

        self.ui.horizontalSlider.valueChanged.connect(self.slider_changed)
        self.ui.horizontalSlider_2.valueChanged.connect(self.slider_changed)

        self.ui.lineEdit.returnPressed.connect(
            lambda : self.lineedit_changed(self.ui.horizontalSlider, self.ui.lineEdit)
        )
        self.ui.lineEdit_2.returnPressed.connect(
            lambda : self.lineedit_changed(self.ui.horizontalSlider_2, self.ui.lineEdit_2)
        )

        self.ui.graphicsView.setScene( QtWidgets.QGraphicsScene(self.ui.graphicsView) )

    def context_menu(self, point):
        menu = QtWidgets.QMenu(self)
        menu.addAction('Delete', self.delete_selected_item)
        menu.exec( self.focusWidget().mapToGlobal(point) )

    def delete_selected_item(self):
        mainwindow = self.mainwindow(self)
        if mainwindow is None:
            tableview_item = None
        else:
            tableview_item = mainwindow.tableview_selected_item()
        
        selected_indexes = self.ui.listView.selectedIndexes()
        for index in selected_indexes[::-1]:
            row = index.row()
            self.model.removeRow(row)
            
            if tableview_item is None:
                continue
            
            for key in ['rects', 'crops']:
                del tableview_item.data(key)[row]
            
            if row - 1 < 0:
                r = 0
            else:
                r = row - 1
            
            tableview_item.data('rects_index', r)

        self.graphics_view_update()

    def lineedit_changed(self, slider, lineedit):
        slider.setValue( int(lineedit.text()) ) 

    def listview_clicked(self, index):
        mainwindow = self.mainwindow(self)
        if mainwindow is None:
            return
        
        tableview_item = mainwindow.tableview_selected_item()
        if tableview_item is None:
            return
        
        tableview_item.data('rects_index', self.ui.listView.selectedIndexes()[0].row())
        self.graphics_view_update()

    def mainwindow(self, widget):
        if widget is None:
            return None
        if widget.inherits('QMainWindow'):
            return widget
        return self.mainwindow( widget.parent() )

    def graphics_view_update(self):
        mainwindow = self.mainwindow(self)
        tableview_item = mainwindow.tableview_selected_item()
        if tableview_item is None:
            return

        scene = self.ui.graphicsView.scene()

        for item in scene.items():
            scene.removeItem(item)

        if mainwindow.tool_bar.ui.toolButton_5.isChecked():
            qpixmap = tableview_item.data('edge')
        else:
            qpixmap = tableview_item.data('qpixmap')
        if not qpixmap is None:
            scene.setSceneRect( QtCore.QRectF(qpixmap.rect()) )
            scene.addPixmap(qpixmap)

        rects = tableview_item.data('rects')
        crops = tableview_item.data('crops')

        if mainwindow.tool_bar.ui.toolButton_6.isChecked() and not rects is None:
            for rect in rects:
                scene.addItem( self.rect_item(rect, 0, 0, 255, 200, 2) )

        if mainwindow.tool_bar.ui.toolButton_7.isChecked() and not crops is None:
            for crop in crops:
                scene.addItem( self.rect_item(crop, 0, 255, 0, 200, 2) )

        if not rects is None and len(rects) > 0:
            rect = rects[ tableview_item.data('rects_index') ]
            scene.addItem( self.rect_item(rect, 255, 0, 0, 255, 4) )

    def recognize(self):
        mainwindow = self.mainwindow(self)
        if mainwindow is None:
            return

        tableview_item = mainwindow.tableview_selected_item()
        if tableview_item is None:
            return
        
        area_range = ( self.ui.horizontalSlider.value(), self.ui.horizontalSlider_2.value() )
        image_process = ImageProcess( tableview_item.data('qpixmap') )
        edge, rects, crops = image_process.recognize_table(area_range)
        
        tableview_item.data('rects_index', 0)
        tableview_item.data('edge', edge)
        tableview_item.data('rects', rects)
        tableview_item.data('crops', crops)

        self.graphics_view_update()

    def rect_item(self, rect, r, g, b, a, pen_width):
        color = QtGui.QColor(r, g, b, a)
        rect_item = QtWidgets.QGraphicsRectItem()
        rect_item.setRect( rect[0], rect[1], rect[2], rect[3] )
        pen = QtGui.QPen(color)
        pen.setWidth(pen_width)
        rect_item.setPen(pen)
        return rect_item

    def set_current_index(self, row):
        if self.model.rowCount() == 0:
            return
        index = self.model.createIndex( row, 0, self.model.root().child(row) )
        self.ui.listView.setCurrentIndex(index)

    def slider_changed(self):
        self.ui.lineEdit.setText( str(self.ui.horizontalSlider.value()) )
        self.ui.lineEdit_2.setText( str(self.ui.horizontalSlider_2.value()) )
        self.recognize()
        self.graphics_view_update()

    def update_rows(self, tableview_item):
        rects = tableview_item.data('rects')
        if rects is None:
            return

        if self.model.rowCount() > 0:
            self.model.removeRows(0, self.model.rowCount())

        self.model.insertRows( 0, len(rects) )
        children = self.model.root().children()
        for r, list_item in enumerate(children):
            list_item.data('column', 'Rect'+str(r))
