"""Run with KiCad's pcbnew Python; modify only a new export copy."""
import argparse
import json
from pathlib import Path
import pcbnew as pcb

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    if args.output.exists() or args.output.resolve() == args.source.resolve():
        raise ValueError('Output must be new')
    board = pcb.LoadBoard(str(args.source))
    vias = [item for item in board.GetTracks() if isinstance(item, pcb.PCB_VIA)]
    for via in vias:
        board.Remove(via)
        via.thisown = False
    pcb.SaveBoard(str(args.output), board)
    print(json.dumps({'hidden_vias': len(vias), 'pads': len(list(board.GetPads())), 'source_modified': False}))
