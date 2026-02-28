import argparse
import os
import sys

# Add the project root to sys.path so the app package can be imported
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app.cmake import CMakeFileGenerator

# Ensure relative paths (e.g. 'main.py', 'build/') resolve relative to this script's directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

parser = argparse.ArgumentParser()
parser.add_argument('--nthreads', '-t', type=int, default=4,
                    help='Number of threads to use')
args = parser.parse_args()

c = CMakeFileGenerator('01-basic', outputdir='build', nthreads=args.nthreads)
c.add_tree('tree1')
c.add_file('main.py')
c.modules['main'].set_as_main()
c.run()
