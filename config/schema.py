from pydantic import BaseModel, Field
from typing import List, Any

class SimulationConfig(BaseModel):
    """Глобальные настройки симуляции"""
    
    z_screen: float = 0.6        # Финальный экран 
    z_trans: float = 0.2         # Положение щелей
    wave_speed: float = 0.2      #  скорость 
    dt_anim: float = 0.033
    screen_resolution: int = 1000

    delta_lambda: float = 0.0
    spatial_samples: int = 10
    w_slit: float = 0.000008       
    slits_enabled: bool = False
    
    slit_distance: float = 0.002 # 2 мм 

    N_src: int = 0
    x_src: List[float] = Field(default_factory=list)
    lambdas: List[float] = Field(default_factory=list)
    E0: List[float] = Field(default_factory=list)
    phi0: List[float] = Field(default_factory=list) # Начальная фаза (рад)
    src_widths: List[float] = Field(default_factory=list)
    source_colors: List[Any] = Field(default_factory=list)

    x_slit: List[float] = Field(default_factory=list)