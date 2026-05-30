import unittest
import numpy as np
from physics.coherence import compute_interference_pattern

class TestPhysics(unittest.TestCase):
    def test_two_slit_coherent(self):
        x = np.linspace(-0.1, 0.1, 200)
        I = compute_interference_pattern(x, [-0.05, 0.05], [550e-9, 550e-9], [1,1], [0,0], [-0.02,0.02], 1e-4, 0.2, 0.5, 0, 0, 10)
        maxI = np.max(I)
        minI = np.min(I)
        visibility = (maxI - minI)/(maxI + minI)
        self.assertGreater(visibility, 0.9)

    def test_temporal_decoherence(self):
        x = np.linspace(-0.1, 0.1, 200)
        I_coherent = compute_interference_pattern(x, [-0.05, 0.05], [550e-9, 550e-9], [1,1], [0,0], [-0.02,0.02], 1e-4, 0.2, 0.5, 0, 0, 10)
        I_decoherent = compute_interference_pattern(x, [-0.05, 0.05], [550e-9, 550e-9], [1,1], [0,0], [-0.02,0.02], 1e-4, 0.2, 0.5, 50e-9, 0, 10)
        def visibility(I):
            return (np.max(I)-np.min(I))/(np.max(I)+np.min(I))
        self.assertGreater(visibility(I_coherent), visibility(I_decoherent))

if __name__ == '__main__':
    unittest.main()