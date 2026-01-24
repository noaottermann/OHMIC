from PyQt5.QtWidgets import QGraphicsLineItem, QGraphicsRectItem, QGraphicsItem
from PyQt5.QtGui import QPen, QColor, QBrush
from PyQt5.QtCore import Qt, QPointF, QLineF

class WireHandle(QGraphicsRectItem):
    def __init__(self, parent_wire):
        # Carré de 8x8 centré
        super().__init__(-4, -4, 8, 8, parent=parent_wire)
        self.parent_wire = parent_wire
        
        self.setBrush(QBrush(Qt.white))
        self.setPen(QPen(Qt.black, 1))
        
        self.setFlags(QGraphicsItem.ItemSendsGeometryChanges)
        self.setZValue(2) # Toujours au-dessus du fil
        self.setCursor(Qt.PointingHandCursor)
        self.setVisible(False)
        
        # État pour le drag manuel
        self._is_dragging = False

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._is_dragging = True
            # On capture la souris pour recevoir les mouseMove même si on sort du carré
            event.accept() 
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._is_dragging:
            # 1. On calcule la nouvelle position dans le référentiel du PARENT
            # event.pos() est local au Handle. mapToParent transforme ça vers le Wire.
            new_pos_in_parent = self.mapToParent(event.pos())
            
            # 2. On bouge le Handle manuellement
            self.setPos(new_pos_in_parent)
            
            # 3. On met à jour la ligne visuelle
            self.parent_wire.update_line_visuals()
            
            # 4. On bloque l'événement pour qu'il ne remonte PAS au parent
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._is_dragging:
            self._is_dragging = False
            # Fin du mouvement : on appelle la scène pour le snapping et la logique
            self.scene().handle_wire_move(self.parent_wire)
            event.accept()
        else:
            super().mouseReleaseEvent(event)


class WireItem(QGraphicsLineItem):
    def __init__(self, wire_model):
        super().__init__()
        self.wire = wire_model
        
        self.setPen(QPen(Qt.black, 2))
        self.setFlags(QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemIsMovable)
        self.setZValue(0) # Le fil est en dessous des poignées
        
        self.handle_a = WireHandle(self)
        self.handle_b = WireHandle(self)
        
        self.refresh_geometry()

    def refresh_geometry(self):
        """
        Recale tout le monde proprement
        """
        if not self.wire.node_a or not self.wire.node_b:
            return

        # On remet le parent à l'origine absolue
        self.prepareGeometryChange()
        self.setPos(0, 0)

        # Coordonnées absolues
        p1 = QPointF(*self.wire.node_a.position)
        p2 = QPointF(*self.wire.node_b.position)

        # On place les éléments à ces coordonnées
        self.handle_a.setPos(p1)
        self.handle_b.setPos(p2)
        self.setLine(QLineF(p1, p2))

    def update_line_visuals(self):
        """Met à jour juste le trait noir entre les carrés"""
        self.setLine(QLineF(self.handle_a.pos(), self.handle_b.pos()))

    def itemChange(self, change, value):
        # Gestion Sélection
        if change == QGraphicsItem.ItemSelectedChange:
            is_selected = bool(value)
            self.handle_a.setVisible(is_selected)
            self.handle_b.setVisible(is_selected)
            
            pen = self.pen()
            if is_selected:
                pen.setColor(QColor("#0078d7"))
                pen.setStyle(Qt.DashLine)
                # On reste derrière les handles (Z=2), mais devant les autres fils
                self.setZValue(1) 
            else:
                pen.setColor(Qt.black)
                pen.setStyle(Qt.SolidLine)
                self.setZValue(0)
            self.setPen(pen)

        return super().itemChange(change, value)

    def mouseReleaseEvent(self, event):
        """Fin du déplacement gobal du fil"""
        super().mouseReleaseEvent(event)
        
        # Si on a bougé le fil entier
        if self.pos().manhattanLength() > 0.1:
             if self.scene():
                 self.scene().handle_wire_move(self)