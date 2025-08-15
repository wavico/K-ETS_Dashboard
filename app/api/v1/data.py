#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
K-ETS Dashboard 데이터 처리 API 엔드포인트
"""

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Body
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
import logging

from app.core.security import get_current_user
from app.services.data_service import DataService
from app.models.schemas import DataUploadResponse, DataProcessRequest

logger = logging.getLogger(__name__)
router = APIRouter()

# 데이터 서비스 인스턴스
data_service = DataService()

@router.post("/data/upload", response_model=DataUploadResponse)
async def upload_data_file(
    file: UploadFile = File(...),
    data_type: str = Query(..., description="데이터 타입 (carbon, power, market)"),
    current_user: dict = Depends(get_current_user)
):
    """데이터 파일 업로드"""
    try:
        upload_result = await data_service.upload_file(
            file=file,
            data_type=data_type,
            user_id=current_user.get("username")
        )
        
        return DataUploadResponse(
            success=True,
            file_id=upload_result["file_id"],
            filename=upload_result["filename"],
            data_type=data_type,
            message="파일 업로드가 성공적으로 완료되었습니다."
        )
    except Exception as e:
        logger.error(f"파일 업로드 오류: {e}")
        raise HTTPException(status_code=500, detail=f"파일 업로드 실패: {str(e)}")

@router.get("/data/files", response_model=List[Dict[str, Any]])
async def get_data_files(
    data_type: Optional[str] = Query(None, description="데이터 타입 필터"),
    current_user: dict = Depends(get_current_user)
):
    """업로드된 데이터 파일 목록 조회"""
    try:
        files = await data_service.get_files(
            data_type=data_type,
            user_id=current_user.get("username")
        )
        return files
    except Exception as e:
        logger.error(f"파일 목록 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="파일 목록 조회 실패")

@router.get("/data/process/{file_id}", response_model=Dict[str, Any])
async def process_data_file(
    file_id: str,
    process_type: str = Query(..., description="처리 타입 (clean, validate, transform)"),
    current_user: dict = Depends(get_current_user)
):
    """데이터 파일 처리"""
    try:
        process_result = await data_service.process_file(
            file_id=file_id,
            process_type=process_type,
            user_id=current_user.get("username")
        )
        
        return {
            "success": True,
            "file_id": file_id,
            "process_type": process_type,
            "result": process_result
        }
    except Exception as e:
        logger.error(f"데이터 처리 오류: {e}")
        raise HTTPException(status_code=500, detail=f"데이터 처리 실패: {str(e)}")

@router.post("/data/analyze", response_model=Dict[str, Any])
async def analyze_data_file(
    request: DataProcessRequest,
    current_user: dict = Depends(get_current_user)
):
    """데이터 파일 분석"""
    try:
        analysis_result = await data_service.analyze_data(
            file_id=request.file_id,
            analysis_type=request.analysis_type,
            parameters=request.parameters,
            user_id=current_user.get("username")
        )
        
        return {
            "success": True,
            "analysis": analysis_result
        }
    except Exception as e:
        logger.error(f"데이터 분석 오류: {e}")
        raise HTTPException(status_code=500, detail=f"데이터 분석 실패: {str(e)}")

@router.get("/data/export/{file_id}")
async def export_processed_data(
    file_id: str,
    export_format: str = Query("csv", description="내보내기 형식 (csv, excel, json)"),
    current_user: dict = Depends(get_current_user)
):
    """처리된 데이터 내보내기"""
    try:
        export_result = await data_service.export_data(
            file_id=file_id,
            export_format=export_format,
            user_id=current_user.get("username")
        )
        
        return JSONResponse(
            content=export_result,
            headers={"Content-Disposition": f"attachment; filename=data_{file_id}.{export_format}"}
        )
    except Exception as e:
        logger.error(f"데이터 내보내기 오류: {e}")
        raise HTTPException(status_code=500, detail="데이터 내보내기 실패")

@router.delete("/data/files/{file_id}")
async def delete_data_file(
    file_id: str,
    current_user: dict = Depends(get_current_user)
):
    """데이터 파일 삭제"""
    try:
        await data_service.delete_file(
            file_id=file_id,
            user_id=current_user.get("username")
        )
        
        return {
            "success": True,
            "message": "파일이 성공적으로 삭제되었습니다."
        }
    except Exception as e:
        logger.error(f"파일 삭제 오류: {e}")
        raise HTTPException(status_code=500, detail="파일 삭제 실패")

@router.get("/data/statistics", response_model=Dict[str, Any])
async def get_data_statistics(
    data_type: Optional[str] = Query(None, description="데이터 타입"),
    current_user: dict = Depends(get_current_user)
):
    """데이터 통계 정보 조회"""
    try:
        stats = await data_service.get_statistics(
            data_type=data_type,
            user_id=current_user.get("username")
        )
        return stats
    except Exception as e:
        logger.error(f"통계 정보 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="통계 정보 조회 실패")

@router.post("/data/validate", response_model=Dict[str, Any])
async def validate_data_quality(
    file_id: str,
    validation_rules: Dict[str, Any] = Body(...),
    current_user: dict = Depends(get_current_user)
):
    """데이터 품질 검증"""
    try:
        validation_result = await data_service.validate_data(
            file_id=file_id,
            validation_rules=validation_rules,
            user_id=current_user.get("username")
        )
        
        return {
            "success": True,
            "validation": validation_result
        }
    except Exception as e:
        logger.error(f"데이터 검증 오류: {e}")
        raise HTTPException(status_code=500, detail=f"데이터 검증 실패: {str(e)}")

@router.get("/data/health")
async def get_data_service_health():
    """데이터 서비스 상태 확인 (인증 불필요)"""
    try:
        health_status = await data_service.get_health_status()
        return {
            "status": "healthy",
            "service": "Data Service",
            "components": health_status
        }
    except Exception as e:
        logger.error(f"데이터 서비스 상태 확인 오류: {e}")
        return {
            "status": "unhealthy",
            "service": "Data Service",
            "error": str(e)
        }
