import shutil
from pathlib import Path
import subprocess

root_directory = Path(__file__).parent.parent
source_directory = root_directory / 'src'
build_directory = root_directory / 'build'

if build_directory.exists():
    shutil.rmtree(build_directory)

build_directory.mkdir(parents=True, exist_ok=True)

for file in source_directory.rglob('*.py'):
    relative_path = file.relative_to(source_directory)
    output_path = build_directory / relative_path.with_suffix('.mpy')
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    subprocess.run(
        ['mpy-cross', f'-o', str(output_path), '-march=armv6m', str(file)]
    )

for file in source_directory.rglob('*.pio'):
    relative_path = file.relative_to(source_directory)
    output_path = build_directory / relative_path.with_suffix('.py')

    output_path.parent.mkdir(parents=True, exist_ok=True)

    subprocess.run(
        ['pioasm', '-o', 'python', str(file), str(output_path)],
        cwd=source_directory,
        check=True
    )