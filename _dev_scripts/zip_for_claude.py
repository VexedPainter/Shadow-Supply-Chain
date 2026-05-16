import os
import zipfile

def create_claude_zip(output_filename="shadow_supply_chain_for_claude.zip"):
    # Directories to completely ignore
    ignore_dirs = {'.git', '__pycache__', 'Include', 'Lib', 'Scripts', 'share', 'venv', 'env', 'node_modules'}
    # File extensions to ignore (binaries, logs, pdfs, databases)
    ignore_exts = {'.pyc', '.db', '.sqlite', '.sqlite3', '.log', '.pdf', '.zip'}
    
    with zipfile.ZipFile(output_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk('.'):
            # Modify dirs in-place to skip ignored directories
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            
            for file in files:
                # Check extension
                ext = os.path.splitext(file)[1].lower()
                if ext in ignore_exts:
                    continue
                
                # Check specific files to ignore
                if file == output_filename or file == 'zip_for_claude.py':
                    continue
                
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, '.')
                print(f"Adding: {arcname}")
                zipf.write(file_path, arcname)
                
    print(f"\nSuccessfully created {output_filename}")

if __name__ == "__main__":
    create_claude_zip()
