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
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

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

                    # 컬럼명을 영문으로 매핑
                    col_mapping = {
                        '년': 'year',
                        '월': 'month',
                        '일': 'day',
                        '설비용량(MW)': 'supply_capacity',
                        '공급능력(MW)': 'demand_capacity',
                        '최대전력(MW)': 'max_demand',
                        '공급예비력(MW)': 'reserve_capacity',
                        '공급예비율(%)': 'reserve_rate',
                        '최대전력기준일시': 'max_demand_time'
                    }

                    # 컬럼명이 한글이면 매핑, 아니면 그대로 유지
                    if df.columns[0] in col_mapping:
                        df = df.rename(columns=col_mapping)
                    elif len(df.columns) >= 9:
                        # 한글이 깨진 경우 순서대로 매핑
                        df.columns = [
                            'year', 'month', 'day', 'supply_capacity',
                            'demand_capacity', 'max_demand', 'reserve_capacity',
                            'reserve_rate', 'max_demand_time'
                        ]

                    # 날짜 컬럼 생성 (각 컬럼을 문자열로 결합 후 변환)
                    df['date_str'] = (df['year'].astype(str) + '-' +
                                      df['month'].astype(str).str.zfill(2) + '-' +
                                      df['day'].astype(str).str.zfill(2))
                    df['date'] = pd.to_datetime(df['date_str'], format='%Y-%m-%d', errors='coerce')

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
            
            # 한국 공휴일 추가 (Prophet 내장 기능 사용)
            try:
                self.model.add_country_holidays(country_name='KR')
                logger.info("한국 공휴일 추가 완료")
            except Exception as e:
                logger.warning(f"공휴일 추가 실패 (무시하고 계속 진행): {e}")
            
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
    
    def evaluate_model(self, test_size: float = 0.2) -> Dict[str, Any]:
        """
        모델 성능 평가 (학습 데이터의 일부를 테스트용으로 분리)

        Args:
            test_size: 테스트 데이터 비율 (0~1)

        Returns:
            성능 지표 딕셔너리
        """
        if not self.is_model_fitted or self.df is None:
            logger.error("모델이 학습되지 않았거나 데이터가 없습니다")
            return {"error": "모델이 학습되지 않았습니다"}

        try:
            # 데이터 분할
            split_idx = int(len(self.df) * (1 - test_size))
            train_df = self.df[:split_idx].copy()
            test_df = self.df[split_idx:].copy()

            logger.info(f"학습 데이터: {len(train_df)}개, 테스트 데이터: {len(test_df)}개")

            # 새 모델로 학습
            test_model = Prophet(
                yearly_seasonality=True,
                weekly_seasonality=True,
                daily_seasonality=False,
                seasonality_mode='multiplicative',
                changepoint_prior_scale=0.01,
                seasonality_prior_scale=10.0
            )
            test_model.fit(train_df)

            # 테스트 기간 예측
            future = test_model.make_future_dataframe(periods=len(test_df), freq='D')
            forecast = test_model.predict(future)

            # 테스트 데이터에 해당하는 예측값 추출
            forecast_test = forecast.tail(len(test_df))

            # 실제값과 예측값 병합
            test_actual = test_df['y'].values
            test_predicted = forecast_test['yhat'].values

            # 성능 지표 계산
            mae = mean_absolute_error(test_actual, test_predicted)
            rmse = np.sqrt(mean_squared_error(test_actual, test_predicted))
            mape = np.mean(np.abs((test_actual - test_predicted) / test_actual)) * 100
            r2 = r2_score(test_actual, test_predicted)

            # 신뢰구간 내 포함 비율
            in_interval = np.sum(
                (test_actual >= forecast_test['yhat_lower'].values) &
                (test_actual <= forecast_test['yhat_upper'].values)
            )
            coverage = (in_interval / len(test_actual)) * 100

            return {
                "metrics": {
                    "MAE": round(mae, 2),
                    "RMSE": round(rmse, 2),
                    "MAPE": round(mape, 2),
                    "R2_Score": round(r2, 4),
                    "Coverage": round(coverage, 2)
                },
                "data_split": {
                    "train_size": len(train_df),
                    "test_size": len(test_df),
                    "test_ratio": test_size
                },
                "test_period": {
                    "start": test_df['ds'].min().strftime('%Y-%m-%d'),
                    "end": test_df['ds'].max().strftime('%Y-%m-%d')
                },
                "actual_vs_predicted": {
                    "dates": test_df['ds'].dt.strftime('%Y-%m-%d').tolist(),
                    "actual": test_actual.tolist(),
                    "predicted": test_predicted.tolist(),
                    "lower_bound": forecast_test['yhat_lower'].tolist(),
                    "upper_bound": forecast_test['yhat_upper'].tolist()
                }
            }

        except Exception as e:
            logger.error(f"모델 평가 실패: {e}")
            return {"error": f"모델 평가 실패: {str(e)}"}

    def cross_validate_model(self, initial_days: int = 365, period_days: int = 30,
                           horizon_days: int = 30) -> Dict[str, Any]:
        """
        교차 검증을 통한 모델 성능 평가

        Args:
            initial_days: 초기 학습 기간 (일)
            period_days: 검증 간격 (일)
            horizon_days: 예측 기간 (일)

        Returns:
            교차 검증 결과
        """
        if not PROPHET_AVAILABLE:
            return {"error": "Prophet 라이브러리가 설치되지 않았습니다"}

        if not self.is_model_fitted or self.df is None:
            logger.error("모델이 학습되지 않았거나 데이터가 없습니다")
            return {"error": "모델이 학습되지 않았습니다"}

        try:
            from prophet.diagnostics import cross_validation, performance_metrics

            logger.info("교차 검증 수행 중...")

            # 교차 검증 수행
            df_cv = cross_validation(
                self.model,
                initial=f'{initial_days} days',
                period=f'{period_days} days',
                horizon=f'{horizon_days} days'
            )

            # 성능 지표 계산
            df_p = performance_metrics(df_cv)

            # 평균 성능 지표
            avg_metrics = {
                "MAE": round(df_p['mae'].mean(), 2),
                "RMSE": round(df_p['rmse'].mean(), 2),
                "MAPE": round(df_p['mape'].mean() * 100, 2),
                "Coverage": round(df_p['coverage'].mean() * 100, 2)
            }

            return {
                "average_metrics": avg_metrics,
                "detailed_metrics": df_p.to_dict('records'),
                "cv_params": {
                    "initial_days": initial_days,
                    "period_days": period_days,
                    "horizon_days": horizon_days
                },
                "num_folds": len(df_cv['cutoff'].unique())
            }

        except Exception as e:
            logger.error(f"교차 검증 실패: {e}")
            return {"error": f"교차 검증 실패: {str(e)}"}

    def create_evaluation_plot(self, evaluation_result: Dict[str, Any]) -> Optional[go.Figure]:
        """
        평가 결과 시각화

        Args:
            evaluation_result: evaluate_model() 결과

        Returns:
            Plotly Figure
        """
        if "error" in evaluation_result or "actual_vs_predicted" not in evaluation_result:
            return None

        try:
            data = evaluation_result["actual_vs_predicted"]
            dates = pd.to_datetime(data["dates"])

            fig = make_subplots(
                rows=2, cols=1,
                subplot_titles=('실제값 vs 예측값', '예측 오차'),
                vertical_spacing=0.15,
                row_heights=[0.7, 0.3]
            )

            # 실제값
            fig.add_trace(
                go.Scatter(
                    x=dates,
                    y=data["actual"],
                    mode='lines+markers',
                    name='실제값',
                    line=dict(color='blue', width=2),
                    marker=dict(size=6)
                ),
                row=1, col=1
            )

            # 예측값
            fig.add_trace(
                go.Scatter(
                    x=dates,
                    y=data["predicted"],
                    mode='lines+markers',
                    name='예측값',
                    line=dict(color='red', width=2, dash='dash'),
                    marker=dict(size=6)
                ),
                row=1, col=1
            )

            # 신뢰구간
            upper = data["upper_bound"]
            lower = data["lower_bound"][::-1]
            dates_reversed = dates[::-1]

            fig.add_trace(
                go.Scatter(
                    x=dates.tolist() + dates_reversed.tolist(),
                    y=upper + lower,
                    fill='toself',
                    fillcolor='rgba(255,0,0,0.1)',
                    line=dict(color='rgba(255,255,255,0)'),
                    name='95% 신뢰구간',
                    showlegend=True
                ),
                row=1, col=1
            )

            # 오차
            errors = np.array(data["actual"]) - np.array(data["predicted"])
            fig.add_trace(
                go.Bar(
                    x=dates,
                    y=errors,
                    name='예측 오차',
                    marker=dict(
                        color=errors,
                        colorscale='RdYlGn_r',
                        showscale=True,
                        colorbar=dict(title="오차", x=1.1)
                    )
                ),
                row=2, col=1
            )

            # 성능 지표 표시
            metrics = evaluation_result.get("metrics", {})
            annotation_text = (
                f"MAE: {metrics.get('MAE', 0):,.0f}<br>"
                f"RMSE: {metrics.get('RMSE', 0):,.0f}<br>"
                f"MAPE: {metrics.get('MAPE', 0):.2f}%<br>"
                f"R²: {metrics.get('R2_Score', 0):.4f}<br>"
                f"Coverage: {metrics.get('Coverage', 0):.1f}%"
            )

            fig.add_annotation(
                text=annotation_text,
                xref="paper", yref="paper",
                x=0.02, y=0.98,
                showarrow=False,
                bgcolor="rgba(255,255,255,0.8)",
                bordercolor="black",
                borderwidth=1,
                font=dict(size=10)
            )

            # 레이아웃 설정
            fig.update_layout(
                title='모델 성능 평가 결과',
                height=800,
                showlegend=True,
                template='plotly_white'
            )

            fig.update_xaxes(title_text='날짜', row=2, col=1)
            fig.update_yaxes(title_text='최대수요 (MW)', row=1, col=1)
            fig.update_yaxes(title_text='오차 (MW)', row=2, col=1)

            return fig

        except Exception as e:
            logger.error(f"평가 시각화 생성 실패: {e}")
            return None

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