import os, random, string

from helpers import Settings, get_settings

class BaseController:
    def __init__(self):
        self.src_path = os.path.dirname(os.path.dirname(__file__))    
        self.files_path = os.path.join(self.src_path, "assets/uploaded_real_files")

        if not os.path.exists(self.files_path):
            os.makedirs(self.files_path, exist_ok=True)

        self.app_settings = get_settings()
    
    def generate_random_string(self, k:int = 10):
        return "".join( random.choices(string.ascii_letters+string.digits, k=k) )
    

