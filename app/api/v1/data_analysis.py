#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
데이터 분석 API 엔드포인트
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import logging

from app.services.data_structure_checker import DataStructureChecker
from app.services.data_validator import DataValidator
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

class DataStructureResponse(BaseModel):
    """데이터 구조 응답 모델"""
    data_folder: str
    total_files: int
    analyzed_files: int
    results: Dict[str, Any]

class DataValidationResponse(BaseModel):
    """데이터 검증 응답 모델"""
    csv_files: Dict[str, Any]
    excel_files: Dict[str, Any]
    summary: Dict[str, Any]

class FileInfoResponse(BaseModel):
    """파일 정보 응답 모델"""
    filename: str
    exists: bool
    details: Dict[str, Any]

class DataQualityResponse(BaseModel):
    """데이터 품질 응답 모델"""
    filename: str
    quality_metrics: Dict[str, Any]

@router.get("/structure", response_model=DataStructureResponse)
async def analyze_data_structure(
    data_folder: str = Query(default="data", description="데이터 폴더 경로")
):
    """데이터 구조 분석"""
    try:
        checker = DataStructureChecker(data_folder)
        result = checker.check_all_data_structure()
        
        return DataStructureResponse(
            data_folder=result["data_folder"],
            total_files=result["total_files"],
            analyzed_files=result["analyzed_files"],
            results=result["results"]
        )
        
    except Exception as e:
        logger.error(f"데이터 구조 분석 실패: {e}")
        raise HTTPException(status_code=500, detail=f"데이터 구조 분석에 실패했습니다: {str(e)}")

@router.get("/structure/summary")
async def get_data_structure_summary(
    data_folder: str = Query(default="data", description="데이터 폴더 경로")
):
    """데이터 구조 요약 정보"""
    try:
        checker = DataStructureChecker(data_folder)
        summary = checker.get_summary()
        
        return summary
        
    except Exception as e:
        logger.error(f"데이터 구조 요약 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"요약 정보 조회에 실패했습니다: {str(e)}")

@router.get("/validation", response_model=DataValidationResponse)
async def validate_all_data(
    data_folder: str = Query(default="data", description="데이터 폴더 경로")
):
    """모든 데이터 파일 검증"""
    try:
        validator = DataValidator(data_folder)
        result = validator.validate_all_files()
        
        return DataValidationResponse(
            csv_files=result["csv_files"],
            excel_files=result["excel_files"],
            summary=result["summary"]
        )
        
    except Exception as e:
        logger.error(f"데이터 검증 실패: {e}")
        raise HTTPException(status_code=500, detail=f"데이터 검증에 실패했습니다: {str(e)}")

@router.get("/file/{filename}", response_model=FileInfoResponse)
async def get_file_info(
    filename: str,
    data_folder: str = Query(default="data", description="데이터 폴더 경로")
):
    """특정 파일 정보 조회"""
    try:
        validator = DataValidator(data_folder)
        result = validator.get_file_info(filename)
        
        if result is None:
            raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다")
        
        return FileInfoResponse(
            filename=filename,
            exists=result.get("exists", False),
            details=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"파일 정보 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"파일 정보 조회에 실패했습니다: {str(e)}")

@router.get("/quality/{filename}", response_model=DataQualityResponse)
async def check_data_quality(
    filename: str,
    data_folder: str = Query(default="data", description="데이터 폴더 경로")
):
    """데이터 품질 검사"""
    try:
        validator = DataValidator(data_folder)
        result = validator.check_data_quality(filename)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return DataQualityResponse(
            filename=filename,
            quality_metrics=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"데이터 품질 검사 실패: {e}")
        raise HTTPException(status_code=500, detail=f"데이터 품질 검사에 실패했습니다: {str(e)}")

@router.get("/files/list")
async def list_available_files(
    data_folder: str = Query(default="data", description="데이터 폴더 경로")
):
    """사용 가능한 파일 목록 조회"""
    try:
        validator = DataValidator(data_folder)
        
        return {
            "csv_files": validator.csv_files,
            "excel_files": validator.excel_files,
            "total_files": len(validator.csv_files) + len(validator.excel_files)
        }
        
    except Exception as e:
        logger.error(f"파일 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"파일 목록 조회에 실패했습니다: {str(e)}")

@router.get("/health")
async def data_analysis_health_check():
    """데이터 분석 서비스 헬스 체크"""
    try:
        # 기본 데이터 폴더 확인
        checker = DataStructureChecker()
        validator = DataValidator()
        
        return {
            "status": "healthy",
            "service": "data_analysis",
            "data_folder_exists": checker.data_folder.exists(),
            "available_csv_files": len(validator.csv_files),
            "available_excel_files": len(validator.excel_files)
        }
        
    except Exception as e:
        logger.error(f"데이터 분석 헬스 체크 실패: {e}")
        return {
            "status": "unhealthy",
            "service": "data_analysis", 
            "error": str(e)
        }