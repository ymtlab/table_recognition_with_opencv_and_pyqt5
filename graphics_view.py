# -*- coding: utf-8 -*-
from PyQt5 import QtWidgets, QtCore, QtGui

class GraphicsView(QtWidgets.QGraphicsView):
    def __init__(self, *argv, **keywords):
        super(GraphicsView, self).__init__(*argv, **keywords)
        self._numScheduledScalings = 0
        self.coordinates = []

    def wheelEvent(self, event):
        numDegrees = event.angleDelta().y() / 8
        numSteps = numDegrees / 15
        self._numScheduledScalings += numSteps
        if self._numScheduledScalings * numSteps < 0:
            self._numScheduledScalings = numSteps
        anim = QtCore.QTimeLine(350, self)
        anim.setUpdateInterval(20)
        anim.valueChanged.connect(self.scalingTime)
        anim.finished.connect(self.animFinished)
        anim.start()

    def scalingTime(self, x):
        factor = 1.0 + float(self._numScheduledScalings) / 300.0
        self.scale(factor, factor)

    def animFinished(self):
        if self._numScheduledScalings > 0:
            self._numScheduledScalings -= 1
        else:
            self._numScheduledScalings += 1
        
    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.MidButton:
            self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)

            event = QtGui.QMouseEvent(
                QtCore.QEvent.GraphicsSceneDragMove, 
                event.pos(), 
                QtCore.Qt.MouseButton.LeftButton, 
                QtCore.Qt.MouseButton.LeftButton, 
                QtCore.Qt.KeyboardModifier.NoModifier
            )

        elif event.button() == QtCore.Qt.LeftButton:
            self.setDragMode(QtWidgets.QGraphicsView.RubberBandDrag)
            p = self.mapToScene(event.pos())
            self.coordinates = [p.x(), p.y()]

        QtWidgets.QGraphicsView.mousePressEvent(self, event)
   
    def mouseReleaseEvent(self, event):
        QtWidgets.QGraphicsView.mouseReleaseEvent(self, event)
        self.setDragMode(QtWidgets.QGraphicsView.NoDrag)

        if event.button() == QtCore.Qt.LeftButton:
            # set coordinates in draw shapes
            p = self.mapToScene(event.pos())
            self.coordinates.extend([p.x(), p.y()])
            items, model = self.drawshapes_from_mainwindow(self)
            if items is None:
                return
            for item in items:
                item.set_data( 'Page size', ','.join([str(int(p)) for p in self.coordinates]) )
                parent = model.index(item.parent().row(), 0, QtCore.QModelIndex())
                index = model.index(item.row(), 0, parent)
                model.dataChanged.emit(index, index)

    def find_mainwindow(self, parent):
        if parent is None:
            return None
        if parent.inherits('QMainWindow'):
            return parent
        return self.find_mainwindow(parent.parent())

    def drawshapes_from_mainwindow(self, is_selected=False):
        try:
            mainwindow = self.find_mainwindow(self)
            dock = mainwindow.findChild(QtWidgets.QDockWidget, 'dockWidgetDrawshapes')
            treeView = dock.findChild(QtWidgets.QTreeView)
            if is_selected:
                return [ index.internalPointer() for index in treeView.selectedIndexes() ], treeView.model()
            else:
                return [ child for child in treeView.model().root_item.children() ], treeView.model()
        except:
            return [], None
