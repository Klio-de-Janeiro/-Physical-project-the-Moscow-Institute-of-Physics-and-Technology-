from .schema import SimulationConfig

DEFAULT_CONFIG = SimulationConfig(
    z_screen=0.6,
    z_trans=0.2,
    wave_speed=0.1,
    slit_distance=0.002, # 2 мм
    N_src=0,
    x_src=[],
    lambdas=[],
    E0=[],
    phi0=[],
    src_widths=[],
    source_colors=[],
    x_slit=[]
)