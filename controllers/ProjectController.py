import os

from .BaseController import BaseController

class ProjectController(BaseController):
    def __init__(self, project_id:str):
        super().__init__()
        
        self.project_path = os.path.join(self.files_path, project_id)
        if not os.path.exists(self.project_path):
            os.makedirs(self.project_path, exist_ok=True)
        