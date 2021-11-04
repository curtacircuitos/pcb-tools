import os
from gerber.pcb import PCB


def test_from_directory():
    test_pcb = PCB.from_directory(os.path.join(os.path.dirname(__file__), 'resources//eagle_files'))
    assert len(test_pcb.layers) == 11  # Checks all the available layer files have been read or not.
