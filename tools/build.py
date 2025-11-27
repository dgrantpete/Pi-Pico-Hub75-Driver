import shutil
from pathlib import Path
import subprocess
import runpy
import itertools
import argparse

root_directory = Path(__file__).parent.parent
source_directory = root_directory / 'src'
build_directory = root_directory / 'build'
pico_directory = root_directory / 'pico'

parser = argparse.ArgumentParser(description="Build script for Pi-Pico-Hub75-Driver")

parser.add_argument(
    "-c",
    "--configuration",
    choices=["debug", "release"],
    default="debug",
    help="Build configuration (defaults to 'debug')"
)

parser.add_argument(
    "-a",
    "--arch",
    choices=["armv7emsp", "armv6m", "all"],
    default="all",
    help="""
    Target architecture (defaults to 'all'): setting specific architecture allows more .py files to be compiled
    RP2040 uses 'armv6m', RP2350 uses 'armv7emsp'
    """
)

parser.add_argument(
    "--cflags",
    nargs='*',
    default=['-O2', '-funroll-loops', '-finline-small-functions'],
    help="Additional C compiler flags (default flags tuned for optimal performance on RP2040 and RP2350)"
)

parser.add_argument(
    "--debug-files",
    nargs='*',
    default=['*/tests/*', '*/benchmarks.py', '*/unittest/*'],
    help="List of file patterns which will be ignored in release builds (default: tests and benchmarks)"
)

args = parser.parse_args()

if build_directory.exists():
    shutil.rmtree(build_directory)

if pico_directory.exists():
    shutil.rmtree(pico_directory)

build_directory.mkdir(parents=True, exist_ok=True)
pico_directory.mkdir(parents=True, exist_ok=True)

micropython_directory = root_directory / 'tools' / 'micropython'

constants = {}

for file in source_directory.rglob('constants.py'):
    constants |= {key: value for key, value in runpy.run_path(str(file)).items() if key.isupper()}

for file in source_directory.rglob('Makefile'):
    cflags_extra = ' '.join(itertools.chain(args.cflags, (f'-D{key}={value}' for key, value in constants.items())))
    
    make_flags = [
        f'-C{file.parent.as_posix()}',
        f'CFLAGS_EXTRA={cflags_extra}',
        f'MPY_DIR={micropython_directory.as_posix()}',
        f'BUILD={build_directory.as_posix()}'
    ]

    subprocess.run(
        ['make', *make_flags],
        check=True
    )

# Move compiled .mpy files to pico directory that were built when 'make' was called
for file in source_directory.rglob('*.mpy'):
    relative_path = file.relative_to(source_directory)

    output_path = pico_directory / relative_path
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    shutil.move(file, output_path)

for file in source_directory.rglob('*.py'):
    if args.configuration == 'release' and any(file.match(pattern) for pattern in args.debug_files):
        print(f"Skipping '{file}' in release build")
        continue

    relative_path = file.relative_to(source_directory)

    output_path = pico_directory / relative_path
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if args.configuration == 'debug':
        print(f"Copying '{file}' to '{output_path}' without compilation for debug build")
        shutil.copy2(file, output_path)
        continue

    try:
        print(f"Compiling '{file}' to '{output_path.with_suffix('.mpy')}'")

        mpy_cross_flags = [f'-o', str(output_path.with_suffix('.mpy')), str(file)]

        if args.arch != 'all':
            mpy_cross_flags.append(f'-march={args.arch}')

        subprocess.run(
            ['mpy-cross', *mpy_cross_flags],
            capture_output=True,
            check=True,
            text=True
        )

    except subprocess.CalledProcessError as e:
        # If we can't compile, we just copy the original .py file over
        if 'invalid arch' in e.stderr:
            print(f"Skipping compilation of '{file}': requires multiple compiled versions for different architectures, copying .py file directly")
            shutil.copy2(file, output_path)
            continue

        print(f"Error compiling {file}:")
        print(e.stderr or e.stdout)