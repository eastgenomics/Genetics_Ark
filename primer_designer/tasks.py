# task to delete all directories and zip in static/tmp
# import os, shutil
# from pathlib import Path

# BASEDIR = Path(__file__).parent.parent.absolute()

# def delete_dirs():
#     """
#     Deletes all directories and zip in static/tmp
#     """

#     folder = f'{BASEDIR}/static/tmp'
#     print(f'Deleting files in {folder}')

#     for filename in os.listdir(folder):
#         file_path = os.path.join(folder, filename)
#         try:
#             if os.path.isfile(file_path) or os.path.islink(file_path):
#                 os.unlink(file_path)
#             elif os.path.isdir(file_path):
#                 shutil.rmtree(file_path)
#         except Exception as err:
#             print(f'Failed to delete {file_path} due to {err}')