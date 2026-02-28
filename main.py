from app.cmake import CMakeFileGenerator

def pypperoni(project, outputdir, nthreads):
    return CMakeFileGenerator(project, outputdir, nthreads)

if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument('project', help='Path to the project to compile')

    parser.add_argument('--outputdir', '-o', default='build',
                        help='Directory to output the build files')

    parser.add_argument('--nthreads', '-t', type=int, default=4,
                        help='Number of threads to use')

    parser.add_argument('--files', '-f', nargs='*',
                        help='Files to include in the build')

    parser.add_argument('--directories', '-d', nargs='*',
                        help='Directories to include in the build')

    args = parser.parse_args()

    pypperoni(args.project, args.outputdir, args.nthreads)