from fastapi import UploadFile
import os, re

from .BaseController import BaseController
from constants import ResponseSignal



class DataController(BaseController):
    def __init__(self, ):
        super().__init__()
        self.conversion_factor = 1048576   # from mega bytes to bytes

    def validate_file(self, file:UploadFile):
        if file.headers["content-type"] not in self.app_settings.FILE_ALLOWED_TYPES:
            return False, ResponseSignal.FILE_TYPE_NOT_SUPPORTED.value

        if self.app_settings.FILE_MAX_SIZE * self.conversion_factor < file.size:
            return False, ResponseSignal.FILE_SIZE_EXCEEDED.value
        
        return True, None

    def get_clean_file_name(self, orig_file_name: str):
        # remove any special charactsers, except underscore and .
        cleaned_file_name = re.sub(r'[^\w.]', '', orig_file_name.strip())
        # replace spaces with underscore
        cleaned_file_name = cleaned_file_name.replace(" ", "_")
        return cleaned_file_name
    
    def get_file_name(self, project_id:str, orig_file_name:str):
        random_token = self.generate_random_string()
        orig_file_name = self.get_clean_file_name(orig_file_name)
        file_path = os.path.join(self.files_path, project_id, random_token+"_"+orig_file_name)
        while os.path.exists(file_path):
            random_token = self.generate_random_string()
            file_path = os.path.join(self.files_path, project_id, random_token+"_"+orig_file_name)
        return file_path, random_token+"_"+orig_file_name
    

