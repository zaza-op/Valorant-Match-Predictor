import os

def get_folder_size(folder_path):
    total_size = 0
    file_count = 0
    
    for dirpath, dirnames, filenames in os.walk(folder_path):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            size = os.path.getsize(filepath)
            size_mb = size / (1024 * 1024)
            print(f"{filepath}: {size_mb:.2f} MB")
            total_size += size
            file_count += 1
    
    total_mb = total_size / (1024 * 1024)
    print(f"\nTotal: {total_mb:.2f} MB across {file_count} files")
    return total_mb

# Check your processed data
get_folder_size("data/raw/")