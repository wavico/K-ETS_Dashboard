#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prophet 시계열 예측 서비스
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import logging
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False
    Prophet = None

logger = logging.getLogger(__name__)

class ProphetService:
    """Prophet 시계열 예측 서비스"""
    
    def __init__(self, data_folder: str = "data"):
        """초기화"""
        self.data_folder = Path(data_folder)
        self.df = None
        self.model = None
        self.forecast = None
        self.is_model_fitted = False
        
        if not PROPHET_AVAILABLE:
            logger.warning("Prophet 라이브러리가 설치되지 않았습니다. pip install prophet 명령으로 설치하세요.")
        
        self._load_power_data()
    
    def _load_power_data(self) -> None:
        """전력수급 데이터 로드"""
        try:
            filepath = self.data_folder / "HOME_전력수급_최대전력수급.csv"
            
            if not filepath.exists():
                logger.error(f"파일을 찾을 수 없습니다: {filepath}")
                self._create_sample_data()
                return
            
            # 다양한 인코딩으로 시도
            for encoding in ['cp949', 'euc-kr', 'utf-8', 'utf-8-sig']:
                try:
                    df = pd.read_csv(filepath, encoding=encoding)
                    
                    # 컬럼명 정리 (한글이 깨진 경우 영문으로 매핑)
                    if len(df.columns) >= 9:
                        df.columns = [
                            'year', 'month', 'day', 'supply_capacity',
                            'demand_capacity', 'max_demand', 'reserve_capacity', 
                            'reserve_rate', 'max_demand_time'
                        ]
                    
                    # 날짜 컬럼 생성
                    df['date'] = pd.to_datetime(df[['year', 'month', 'day']])
                    
                    # Prophet 형식으로 변환 (ds: 날짜, y: 예측 대상)
                    self.df = df[['date', 'max_demand']].copy()
                    self.df.columns = ['ds', 'y']
                    self.df = self.df.sort_values('ds').reset_index(drop=True)
                    
                    # 결측값 처리
                    self.df = self.df.dropna()
                    
                    logger.info(f"전력수급 데이터 로드 완료: {self.df.shape}, 인코딩: {encoding}")
                    logger.info(f"데이터 기간: {self.df['ds'].min()} ~ {self.df['ds'].max()}")
                    break
                    
                except UnicodeDecodeError:
                    continue
                except Exception as e:
                    logger.error(f"데이터 로드 실패 ({encoding}): {e}")
                    continue
            else:
                logger.error("모든 인코딩으로 파일 로드 실패")
                self._create_sample_data()
                
        except Exception as e:
            logger.error(f"데이터 로드 중 오류: {e}")
            self._create_sample_data()
    
    def _create_sample_data(self) -> None:
        """샘플 데이터 생성"""
        logger.info("샘플 전력수급 데이터 생성 중...")
        
        # 최근 2년간의 일일 데이터 생성
        start_date = datetime.now() - timedelta(days=730)
        dates = pd.date_range(start=start_date, periods=730, freq='D')
        
        # 계절성과 트렌드를 가진 전력수요 데이터 생성
        np.random.seed(42)
        base_demand = 80000
        
        # 연도별 증가 트렌드
        yearly_trend = np.linspace(0, 5000, len(dates))
        
        # 계절성 (여름/겨울 높고, 봄/가을 낮음)
        day_of_year = dates.dayofyear
        seasonal = 15000 * np.sin(2 * np.pi * (day_of_year - 80) / 365.25) + \
                  10000 * np.sin(4 * np.pi * (day_of_year - 80) / 365.25)
        
        # 주간 패턴 (주말 낮음)
        weekly = -3000 * np.sin(2 * np.pi * dates.dayofweek / 7)
        
        # 노이즈
        noise = np.random.normal(0, 2000, len(dates))
        
        # 최종 수요량
        max_demand = base_demand + yearly_trend + seasonal + weekly + noise
        max_demand = np.maximum(max_demand, 50000)  # 최소값 설정
        
        self.df = pd.DataFrame({
            'ds': dates,
            'y': max_demand
        })
        
        logger.info(f"샘플 데이터 생성 완료: {self.df.shape}")
    
    def fit_model(self, **kwargs) -> bool:
        """Prophet 모델 학습"""
        if not PROPHET_AVAILABLE:
            logger.error("Prophet 라이브러리가 없어 모델 학습 불가")
            return False
            
        if self.df is None or self.df.empty:
            logger.error("학습할 데이터가 없습니다")
            return False
        
        try:
            # Prophet 모델 설정
            model_params = {
                'yearly_seasonality': True,
                'weekly_seasonality': True,
                'daily_seasonality': False,
                'seasonality_mode': 'multiplicative',
                'changepoint_prior_scale': 0.01,
                'seasonality_prior_scale': 10.0,
                **kwargs
            }
            
            self.model = Prophet(**model_params)
            
            # 한국 공휴일 추가 (간단한 버전)
            holidays = pd.DataFrame({
                'holiday': 'korean_holiday',
                'ds': pd.to_datetime([
                    '2024-01-01', '2024-02-10', '2024-03-01', '2024-05-05',
                    '2024-06-06', '2024-08-15', '2024-10-03', '2024-12-25',
                    '2025-01-01', '2025-02-29', '2025-03-01', '2025-05-05',
                    '2025-06-06', '2025-08-15', '2025-10-03', '2025-12-25'
                ]),
                'lower_window': 0,
                'upper_window': 1,
            })
            
            # 데이터 범위 내 공휴일만 필터링
            holidays = holidays[
                (holidays['ds'] >= self.df['ds'].min()) & 
                (holidays['ds'] <= self.df['ds'].max())
            ]
            
            if not holidays.empty:
                self.model.add_country_holidays(country_name='KR')
            
            # 모델 학습
            logger.info("Prophet 모델 학습 시작...")
            self.model.fit(self.df)
            self.is_model_fitted = True
            
            logger.info("Prophet 모델 학습 완료")
            return True
            
        except Exception as e:
            logger.error(f"모델 학습 실패: {e}")
            return False
    
    def predict(self, periods: int = 30, freq: str = 'D') -> Optional[pd.DataFrame]:
        """예측 수행"""
        if not self.is_model_fitted:
            logger.warning("모델이 학습되지 않음. 자동으로 학습을 수행합니다.")
            if not self.fit_model():
                return None
        
        try:
            # 미래 날짜 생성
            future = self.model.make_future_dataframe(periods=periods, freq=freq)
            
            # 예측 수행
            logger.info(f"예측 수행 중... (기간: {periods}일)")
            self.forecast = self.model.predict(future)
            
            logger.info("예측 완료")
            return self.forecast
            
        except Exception as e:
            logger.error(f"예측 수행 실패: {e}")
            return None
    
    def get_forecast_summary(self, periods: int = 30) -> Dict[str, Any]:
        """예측 결과 요약"""
        if self.forecast is None:
            self.predict(periods=periods)
        
        if self.forecast is None:
            return {"error": "예측 결과가 없습니다"}
        
        try:
            # 예측 기간만 추출
            forecast_future = self.forecast.tail(periods)
            
            # 통계 계산
            last_actual = self.df['y'].iloc[-1]
            forecast_mean = forecast_future['yhat'].mean()
            forecast_trend = forecast_future['trend'].iloc[-1] - forecast_future['trend'].iloc[0]
            
            # 최대/최소값
            forecast_max = forecast_future['yhat'].max()
            forecast_min = forecast_future['yhat'].min()
            forecast_max_date = forecast_future.loc[forecast_future['yhat'].idxmax(), 'ds']
            forecast_min_date = forecast_future.loc[forecast_future['yhat'].idxmin(), 'ds']
            
            return {
                "prediction_period": f"{periods}일",
                "current_demand": round(last_actual, 0),
                "forecast_mean": round(forecast_mean, 0),
                "forecast_trend": round(forecast_trend, 0),
                "forecast_max": round(forecast_max, 0),
                "forecast_min": round(forecast_min, 0),
                "forecast_max_date": forecast_max_date.strftime('%Y-%m-%d'),
                "forecast_min_date": forecast_min_date.strftime('%Y-%m-%d'),
                "change_percent": round(((forecast_mean - last_actual) / last_actual) * 100, 2),
                "uncertainty_range": round(forecast_future['yhat_upper'].mean() - forecast_future['yhat_lower'].mean(), 0)
            }
            
        except Exception as e:
            logger.error(f"예측 요약 생성 실패: {e}")
            return {"error": f"요약 생성 실패: {str(e)}"}
    
    def create_forecast_plot(self, periods: int = 30) -> Optional[go.Figure]:
        """예측 결과 시각화"""
        if self.forecast is None:
            self.predict(periods=periods)
        
        if self.forecast is None:
            return None
        
        try:
            fig = make_subplots(
                rows=2, cols=1,
                subplot_titles=('전력 최대수요 예측', '예측 구성요소'),
                vertical_spacing=0.1,
                row_heights=[0.7, 0.3]
            )
            
            # 실제 데이터
            fig.add_trace(
                go.Scatter(
                    x=self.df['ds'],
                    y=self.df['y'],
                    mode='lines',
                    name='실제 수요',
                    line=dict(color='blue', width=2)
                ),
                row=1, col=1
            )
            
            # 예측값
            future_data = self.forecast.tail(periods)
            fig.add_trace(
                go.Scatter(
                    x=future_data['ds'],
                    y=future_data['yhat'],
                    mode='lines',
                    name='예측 수요',
                    line=dict(color='red', width=2, dash='dash')
                ),
                row=1, col=1
            )
            
            # 신뢰구간
            fig.add_trace(
                go.Scatter(
                    x=pd.concat([future_data['ds'], future_data['ds'][::-1]]),
                    y=pd.concat([future_data['yhat_upper'], future_data['yhat_lower'][::-1]]),
                    fill='toself',
                    fillcolor='rgba(255,0,0,0.2)',
                    line=dict(color='rgba(255,255,255,0)'),
                    name='신뢰구간',
                    showlegend=True
                ),
                row=1, col=1
            )
            
            # 트렌드 구성요소
            fig.add_trace(
                go.Scatter(
                    x=self.forecast['ds'],
                    y=self.forecast['trend'],
                    mode='lines',
                    name='트렌드',
                    line=dict(color='green', width=1)
                ),
                row=2, col=1
            )
            
            # 레이아웃 설정
            fig.update_layout(
                title='전력 최대수요 Prophet 예측',
                height=800,
                showlegend=True,
                template='plotly_white'
            )
            
            fig.update_xaxes(title_text='날짜', row=2, col=1)
            fig.update_yaxes(title_text='최대수요 (MW)', row=1, col=1)
            fig.update_yaxes(title_text='트렌드 (MW)', row=2, col=1)
            
            return fig
            
        except Exception as e:
            logger.error(f"시각화 생성 실패: {e}")
            return None
    
    def get_model_info(self) -> Dict[str, Any]:
        """모델 정보 반환"""
        if not self.is_model_fitted:
            return {"error": "모델이 학습되지 않았습니다"}
        
        try:
            # 데이터 정보
            data_info = {
                "data_points": len(self.df),
                "date_range": {
                    "start": self.df['ds'].min().strftime('%Y-%m-%d'),
                    "end": self.df['ds'].max().strftime('%Y-%m-%d')
                },
                "demand_range": {
                    "min": round(self.df['y'].min(), 0),
                    "max": round(self.df['y'].max(), 0),
                    "mean": round(self.df['y'].mean(), 0)
                }
            }
            
            # 모델 파라미터
            model_params = {
                "yearly_seasonality": self.model.yearly_seasonality,
                "weekly_seasonality": self.model.weekly_seasonality,
                "daily_seasonality": self.model.daily_seasonality,
                "seasonality_mode": self.model.seasonality_mode,
                "changepoint_prior_scale": self.model.changepoint_prior_scale
            }
            
            return {
                "model_type": "Prophet",
                "is_fitted": self.is_model_fitted,
                "data_info": data_info,
                "model_params": model_params,
                "prophet_available": PROPHET_AVAILABLE
            }
            
        except Exception as e:
            logger.error(f"모델 정보 생성 실패: {e}")
            return {"error": f"모델 정보 생성 실패: {str(e)}"}
    
    def predict_from_query(self, query: str) -> Dict[str, Any]:
        """자연어 질의에 따른 예측"""
        try:
            # 질의에서 예측 기간 추출
            periods = 30  # 기본값
            
            if '주' in query or 'week' in query.lower():
                if '1주' in query or '1 주' in query:
                    periods = 7
                elif '2주' in query or '2 주' in query:
                    periods = 14
                elif '4주' in query or '4 주' in query:
                    periods = 28
            elif '개월' in query or 'month' in query.lower():
                if '1개월' in query or '1 개월' in query:
                    periods = 30
                elif '3개월' in query or '3 개월' in query:
                    periods = 90
                elif '6개월' in query or '6 개월' in query:
                    periods = 180
            elif '일' in query or 'day' in query.lower():
                import re
                numbers = re.findall(r'\d+', query)
                if numbers:
                    periods = min(int(numbers[0]), 365)  # 최대 1년
            
            # 예측 수행
            forecast_df = self.predict(periods=periods)
            if forecast_df is None:
                return {"error": "예측 수행에 실패했습니다"}
            
            # 요약 정보
            summary = self.get_forecast_summary(periods=periods)
            
            # 시각화
            chart = self.create_forecast_plot(periods=periods)
            
            # 모델 정보
            model_info = self.get_model_info()
            
            return {
                "query": query,
                "periods": periods,
                "summary": summary,
                "predictions": forecast_df.tail(periods)[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].to_dict('records'),
                "chart": chart,
                "model_info": model_info,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"질의 기반 예측 실패: {e}")
            return {
                "query": query,
                "error": f"예측 실패: {str(e)}",
                "success": False
            }