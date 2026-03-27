from fastapi import APIRouter, UploadFile, File, HTTPException, status
from fastapi.responses import FileResponse
from typing import List, Dict, Any
import os
import shutil
from datetime import datetime

from schemas.schemas import UploadResponse
from core.config import settings

router = APIRouter()


@router.post("/file", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(file: UploadFile = File(...)):
    """Upload a single file to the system"""
    try:
        # Validate file type
        allowed_extensions = {'.txt', '.pdf', '.md'}
        file_ext = os.path.splitext(file.filename)[1].lower()

        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的文件类型。支持的格式: {', '.join(allowed_extensions)}"
            )

        # Create upload directory if it doesn't exist
        upload_dir = os.path.join(settings.UPLOAD_DIR, datetime.now().strftime("%Y-%m-%d"))
        os.makedirs(upload_dir, exist_ok=True)

        # Save file
        file_path = os.path.join(upload_dir, file.filename)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        file_size = os.path.getsize(file_path)

        return UploadResponse(
            message="文件上传成功",
            file_name=file.filename,
            file_size=file_size,
            file_path=file_path,
            uploaded_at=datetime.now()
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文件上传失败: {str(e)}"
        )


@router.post("/multiple")
async def upload_multiple_files(files: List[UploadFile] = File(...)):
    """Upload multiple files at once"""
    results = []
    errors = []

    for file in files:
        try:
            # Validate file type
            allowed_extensions = {'.txt', '.pdf', '.md'}
            file_ext = os.path.splitext(file.filename)[1].lower()

            if file_ext not in allowed_extensions:
                errors.append({
                    "filename": file.filename,
                    "error": f"不支持的文件类型"
                })
                continue

            # Create upload directory if it doesn't exist
            upload_dir = os.path.join(settings.UPLOAD_DIR, datetime.now().strftime("%Y-%m-%d"))
            os.makedirs(upload_dir, exist_ok=True)

            # Save file
            file_path = os.path.join(upload_dir, file.filename)

            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            file_size = os.path.getsize(file_path)

            results.append({
                "filename": file.filename,
                "file_size": file_size,
                "file_path": file_path,
                "uploaded_at": datetime.now().isoformat()
            })

        except Exception as e:
            errors.append({
                "filename": file.filename,
                "error": str(e)
            })

    return {
        "uploaded": results,
        "errors": errors,
        "total_uploaded": len(results),
        "total_failed": len(errors)
    }


@router.get("/file/{filename}")
async def get_file_info(filename: str):
    """Get information about a specific file"""
    try:
        # Find the file in upload directories
        upload_dir = settings.UPLOAD_DIR
        if not os.path.exists(upload_dir):
            raise HTTPException(status_code=404, detail="上传目录不存在")

        file_path = None
        for root, dirs, files in os.walk(upload_dir):
            if filename in files:
                file_path = os.path.join(root, filename)
                break

        if not file_path:
            raise HTTPException(status_code=404, detail="文件不存在")

        file_stats = os.stat(file_path)
        file_ext = os.path.splitext(filename)[1].lower()

        return {
            "filename": filename,
            "size": file_stats.st_size,
            "created_at": datetime.fromtimestamp(file_stats.st_ctime),
            "modified_at": datetime.fromtimestamp(file_stats.st_mtime),
            "file_path": file_path,
            "mime_type": {
                '.txt': 'text/plain',
                '.pdf': 'application/pdf',
                '.md': 'text/markdown'
            }.get(file_ext, 'application/octet-stream')
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文件信息失败: {str(e)}")


@router.get("/download/{filename}")
async def download_file(filename: str):
    """Download a specific file"""
    try:
        # Find the file in upload directories
        upload_dir = settings.UPLOAD_DIR
        if not os.path.exists(upload_dir):
            raise HTTPException(status_code=404, detail="上传目录不存在")

        file_path = None
        for root, dirs, files in os.walk(upload_dir):
            if filename in files:
                file_path = os.path.join(root, filename)
                break

        if not file_path:
            raise HTTPException(status_code=404, detail="文件不存在")

        return FileResponse(
            path=file_path,
            filename=filename,
            media_type={
                '.txt': 'text/plain',
                '.pdf': 'application/pdf',
                '.md': 'text/markdown'
            }.get(os.path.splitext(filename)[1].lower(), 'application/octet-stream')
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"下载文件失败: {str(e)}")


@router.delete("/file/{filename}")
async def delete_file(filename: str):
    """Delete a specific file"""
    try:
        # Find the file in upload directories
        upload_dir = settings.UPLOAD_DIR
        if not os.path.exists(upload_dir):
            raise HTTPException(status_code=404, detail="上传目录不存在")

        file_path = None
        for root, dirs, files in os.walk(upload_dir):
            if filename in files:
                file_path = os.path.join(root, filename)
                break

        if not file_path:
            raise HTTPException(status_code=404, detail="文件不存在")

        os.remove(file_path)
        return {"message": f"文件 {filename} 删除成功"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除文件失败: {str(e)}")


@router.get("/list")
async def list_files():
    """List all uploaded files"""
    try:
        upload_dir = settings.UPLOAD_DIR
        if not os.path.exists(upload_dir):
            return {"files": [], "total_count": 0}

        files = []
        for root, dirs, filenames in os.walk(upload_dir):
            for filename in filenames:
                file_path = os.path.join(root, filename)
                file_stats = os.stat(file_path)

                files.append({
                    "filename": filename,
                    "size": file_stats.st_size,
                    "created_at": datetime.fromtimestamp(file_stats.st_ctime),
                    "modified_at": datetime.fromtimestamp(file_stats.st_mtime),
                    "directory": os.path.relpath(root, upload_dir),
                    "file_path": file_path
                })

        return {
            "files": sorted(files, key=lambda x: x["created_at"], reverse=True),
            "total_count": len(files)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文件列表失败: {str(e)}")


@router.delete("/cleanup")
async def cleanup_old_files(days: int = 30):
    """Delete files older than specified days"""
    try:
        import time

        upload_dir = settings.UPLOAD_DIR
        if not os.path.exists(upload_dir):
            return {"message": "上传目录不存在", "deleted_count": 0}

        current_time = time.time()
        cutoff_time = current_time - (days * 24 * 60 * 60)

        deleted_count = 0
        for root, dirs, filenames in os.walk(upload_dir):
            for filename in filenames:
                file_path = os.path.join(root, filename)
                file_stats = os.stat(file_path)

                if file_stats.st_ctime < cutoff_time:
                    try:
                        os.remove(file_path)
                        deleted_count += 1
                    except:
                        pass  # Ignore errors when deleting files

        return {
            "message": f"已删除 {deleted_count} 个超过 {days} 天的文件",
            "deleted_count": deleted_count
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清理旧文件失败: {str(e)}")