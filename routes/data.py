from fastapi import APIRouter, Depends, Body, UploadFile, File, status, BackgroundTasks
from fastapi.responses import JSONResponse
from pathlib import Path
import aiofiles
import uuid

from helpers import get_settings, Settings
from controllers import DataController, ProcessController, ProjectController, TextStorageService



dataRoute = APIRouter(
    prefix="/api/TA",
    tags=["data_route"]
)

# ----------------------
# Helper to run blocking code in threadpool
# ----------------------
import asyncio
def run_in_thread(func, *args, **kwargs):
    loop = asyncio.get_running_loop()
    return loop.run_in_executor(None, lambda: func(*args, **kwargs))

@dataRoute.post("/fileProcessing")
async def upload_file_and_extract_then_save_it(
        background_tasks: BackgroundTasks,
        app_settings: Settings = Depends(get_settings),
        project_id: str = Body(..., embed=True),
        file: UploadFile = File(...)
    ):

    # ----------------------
    # 0. Generate thread_id
    # ----------------------
    thread_id = str(uuid.uuid4())

    data_controller = DataController()
    # ----------------------
    # 1. Validate file
    # ----------------------
    is_valid, message = DataController().validate_file(file)
    if not is_valid:
        return JSONResponse(
            content={"error": message},
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # ----------------------
    # 2. Prepare project folder
    # ----------------------
    project_controller = ProjectController(project_id)
    save_path, stored_file_name = DataController().get_file_name(project_id, file.filename)

    # Make sure folder exists
    Path(save_path).parent.mkdir(parents=True, exist_ok=True)

    # ----------------------
    # 3. Save uploaded file asynchronously
    # ----------------------
    async with aiofiles.open(save_path, "wb") as f:
        content = await file.read()
        await f.write(content)

    # ----------------------
    # 4. Extract content (blocking - consider moving to background for large files)
    # ----------------------
    loaded_text = await run_in_thread(ProcessController.extract_content, save_path)

    # ----------------------
    # 5. Save extracted text asynchronously
    # ----------------------
    clean_file_path = await TextStorageService.save_text(project_id, stored_file_name, loaded_text)

    # ----------------------
    # 6. Return response
    # ----------------------
    return {
        "status": status.HTTP_200_OK,
        "thread_id": thread_id,
        "message": "File processed successfully",
        "uploaded_file": stored_file_name,
        "text_file": clean_file_path
    }










