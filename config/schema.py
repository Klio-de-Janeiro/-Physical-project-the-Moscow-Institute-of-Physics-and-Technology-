from pydantic import BaseModel, Field
from typing import List, Any

class SimulationConfig(BaseModel):
    """Глобальные настройки симуляции"""
    
    # Геометрия сцены
    z_screen: float = 0.6        # Финальный экран (поменяли на 0.6 по твоему ТЗ)
    z_trans: float = 0.2         # Положение преграды (щелей)
    wave_speed: float = 0.2      # Оптимальная скорость для мм-масштаба
    dt_anim: float = 0.033
    screen_resolution: int = 1000

    # Настройки когерентности и щелей
    delta_lambda: float = 0.0
    spatial_samples: int = 10
    w_slit: float = 0.0005       # 0.5 мм ширина щели
    slits_enabled: bool = False
    
    # НОВОЕ: дистанция между щелями (в метрах)
    slit_distance: float = 0.002 # 2 мм по умолчанию

    # --- ИСТОЧНИКИ ---
    N_src: int = 0
    x_src: List[float] = Field(default_factory=list)
    lambdas: List[float] = Field(default_factory=list)
    E0: List[float] = Field(default_factory=list)
    phi0: List[float] = Field(default_factory=list) # Начальная фаза (рад)
    src_widths: List[float] = Field(default_factory=list)
    source_colors: List[Any] = Field(default_factory=list)

    # --- ЩЕЛИ ---
    x_slit: List[float] = Field(default_factory=list)