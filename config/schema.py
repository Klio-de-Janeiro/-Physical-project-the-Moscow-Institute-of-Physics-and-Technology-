from pydantic import BaseModel, Field, model_validator
from typing import List

class SimulationConfig(BaseModel):
    N_src: int = Field(0, ge=0, le=10)
    x_src: List[float] = []
    wave_speed: float = Field(0.2, ge=0.01, le=2.0)   # ✅ добавлено
    lambdas: List[float] = []
    E0: List[float] = []
    phi0: List[float] = []
    source_colors: List[str] = []
    src_widths: List[float] = []
    delta_lambda: float = Field(0.0, ge=0, le=50e-9)
    z_trans: float = Field(0.2, ge=0.01, le=1.0)
    x_slit: List[float] = []
    w_slit: float = Field(1e-4, ge=1e-6, le=1e-3)
    z_screen: float = Field(0.5, ge=0.1, le=2.0)
    dt_emit: float = Field(1.0, ge=0.5, le=3.0)
    dt_anim: float = Field(0.033, ge=0.016, le=0.05)
    spatial_samples: int = Field(20, ge=1, le=100)
    screen_resolution: int = Field(400, ge=100, le=1000)

    @model_validator(mode='after')
    def check_lengths(self):
        src_fields = [self.x_src, self.lambdas, self.E0, self.phi0, self.source_colors, self.src_widths]
        for f in src_fields:
            if len(f) != self.N_src:
                raise ValueError(f'List length must match N_src={self.N_src}')
        return self