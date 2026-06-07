from PyQt6.QtCore import Qt, QObject
import pyqtgraph as pg

class InteractionHandler(QObject):
    def __init__(self, main_window, controller):
        super().__init__()
        self.mw = main_window
        self.ctrl = controller
        self.dragging = None
        self.setup_events()

    def setup_events(self):
        scene = self.mw.scene_plot.scene()
        scene.sigMouseMoved.connect(self.on_move)
        scene.sigMouseClicked.connect(self.on_click)

    def on_move(self, pos):
        vb = self.mw.scene_plot.getViewBox()
        pt = vb.mapSceneToView(pos)
        
        x = max(-0.015, min(0.015, pt.y())) 

        if getattr(self.ctrl, 'pending_source_params', None) is not None:
            self.ctrl.update_preview_position(x)
            
        elif self.dragging:
            typ, idx = self.dragging
            if typ == 'source': 
                self.ctrl.config.x_src[idx] = x
            elif typ == 'slit': 
                self.ctrl.config.x_slit[idx] = x
            
            self.ctrl.on_params_changed()

    def on_click(self, event):
        vb = self.mw.scene_plot.getViewBox()
        pt = vb.mapSceneToView(event.scenePos())
        z, x = pt.x(), max(-0.015, min(0.015, pt.y()))

        if event.button() == Qt.MouseButton.LeftButton:
            if self.dragging:
                self.dragging = None
                return

            if getattr(self.ctrl, 'pending_source_params', None) is not None:
                self.ctrl.place_source_at(x)
                return
                
            for i, sx in enumerate(self.ctrl.config.x_src):
                if abs(x-sx) < 0.0005 and abs(z) < 0.02: 
                    self.dragging = ('source', i)
                    return
                    
            if hasattr(self.ctrl.config, 'x_slit'):
                for i, sx in enumerate(self.ctrl.config.x_slit):
                    if abs(x-sx) < 0.0005 and abs(z-self.ctrl.config.z_trans) < 0.02: 
                        self.dragging = ('slit', i)
                        return

        elif event.button() == Qt.MouseButton.RightButton:
            if getattr(self.ctrl, 'pending_source_params', None) is not None:
                self.ctrl.cancel_placement()
                return
                
            for i, sx in enumerate(self.ctrl.config.x_src):
                if abs(x-sx) < 0.0005 and abs(z) < 0.02: 
                    self.ctrl.remove_source(i)
                    return
                    
            if hasattr(self.ctrl.config, 'x_slit'):
                for i, sx in enumerate(self.ctrl.config.x_slit):
                    if abs(x-sx) < 0.0005 and abs(z-self.ctrl.config.z_trans) < 0.02:
                        del self.ctrl.config.x_slit[i]
                        self.ctrl.on_params_changed()
                        return