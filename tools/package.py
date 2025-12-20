import shutil
import json
import zipfile
from pathlib import Path
import argparse

root_directory = Path(__file__).parent.parent

parser = argparse.ArgumentParser(description="Package built files into release assets with mip-compatible manifest")

parser.add_argument(
    "version",
    type=str,
    help="Release version (e.g., v1.0.0)"
)

parser.add_argument(
    "-i",
    "--input",
    type=Path,
    required=True,
    help="Input directory containing built files from build.py"
)

parser.add_argument(
    "-o",
    "--output",
    type=Path,
    default="release-assets",
    help="Output directory for release assets (defaults to 'release-assets')"
)

parser.add_argument(
    "-m",
    "--manifest",
    type=str,
    default=None,
    help="Name of the manifest file to generate (defaults to 'package.json' or 'package-{variant}.json')"
)

parser.add_argument(
    "-v",
    "--variant",
    type=str,
    default="",
    help="Build variant (e.g., 'dev') - affects zip name and file encoding"
)

parser.add_argument(
    "-r",
    "--repository",
    type=str,
    required=True,
    help="GitHub repository in 'owner/repo' format (required)"
)

args = parser.parse_args()

# Derive manifest name from variant if not explicitly provided
if args.manifest is None:
    if args.variant:
        args.manifest = f"package-{args.variant}.json"
    else:
        args.manifest = "package.json"

# Resolve input directory
if args.input.is_absolute():
    input_directory = args.input
else:
    input_directory = root_directory / args.input

if not input_directory.exists():
    raise FileNotFoundError(f"Input directory does not exist: {input_directory}")

# Resolve output directory
if args.output.is_absolute():
    output_directory = args.output
else:
    output_directory = root_directory / args.output

output_directory.mkdir(parents=True, exist_ok=True)

# Strip 'v' prefix from version for package.json version field
version_number = args.version.lstrip('v')

# Build the base URL for release assets
base_url = f"https://github.com/{args.repository}/releases/download/{args.version}"

# Determine zip filename based on variant
if args.variant:
    zip_filename = f"hub75-{args.version}-{args.variant}.zip"
else:
    zip_filename = f"hub75-{args.version}.zip"

zip_path = output_directory / zip_filename

# Collect URL mappings for package.json
url_mappings = []

# Create zip file with original structure
print(f"Creating zip archive: {zip_path}")
with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
    # Process all files in input directory
    for file in input_directory.rglob('*'):
        if file.is_dir():
            continue

        # Get path relative to input directory
        relative_path = file.relative_to(input_directory)

        # Add to zip with original structure
        zip_file.write(file, relative_path)

        # Build flattened filename using . as separator
        # Format: [variant.]path.segments.filename.ext
        path_parts = relative_path.parts
        if args.variant:
            flattened_name = args.variant + '.' + '.'.join(path_parts)
        else:
            flattened_name = '.'.join(path_parts)

        # Destination path in package.json (where mip installs to on device)
        # Only include files under lib/ in the mip manifest - mip is for the library,
        # not demo files like main.py. Users can get the full demo from the zip.
        destination_path = relative_path.as_posix()
        if destination_path.startswith('lib/'):
            # Strip 'lib/' prefix since mip already installs to /lib by default
            destination_path = destination_path[4:]
        else:
            # Skip non-library files (like main.py) from mip manifest
            # They're still included in the zip for manual installation
            continue

        # Source URL for the flattened file
        source_url = f"{base_url}/{flattened_name}"

        # Copy file to output with flattened name
        output_path = output_directory / flattened_name
        print(f"Packaging '{relative_path}' -> '{flattened_name}'")
        shutil.copy2(file, output_path)

        # Add to URL mappings
        url_mappings.append([destination_path, source_url])

# Sort mappings for consistent output
url_mappings.sort(key=lambda mapping: mapping[0])

# Generate package.json
package_manifest = {
    "urls": url_mappings,
    "version": version_number
}

manifest_path = output_directory / args.manifest
print(f"Writing manifest to '{manifest_path}'")

with open(manifest_path, 'w') as manifest_file:
    json.dump(package_manifest, manifest_file, indent=2)

print(f"Packaged {len(url_mappings)} files for release {args.version}")
print(f"  Zip: {zip_filename}")
print(f"  Manifest: {args.manifest}")
if args.variant:
    print(f"  Variant: {args.variant}")
