import os

def get_image_path(image_name):
    """
    Dapatkan path absolut untuk file gambar.
    Memastikan gambar dapat ditemukan terlepas dari lokasi aplikasi dijalankan.
    """
    # Get the directory where the current file (path_utils.py) is located
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Go up one level to reach the project root
    project_root = os.path.dirname(current_dir)
    # Construct the path to the images folder
    images_dir = os.path.join(project_root, "images")
    # Return the full path to the requested image
    return os.path.join(images_dir, image_name) 

def get_database_path(file_name):
    """
    Dapatkan path absolut untuk file database.
    Memastikan file database dapat ditemukan terlepas dari lokasi aplikasi dijalankan.
    
    Args:
        file_name (str): Nama file database (contoh: 'users.txt', 'tasks.txt', dll)
        
    Returns:
        str: Path absolut ke file database
    """
    # Get the directory where the current file (path_utils.py) is located
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Go up one level to reach the project root
    project_root = os.path.dirname(current_dir)
    # Construct the path to the database folder
    database_dir = os.path.join(project_root, "database")
    # Return the full path to the requested database file
    return os.path.join(database_dir, file_name) 