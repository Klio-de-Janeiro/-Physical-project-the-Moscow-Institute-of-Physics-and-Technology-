class SceneManager:
    def world_to_view(self, z, x, view_range):
        """Упрощённое преобразование для pyqtgraph (автоматическое)"""
        return z, x
    def view_to_world(self, z, x):
        return z, x