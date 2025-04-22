import os

def get_image_path(image_name):
    """
    Get the absolute path for an image file.
    This ensures images can be found regardless of where the application is run from.
    """
    # Get the directory where the current file (path_utils.py) is located
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Construct the path to the images folder
    images_dir = os.path.join(current_dir, "images")
    # Return the full path to the requested image
    return os.path.join(images_dir, image_name) 

def get_database_path(file_name):
    """
    Get the absolute path for a database file.
    This ensures database files can be found regardless of where the application is run from.
    
    Args:
        file_name (str): Name of the database file (e.g., 'users.txt', 'tasks.txt', etc.)
        
    Returns:
        str: Absolute path to the database file
    """
    # Get the directory where the current file (path_utils.py) is located
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Construct the path to the database folder
    database_dir = os.path.join(current_dir, "database")
    # Return the full path to the requested database file
    return os.path.join(database_dir, file_name) 