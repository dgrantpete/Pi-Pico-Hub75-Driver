import shutil
from pathlib import Path
import subprocess
import runpy
import itertools

root_directory = Path(__file__).parent.parent
source_directory = root_directory / 'src'
build_directory = root_directory / 'build'
pico_directory = root_directory / 'pico'

cflags = ['-O2', '-funroll-loops', '-finline-small-functions']

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
    cflags_extra = ' '.join(itertools.chain(cflags, (f'-D{key}={value}' for key, value in constants.items())))

    subprocess.run(
        [
            'make',
            f'-C{file.parent.as_posix()}',
            f'CFLAGS_EXTRA={cflags_extra}',
            f'MPY_DIR={micropython_directory.as_posix()}',
            f'BUILD={build_directory.as_posix()}'
        ],
        check=True
    )

# Move compiled .mpy files to pico directory that were built when 'make' was called
for file in source_directory.rglob('*.mpy'):
    relative_path = file.relative_to(source_directory)

    output_path = pico_directory / relative_path
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    shutil.move(file, output_path)

for file in source_directory.rglob('*.py'):
    relative_path = file.relative_to(source_directory)

    output_path = pico_directory / relative_path
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        subprocess.run(
            ['mpy-cross', f'-o', str(output_path.with_suffix('.mpy')), str(file)],
            capture_output=True,
            check=True,
            text=True
        )

    except subprocess.CalledProcessError as e:
        # If we can't compile, we just copy the original .py file over
        if 'invalid arch' in e.stderr:
            print(f"Skipping '{file}': cannot be compiled due to specific architecture requirements")

            shutil.copy2(file, output_path)
            
            continue

        print(f"Error compiling {file}:")
        print(e)

        raise