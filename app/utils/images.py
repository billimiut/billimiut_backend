from PIL import Image, ImageOps
from fastapi import UploadFile, HTTPException, status,File
import io 
from app.utils.amazon import upload_to_s3
from datetime import datetime

from dotenv import load_dotenv,find_dotenv
import os

load_dotenv(find_dotenv())


async def upload_image(file: UploadFile = File(...)):
    try:
        file = await validate_image_type(file)
        file = await validate_image_size(file)
        file = change_filename(file)
        image = resize_image(file)
        image_bytes = convert_image_to_bytes(image)
        print(file.filename)
        upload_to_s3(image_bytes, 'billimiut-post-image', file.filename)
        bucket_url = os.getenv("BUCKET_URL")
        ret_filename = f"{bucket_url}/{file.filename}"
        print(ret_filename)
        return ret_filename
    except HTTPException as e:
        return False


async def validate_image_type(file: UploadFile) -> UploadFile:
    if file.filename.split(".")[-1].lower() not in ["jpg", "jpeg", "png"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="업로드 불가능한 이미지 확장자입니다.",
        )
 
    if not file.content_type.startswith("image"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미지 파일만 업로드 가능합니다.",
        )
    return file


async def validate_image_size(file: UploadFile) -> UploadFile:
    if len(await file.read()) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미지 파일은 10MB 이하만 업로드 가능합니다.",
        )
    return file


def change_filename(file: UploadFile) -> UploadFile:
    """
    이미지 이름 변경
    """
    # random_name = secrets.token_urlsafe(16)
    # file.filename = f"{random_name}.jpeg"
    file.filename = f"{datetime.now().timestamp()}.png"    
    return file


def resize_image(file: UploadFile, max_size: int = 1024):
    read_image = Image.open(file.file)
    original_width, original_height = read_image.size
 
    if original_width > max_size or original_height > max_size:
        if original_width > original_height:
            new_width = max_size
            new_height = int((new_width / original_width) * original_height)
        else:
            new_height = max_size
            new_width = int((new_height / original_height) * original_width)
        read_image = read_image.resize((new_width, new_height))
 
    read_image = read_image.convert("RGB")
    read_image = ImageOps.exif_transpose(read_image)
    return read_image


def save_image_to_filesystem(image: Image, file_path: str):
    image.save(file_path, "jpeg", quality=70)
    return file_path


def convert_image_to_bytes(image: Image) -> io.BytesIO:
    img_byte = io.BytesIO()
    image.save(img_byte, "jpeg", quality=70)
    img_byte.seek(0)
    return img_byte


"""
https://chaechae.life/blog/fastapi-image-upload
"""
