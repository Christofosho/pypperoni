import argparse
import os
import sys

# Add the parent of the pypperoni package to sys.path so it can be imported as a package
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from pypperoni.cmake import CMakeFileGenerator

# Ensure relative paths (e.g. 'main.py', 'build/') resolve relative to this script's directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

parser = argparse.ArgumentParser()
parser.add_argument('--nthreads', '-t', type=int, default=4,
                    help='Number of threads to use')
args = parser.parse_args()

c = CMakeFileGenerator('02-exceptions', outputdir='build', nthreads=args.nthreads)
c.add_file('main.py')
c.modules['main'].set_as_main()
c.run()
