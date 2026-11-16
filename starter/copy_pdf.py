"""Copy a source PDF supplied by the student; no machine-specific paths."""
import argparse
import shutil
from pathlib import Path


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--source',required=True,type=Path)
    parser.add_argument('--output',type=Path,default=Path(__file__).resolve().parents[1]/'data/cme2._suy_timgs_minh.pdf')
    args=parser.parse_args()
    if args.output.exists():raise ValueError('Destination exists; choose a new output to preserve the original.')
    args.output.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(args.source,args.output)
    print('Copied PDF to',args.output)

if __name__=='__main__':main()
