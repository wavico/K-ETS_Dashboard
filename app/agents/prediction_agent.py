"""
Prophet 기반 시계열 예측 에이전트

FastAPI용으로 업데이트된 예측 에이전트
전력수급 데이터와 탄소 배출 데이터를 활용한 시계열 예측
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, Any, List
import warnings
import logging
warnings.filterwarnings('ignore')

# FastAPI 관련 imports
from app.agents.base_agent import BaseAgent
from app.models.agent_response import PredictionResponse, VisualizationData, DashboardUpdate, MetricData
from app.services.prophet_service import ProphetService

try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False
    Prophet = None

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go

logger = logging.getLogger(__name__)

class PredictionAgent(BaseAgent):
    """Prophet 기반 시계열 예측 에이전트"""
    
    def __init__(self, data_folder: str = "data"):
        """
        예측 에이전트 초기화
        
        Args:
            data_folder: 데이터 폴더 경로 (기본값: "data")
        """
        super().__init__("prediction")
        
        self.data_folder = data_folder
        self.carbon_df = None
        self.power_df = None
        
        # Prophet 서비스 초기화
        self.prophet_service = ProphetService(data_folder)
        
        logger.info("예측 에이전트 초기화 완료")
    
    async def process(self, message: str, context: Dict[str, Any]) -> PredictionResponse:
        """예측 요청 처리"""
        try:
            # Prophet 서비스로 예측 수행
            result = self.prophet_service.predict_from_query(message)
            
            if not result.get("success", False):
                return PredictionResponse(
                    message=f"예측 실패: {result.get('error', '알 수 없는 오류')}",
                    agent_type=self.agent_type,
                    prediction_period=f"{result.get('periods', 30)}일"
                )
            
            # 시각화 데이터 변환
            visualizations = []
            if result.get("chart"):
                viz_data = VisualizationData(
                    chart_type="plotly",
                    data=result["chart"].to_dict() if hasattr(result["chart"], 'to_dict') else {},
                    title="전력수급 예측",
                    description="Prophet 모델을 활용한 전력 최대수요 예측 결과"
                )
                visualizations.append(viz_data)
            
            # 메트릭 데이터 생성
            summary = result.get("summary", {})
            metrics = []
            
            if "current_demand" in summary:
                metrics.append(MetricData(
                    name="현재 수요",
                    value=summary["current_demand"],
                    unit="MW",
                    description="현재 전력 최대수요"
                ))
            
            if "forecast_mean" in summary:
                metrics.append(MetricData(
                    name="예측 평균",
                    value=summary["forecast_mean"], 
                    unit="MW",
                    change=summary.get("change_percent"),
                    change_type="increase" if summary.get("change_percent", 0) > 0 else "decrease",
                    description="예측 기간 평균 수요"
                ))
            
            # 대시보드 업데이트
            dashboard_updates = DashboardUpdate(
                charts=visualizations,
                metrics=metrics
            )
            
            return PredictionResponse(
                message=f"전력수급 {result.get('periods', 30)}일 예측이 완료되었습니다. "
                       f"평균 예측 수요: {summary.get('forecast_mean', 0):,.0f}MW "
                       f"({summary.get('change_percent', 0):+.1f}%)",
                agent_type=self.agent_type,
                prediction_period=f"{result.get('periods', 30)}일",
                model_info=result.get("model_info"),
                accuracy_metrics={"uncertainty_range": summary.get("uncertainty_range", 0)},
                forecast_data={"predictions": result.get("predictions", [])},
                data=result,
                visualizations=visualizations,
                dashboard_updates=dashboard_updates
            )
            
        except Exception as e:
            logger.error(f"예측 처리 실패: {e}")
            return PredictionResponse(
                message=f"예측 처리 중 오류가 발생했습니다: {str(e)}",
                agent_type=self.agent_type,
                prediction_period="N/A"
            )
    
    async def analyze_dashboard_section(self, dashboard_state: Dict) -> Dict[str, Any]:
        """대시보드 섹션 분석"""
        try:
            # 예측 모델 상태 확인
            model_info = self.prophet_service.get_model_info()
            
            # 최근 예측 수행
            if self.prophet_service.forecast is None:
                self.prophet_service.predict(periods=7)  # 1주일 예측
            
            forecast_summary = self.prophet_service.get_forecast_summary(periods=7)
            
            return {
                "model_status": model_info,
                "recent_forecast": forecast_summary,
                "recommendations": [
                    "정기적인 모델 재학습 권장",
                    "계절성 패턴 모니터링 필요",
                    "예측 정확도 검증 수행"
                ],
                "insights": [
                    "Prophet 모델이 활성화됨",
                    "전력수급 예측 기능 사용 가능"
                ]
            }
            
        except Exception as e:
            logger.error(f"대시보드 섹션 분석 실패: {e}")
            return {"error": str(e)}
    
    def predict(self, target_column: str = "max_demand", days_ahead: int = 7) -> Dict[str, Any]:
        """예측 수행 (기존 호환성 유지)"""
        try:
            result = self.prophet_service.predict_from_query(f"{days_ahead}일 예측")
            
            return {
                "target_column": target_column,
                "days_ahead": days_ahead,
                "predictions": result.get("predictions", []),
                "summary": result.get("summary", {}),
                "model_info": result.get("model_info", {}),
                "success": result.get("success", False)
            }
            
        except Exception as e:
            logger.error(f"예측 수행 실패: {e}")
            return {
                "target_column": target_column,
                "days_ahead": days_ahead,
                "error": str(e),
                "success": False
            }
    
    def get_status(self) -> Dict[str, Any]:
        """에이전트 상태 정보"""
        return {
            "status": "running",
            "prophet_available": PROPHET_AVAILABLE,
            "model_fitted": self.prophet_service.is_model_fitted if hasattr(self.prophet_service, 'is_model_fitted') else False,
            "data_loaded": self.prophet_service.df is not None if hasattr(self.prophet_service, 'df') else False,
            "last_prediction": datetime.now().isoformat()
        }
    
    def get_capabilities(self) -> List[str]:
        """에이전트 기능 목록"""
        capabilities = [
            "시계열 예측",
            "전력수급 예측", 
            "계절성 분석",
            "트렌드 분석"
        ]
        
        if PROPHET_AVAILABLE:
            capabilities.extend([
                "Prophet 모델 예측",
                "신뢰구간 예측",
                "공휴일 효과 분석"
            ])
        
        return capabilities
        
    def _load_data(self):
        """탄소 및 전력 데이터 로드"""
        print("📊 예측용 데이터 로딩 중...")
        
        # 탄소 데이터 로드
        carbon_folder = os.path.join(self.data_folder, "carbon")
        if os.path.exists(carbon_folder):
            self.carbon_df = self._load_carbon_data(carbon_folder)
            if self.carbon_df is not None:
                print(f"✅ 탄소 데이터 로드 완료: {len(self.carbon_df)}행")
            
        # 전력 데이터 로드  
        power_folder = os.path.join(self.data_folder, "power")
        if os.path.exists(power_folder):
            self.power_df = self._load_power_data(power_folder)
            if self.power_df is not None:
                print(f"✅ 전력 데이터 로드 완료: {len(self.power_df)}행")
                
        if self.carbon_df is None and self.power_df is None:
            print("⚠️ 로드된 데이터가 없습니다.")
            
    def _load_carbon_data(self, carbon_folder: str) -> Optional[pd.DataFrame]:
        """탄소/배출권 관련 데이터 로드"""
        try:
            carbon_files = []
            print(f"🔍 탄소 폴더 확인: {carbon_folder}")
            
            if not os.path.exists(carbon_folder):
                print(f"❌ 탄소 폴더가 존재하지 않음: {carbon_folder}")
                return None
                
            for file in os.listdir(carbon_folder):
                if file.endswith(('.csv', '.xlsx')):
                    file_path = os.path.join(carbon_folder, file)
                    print(f"📄 처리 중: {file}")
                    
                    # 다양한 인코딩으로 시도
                    for encoding in ['cp949', 'euc-kr', 'utf-8', 'utf-8-sig']:
                        try:
                            if file.endswith('.csv'):
                                df = pd.read_csv(file_path, encoding=encoding, low_memory=False)
                            else:
                                df = pd.read_excel(file_path)
                            
                            carbon_files.append(df)
                            print(f"✅ {file} 로드 완료 ({df.shape}) - 인코딩: {encoding}")
                            break
                        except Exception as e:
                            continue
                    else:
                        print(f"❌ {file} 로드 실패 - 모든 인코딩 시도했음")
                            
            if carbon_files:
                # 모든 파일을 하나로 합치기 (공통 컬럼 기준)
                combined_df = pd.concat(carbon_files, ignore_index=True, sort=False)
                print(f"📊 탄소 데이터 통합 완료: {combined_df.shape}")
                return self._preprocess_carbon_data(combined_df)
            else:
                print("❌ 탄소 데이터 로드 실패 - 유효한 파일 없음")
                return None
                
        except Exception as e:
            print(f"❌ 탄소 데이터 로드 오류: {e}")
            return None
            
    def _load_power_data(self, power_folder: str) -> Optional[pd.DataFrame]:
        """전력 통계 데이터 로드"""
        try:
            power_files = []
            for file in os.listdir(power_folder):
                if file.endswith(('.csv', '.xlsx')):
                    file_path = os.path.join(power_folder, file)
                    
                    # 다양한 인코딩으로 시도
                    for encoding in ['cp949', 'euc-kr', 'utf-8', 'utf-8-sig']:
                        try:
                            if file.endswith('.csv'):
                                df = pd.read_csv(file_path, encoding=encoding)
                            else:
                                df = pd.read_excel(file_path)
                            
                            power_files.append(df)
                            print(f"📄 {file} 로드 완료 (인코딩: {encoding})")
                            break
                        except Exception as e:
                            continue
                            
            if power_files:
                # 모든 파일을 하나로 합치기
                combined_df = pd.concat(power_files, ignore_index=True, sort=False)
                return self._preprocess_power_data(combined_df)
            else:
                print("❌ 전력 데이터 로드 실패")
                return None
                
        except Exception as e:
            print(f"❌ 전력 데이터 로드 오류: {e}")
            return None
            
    def _preprocess_carbon_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """탄소 데이터 전처리 - 날짜 컬럼 생성 및 정리"""
        try:
            # 날짜 컬럼 찾기 및 생성
            date_columns = [col for col in df.columns if any(keyword in str(col).lower() 
                          for keyword in ['일자', 'date', '날짜', '거래일'])]
            
            if date_columns:
                date_col = date_columns[0]
                df['ds'] = pd.to_datetime(df[date_col], errors='coerce')
            else:
                print("⚠️ 탄소 데이터에서 날짜 컬럼을 찾을 수 없습니다.")
                return df
                
            # 날짜별로 정렬
            df = df.sort_values('ds').reset_index(drop=True)
            
            # 중복 제거
            df = df.drop_duplicates().reset_index(drop=True)
            
            return df
            
        except Exception as e:
            print(f"❌ 탄소 데이터 전처리 오류: {e}")
            return df
            
    def _preprocess_power_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """전력 데이터 전처리 - 년/월/일 컬럼으로 날짜 생성"""
        try:
            # 년/월/일 컬럼이 있는 경우
            if len(df.columns) >= 3:
                try:
                    df['ds'] = pd.to_datetime(df.iloc[:, :3].astype(str).agg('-'.join, axis=1), 
                                            format='%Y-%m-%d', errors='coerce')
                except:
                    # 대안: 첫 번째 컬럼이 날짜인 경우
                    df['ds'] = pd.to_datetime(df.iloc[:, 0], errors='coerce')
            
            # 날짜별로 정렬
            df = df.sort_values('ds').reset_index(drop=True)
            
            # 중복 제거
            df = df.drop_duplicates().reset_index(drop=True)
            
            return df
            
        except Exception as e:
            print(f"❌ 전력 데이터 전처리 오류: {e}")
            return df
            
    def _parse_natural_language(self, query: str) -> Tuple[str, int]:
        """자연어 쿼리에서 컬럼명과 예측일수 추출"""
        query_lower = query.lower()
        
        # 예측일수 추출
        import re
        days_match = re.search(r'(\d+)일', query)
        if days_match:
            days_ahead = int(days_match.group(1))
        elif '내일' in query_lower:
            days_ahead = 1
        else:
            days_ahead = 7
        
        # 컬럼 매핑 (자연어 → 실제 컬럼명)
        column_mappings = {
            # 전력 관련
            '최대전력': '최대전력(MW)',
            '설비용량': '설비용량(MW)', 
            '공급능력': '공급능력(MW)',
            '공급예비력': '공급예비력(MW)',
            '공급예비율': '공급예비율(%)',
            '전력': '최대전력(MW)',
            
            # 탄소/배출권 관련
            '종가': '종가',
            '시가': '시가', 
            '고가': '고가',
            '저가': '저가',
            '거래량': '거래량',
            '거래대금': '거래대금',
            '가격': '종가',  # 일반적인 가격은 종가로
            '배출권가격': '종가',
            '배출권': '종가',
        }
        
        # 키워드 기반 컬럼 찾기
        for keyword, actual_column in column_mappings.items():
            if keyword in query_lower:
                return actual_column, days_ahead
                
        # 직접 컬럼명이 포함된 경우 (백업)
        if self.carbon_df is not None:
            for col in self.carbon_df.columns:
                if col.lower().replace('(', '').replace(')', '') in query_lower:
                    return col, days_ahead
                    
        if self.power_df is not None:
            for col in self.power_df.columns:
                if col.lower().replace('(', '').replace(')', '') in query_lower:
                    return col, days_ahead
        
        # 기본값: 종가
        return '종가', days_ahead
    
    def _detect_prediction_source(self, target_column: str) -> str:
        """컬럼명을 기반으로 데이터 소스 자동 감지"""
        target_lower = target_column.lower()
        
        # 전력 관련 키워드
        power_keywords = [
            '최대전력', '전력', 'mw', '발전', '수급', '설비용량',
            '공급능력', '공급예비력', '공급예비율', '전력통계'
        ]
        
        # 탄소/배출권 관련 키워드  
        carbon_keywords = [
            '종가', '시가', '거래량', '거래대금', 'kau', 'kcu', 'koc',
            '배출권', '탄소', '온실가스', '할당', '상쇄'
        ]
        
        # 키워드 매칭
        if any(keyword in target_lower for keyword in power_keywords):
            return 'power'
        elif any(keyword in target_lower for keyword in carbon_keywords):
            return 'carbon'
        else:
            # 실제 데이터에서 컬럼 존재 여부 확인
            if self.carbon_df is not None and target_column in self.carbon_df.columns:
                return 'carbon'
            elif self.power_df is not None and target_column in self.power_df.columns:
                return 'power'
            else:
                # 기본값: carbon (더 많은 거래 데이터 예상)
                return 'carbon'
                
    def _prepare_prophet_data(self, df: pd.DataFrame, target_column: str) -> Optional[pd.DataFrame]:
        """Prophet 형식으로 데이터 준비 (ds, y 컬럼)"""
        try:
            # 필요한 컬럼 확인
            if 'ds' not in df.columns:
                print("❌ 날짜 컬럼(ds)이 없습니다.")
                return None
                
            if target_column not in df.columns:
                print(f"❌ 타겟 컬럼 '{target_column}'이 없습니다.")
                available_cols = [col for col in df.columns if col != 'ds'][:10]
                print(f"📋 사용 가능한 컬럼: {', '.join(available_cols)}")
                
                # 🔍 유사한 컬럼명 찾기 (부분 매칭)
                similar_cols = [col for col in df.columns 
                               if target_column.replace('(', '').replace(')', '').lower() in col.lower() 
                               or col.replace('(', '').replace(')', '').lower() in target_column.lower()]
                
                if similar_cols:
                    print(f"💡 유사한 컬럼 발견: {similar_cols}")
                    # 가장 유사한 첫 번째 컬럼 사용
                    target_column = similar_cols[0]
                    print(f"🔄 '{target_column}' 컬럼으로 자동 변경")
                else:
                    return None
                
            # Prophet 형식으로 데이터 준비
            prophet_df = df[['ds', target_column]].copy()
            prophet_df.columns = ['ds', 'y']
            
            # 🔥 문자열 숫자 정리 (쉼표, 따옴표 제거)
            def clean_numeric_string(val):
                """문자열로 된 숫자를 실제 숫자로 변환"""
                if pd.isna(val):
                    return None
                    
                # 문자열로 변환 후 정리
                str_val = str(val).strip()
                
                # 따옴표 제거
                str_val = str_val.replace('"', '').replace("'", '')
                
                # 쉼표 제거
                str_val = str_val.replace(',', '')
                
                # 빈 문자열이나 0인 경우 제외
                if str_val == '' or str_val == '0':
                    return None
                    
                try:
                    return float(str_val)
                except:
                    return None
            
            print(f"🔧 '{target_column}' 데이터 정리 중...")
            prophet_df['y'] = prophet_df['y'].apply(clean_numeric_string)
            
            # 결측치 및 0값 제거
            prophet_df = prophet_df.dropna()
            prophet_df = prophet_df[prophet_df['y'] > 0]  # 0보다 큰 값만
            
            # 날짜 중복 제거 (최신 값 유지)
            prophet_df = prophet_df.drop_duplicates(subset=['ds'], keep='last')
            
            print(f"📊 정리 후 유효 데이터: {len(prophet_df)}개")
            
            if len(prophet_df) < 10:
                print(f"⚠️ 유효한 데이터가 부족합니다: {len(prophet_df)}개")
                if len(prophet_df) > 0:
                    print(f"💡 샘플 데이터: {prophet_df['y'].head().tolist()}")
                return None
                
            return prophet_df.sort_values('ds').reset_index(drop=True)
            
        except Exception as e:
            print(f"❌ Prophet 데이터 준비 오류: {e}")
            return None
            
    def predict(self, target_column: str, days_ahead: int = 7) -> Dict[str, Any]:
        """
        지정된 컬럼에 대해 예측 수행
        
        Args:
            target_column: 예측할 컬럼명
            days_ahead: 예측할 일수 (기본값: 7일)
            
        Returns:
            예측 결과 딕셔너리
        """
        if not PROPHET_AVAILABLE:
            return {
                'success': False,
                'error': 'Prophet이 설치되지 않았습니다. pip install prophet을 실행해주세요.',
                'predictions': None,
                'chart': None
            }
            
        print(f"🔮 '{target_column}' 예측 시작 (미래 {days_ahead}일)")
        
        # 1. 데이터 소스 자동 감지
        data_source = self._detect_prediction_source(target_column)
        print(f"📊 데이터 소스: {data_source}")
        
        # 2. 해당 데이터프레임 선택
        if data_source == 'power':
            df = self.power_df
        else:
            df = self.carbon_df
            
        if df is None:
            return {
                'success': False,
                'error': f'{data_source} 데이터가 로드되지 않았습니다.',
                'predictions': None,
                'chart': None
            }
            
        # 3. Prophet 형식으로 데이터 준비
        prophet_data = self._prepare_prophet_data(df, target_column)
        if prophet_data is None:
            return {
                'success': False,
                'error': f"'{target_column}' 컬럼의 예측 데이터를 준비할 수 없습니다.",
                'predictions': None,
                'chart': None
            }
            
        # 4. Prophet 모델 학습
        try:
            print("🤖 Prophet 모델 학습 중...")
            model = Prophet(**self.prophet_params)
            model.fit(prophet_data)
            
            # 5. 미래 예측
            future = model.make_future_dataframe(periods=days_ahead)
            forecast = model.predict(future)
            
            # 6. 결과 정리
            predictions = self._format_predictions(forecast, days_ahead, target_column)
            
            # 7. 시각화
            chart_path = self._create_prediction_chart(model, forecast, target_column, data_source)
            
            return {
                'success': True,
                'error': None,
                'predictions': predictions,
                'chart': chart_path,
                'data_source': data_source,
                'model_info': {
                    'training_data_points': len(prophet_data),
                    'prediction_days': days_ahead,
                    'date_range': f"{prophet_data['ds'].min().strftime('%Y-%m-%d')} ~ {prophet_data['ds'].max().strftime('%Y-%m-%d')}"
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"예측 모델 학습 오류: {str(e)}",
                'predictions': None,
                'chart': None
            }
    
    def predict_from_query(self, natural_query: str) -> Dict[str, Any]:
        """
        자연어 쿼리로 예측 수행
        
        예시:
        - "7일뒤 최대전력을 예측해줘"
        - "5일 후 종가 예측"
        - "내일 거래량은?"
        
        Args:
            natural_query: 자연어 예측 요청
            
        Returns:
            예측 결과 딕셔너리
        """
        print(f"🗣️ 자연어 쿼리: '{natural_query}'")
        
        # 자연어에서 컬럼명과 예측일수 추출
        target_column, days_ahead = self._parse_natural_language(natural_query)
        
        print(f"📝 해석 결과: '{target_column}' {days_ahead}일 예측")
        
        # 일반 예측 함수 호출
        result = self.predict(target_column, days_ahead)
        
        # 결과에 원본 쿼리 정보 추가
        if result['success']:
            result['original_query'] = natural_query
            result['parsed_column'] = target_column
            result['parsed_days'] = days_ahead
            
        return result
            
    def _format_predictions(self, forecast: pd.DataFrame, days_ahead: int, target_column: str) -> Dict[str, Any]:
        """예측 결과를 사용자 친화적 형식으로 변환"""
        # 미래 예측 부분만 추출
        future_predictions = forecast.tail(days_ahead)
        
        predictions = {
            'summary': {
                'target_column': target_column,
                'prediction_period': f"미래 {days_ahead}일",
                'average_predicted_value': float(future_predictions['yhat'].mean()),
                'trend': 'increasing' if future_predictions['yhat'].iloc[-1] > future_predictions['yhat'].iloc[0] else 'decreasing'
            },
            'daily_predictions': []
        }
        
        for _, row in future_predictions.iterrows():
            predictions['daily_predictions'].append({
                'date': row['ds'].strftime('%Y-%m-%d'),
                'predicted_value': float(row['yhat']),
                'lower_bound': float(row['yhat_lower']),
                'upper_bound': float(row['yhat_upper']),
                'confidence_interval': f"{float(row['yhat_lower']):.2f} ~ {float(row['yhat_upper']):.2f}"
            })
            
        return predictions
        
    def _create_prediction_chart(self, model: 'Prophet', forecast: pd.DataFrame, 
                               target_column: str, data_source: str) -> Optional[str]:
        """예측 결과 시각화 차트 생성"""
        try:
            fig = model.plot(forecast, figsize=(12, 6))
            plt.title(f'{target_column} 예측 결과 ({data_source} 데이터)', fontsize=14, fontweight='bold')
            plt.xlabel('날짜', fontsize=12)
            plt.ylabel(target_column, fontsize=12)
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            
            # 차트 저장
            chart_path = f"prediction_chart_{target_column}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            return chart_path
            
        except Exception as e:
            print(f"⚠️ 차트 생성 실패: {e}")
            plt.close('all')
            return None
            
    def get_available_columns(self) -> Dict[str, List[str]]:
        """예측 가능한 컬럼 목록 반환"""
        available = {'carbon': [], 'power': []}
        
        if self.carbon_df is not None:
            # 숫자형 컬럼만 추출 (날짜 제외)
            numeric_cols = self.carbon_df.select_dtypes(include=[np.number]).columns.tolist()
            available['carbon'] = [col for col in numeric_cols if col != 'ds']
            
        if self.power_df is not None:
            # 숫자형 컬럼만 추출 (날짜 제외)  
            numeric_cols = self.power_df.select_dtypes(include=[np.number]).columns.tolist()
            available['power'] = [col for col in numeric_cols if col != 'ds']
            
        return available
        
    def get_status(self) -> Dict[str, Any]:
        """에이전트 상태 정보 반환"""
        status = {
            'prophet_available': PROPHET_AVAILABLE,
            'data_loaded': {
                'carbon': self.carbon_df is not None,
                'power': self.power_df is not None
            }
        }
        
        if self.carbon_df is not None:
            status['carbon_data_info'] = {
                'rows': len(self.carbon_df),
                'columns': len(self.carbon_df.columns),
                'date_range': f"{self.carbon_df['ds'].min()} ~ {self.carbon_df['ds'].max()}" if 'ds' in self.carbon_df.columns else "날짜 정보 없음"
            }
            
        if self.power_df is not None:
            status['power_data_info'] = {
                'rows': len(self.power_df),
                'columns': len(self.power_df.columns),
                'date_range': f"{self.power_df['ds'].min()} ~ {self.power_df['ds'].max()}" if 'ds' in self.power_df.columns else "날짜 정보 없음"
            }
            
        return status 