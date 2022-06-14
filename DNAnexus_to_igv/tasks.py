# task to delete all directories and zip in static/tmp
# import os
# import dxpy as dx

# from dotenv import find_dotenv, load_dotenv
# from .find_bam import get_002_projects, find_dx_bams

# def update_json():
#     load_dotenv(find_dotenv())

#     AUTH_TOKEN = os.environ["AUTH_TOKEN"]

#     # env variable for dx authentication
#     DX_SECURITY_CONTEXT = {
#         "auth_token_type": "Bearer",
#         "auth_token": AUTH_TOKEN
#     }

#     # set token to env
#     dx.set_security_context(DX_SECURITY_CONTEXT)

#     project_002_list = get_002_projects()

#     find_dx_bams(project_002_list)
        