import random

from Fill import distribute_items_restrictive

from . import TMNTTestBase


class TestSoloFillIsReliable(TMNTTestBase):
    """A TMNT-only multiworld once failed to fill in ~20% of seeds (10 progression items in 10 locations)."""

    def test_solo_fill_is_reliable(self):
        rng = random.Random(0xD0A1)
        for _ in range(100):
            self.world_setup(seed=rng.getrandbits(64))
            distribute_items_restrictive(self.multiworld)
