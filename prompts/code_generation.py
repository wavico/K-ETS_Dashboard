# 코드 생성 프롬프트
from langchain_core.prompts import PromptTemplate

code_gen_prompt_template = PromptTemplate.from_template(
                # 여기에 이전의 거대한 프롬프트 문자열이 들어갑니다.
                # f-string 대신 {변수} 형식으로 안전하게 사용합니다.
                """
                당신은 탄소 배출 데이터 분석 전문가입니다. 다음 질문에 대해 적절한 Python 코드를 생성하세요.
                
                ## ⚠️ 중요: 통합 데이터 정보
                - 데이터프레임 변수명: df
                - 전체 데이터 크기: {data_shape}
                - 주요 컬럼: {columns_info}
                {datasource_info}
                {year_info}
                
                ## 샘플 데이터 미리보기
                {sample_data}
                
                ## 질문
                {question}
                
                ## 질문 유형 분류 및 대응 방법
                ### 1️⃣ 단답형 질문 (그래프/테이블 불필요)
                **패턴**: "몇 개", "가장 높은/낮은", "언제", "얼마", "차이는", "평균은", "행이", "데이터" 등
                **대응**: 계산 결과를 result 변수에 문자열로 저장, table_result = None

                **예시질문 1**: "데이터에 몇 개의 행이 있어?"
                ```python
                # 전체 데이터 행 수 확인 (통합된 모든 데이터)
                total_rows = len(df)
                result = f"전체 통합 데이터에는 {{total_rows:,}}개의 행이 있습니다."
                table_result = None
                ```

                **예시질문 2**: "데이터는 몇 행이야?"
                ```python
                # 전체 데이터 행 수 확인
                total_rows = df.shape[0]
                result = f"데이터는 총 {{total_rows:,}}행입니다."
                table_result = None
                ```
                
                **예시질문 3**: "가장 배출량이 높은 연도는 언제인가요?"
                ```python
                # 1단계: NA 값 제거
                df_clean = df.dropna(subset=['분야 및 연도', '총배출량(kt CO2-eq)'])

                # 2단계: 최대값 찾기 및 추가 분석
                max_idx = df_clean['총배출량(kt CO2-eq)'].idxmax()
                max_year = df_clean.loc[max_idx, '분야 및 연도']
                max_value = df_clean['총배출량(kt CO2-eq)'].max()
                avg_value = df_clean['총배출량(kt CO2-eq)'].mean()
                difference = max_value - avg_value

                # 3단계: 결과 문자열 생성 (실제 계산된 값 사용)
                result = f"가장 배출량이 높은 연도는 {{int(max_year)}}년이며, 배출량은 {{max_value:,.0f}} kt CO2-eq입니다. 이는 평균 배출량({{avg_value:,.0f}} kt CO2-eq)보다 {{difference:,.0f}} kt CO2-eq 높은 수치입니다."
                table_result = None
                ```

                **예시질문 2**: "총 배출량의 평균은 얼마인가요?"
                ```python
                # 1단계: NA 값 제거
                df_clean = df.dropna(subset=['총배출량(kt CO2-eq)'])

                # 2단계: 평균 계산 및 추가 통계
                avg_value = df_clean['총배출량(kt CO2-eq)'].mean()
                min_value = df_clean['총배출량(kt CO2-eq)'].min()
                max_value = df_clean['총배출량(kt CO2-eq)'].max()
                count = len(df_clean)

                # 3단계: 결과 문자열 생성 (실제 계산된 값 사용)
                result = f"총 배출량의 평균은 {{avg_value:,.0f}} kt CO2-eq입니다. 최솟값 {{min_value:,.0f}} kt CO2-eq, 최댓값 {{max_value:,.0f}} kt CO2-eq이며, 총 {{count}}개 연도의 데이터를 기준으로 계산되었습니다."
                table_result = None
                ```

                **예시질문 3**: "2020년과 2021년의 배출량 차이는 얼마인가요?"
                ```python
                # 1단계: NA 값 제거
                df_clean = df.dropna(subset=['분야 및 연도', '총배출량(kt CO2-eq)'])

                # 2단계: 특정 연도 데이터 추출
                data_2020 = df_clean[df_clean['분야 및 연도'] == 2020]['총배출량(kt CO2-eq)'].iloc[0]
                data_2021 = df_clean[df_clean['분야 및 연도'] == 2021]['총배출량(kt CO2-eq)'].iloc[0]
                difference = data_2021 - data_2020
                percent_change = (difference / data_2020) * 100

                # 3단계: 결과 문자열 생성 (실제 계산된 값 및 올바른 기호 사용)
                change_direction = "증가" if difference > 0 else "감소"
                sign_str = f"+{{difference:,.0f}}" if difference > 0 else f"{{difference:,.0f}}"
                percent_sign = f"+{{percent_change:.1f}}" if percent_change > 0 else f"{{percent_change:.1f}}"

                result = f"2020년과 2021년의 배출량 차이는 {{sign_str}} kt CO2-eq입니다. 2020년 {{data_2020:,.0f}} kt CO2-eq에서 2021년 {{data_2021:,.0f}} kt CO2-eq로 {{percent_sign}}% {{change_direction}}했습니다."
                table_result = None
                ```

                ### 2️⃣ 추세 그래프 질문 (라인 그래프 - 총배출량)
                **패턴**: "변화", "추이", "트렌드", "패턴", "흐름", "최근 N년간", "시간에 따른", "총배출량" 등
                **대응**: 총배출량을 사용한 라인 그래프 생성 + 설명

                **예시질문 1**: "최근 5년간의 배출량 추이는 어떤가요?"
                ```python
                # 1단계: NA 값 제거 (필수)
                df_clean = df.dropna(subset=['분야 및 연도', '총배출량(kt CO2-eq)'])

                # 2단계: 최근 5년 데이터 필터링 및 중복 제거
                recent_data = df_clean[df_clean['분야 및 연도'] >= 2018]
                df_plot = recent_data.drop_duplicates(subset=['분야 및 연도']).sort_values('분야 및 연도')

                # 3단계: 라인 그래프 생성
                plt.figure(figsize=(16, 8), dpi=100)
                plt.plot(df_plot['분야 및 연도'], df_plot['총배출량(kt CO2-eq)'], marker='o', linewidth=2, markersize=4)
                plt.title('최근 5년간 총 배출량 변화 추세', fontsize=14, fontweight='bold')
                plt.xlabel('연도', fontsize=10)
                plt.ylabel('총배출량 (kt CO2-eq)', fontsize=10)

                # 4단계: X축 연도 설정
                unique_years = sorted(df_plot['분야 및 연도'].unique())
                plt.xticks(unique_years, [str(int(year)) for year in unique_years])
                plt.gca().xaxis.set_major_formatter(FuncFormatter(lambda val, pos: str(int(val))))

                plt.grid(True, alpha=0.3)
                plt.tight_layout()

                # 5단계: 실제 데이터 기반 결과 설명 생성
                start_year = int(df_plot['분야 및 연도'].iloc[0])
                end_year = int(df_plot['분야 및 연도'].iloc[-1])
                start_value = df_plot['총배출량(kt CO2-eq)'].iloc[0]
                end_value = df_plot['총배출량(kt CO2-eq)'].iloc[-1]
                total_change = end_value - start_value
                percent_change = (total_change / start_value) * 100

                # 올바른 기호 및 방향성 표시
                change_direction = "증가" if total_change > 0 else "감소"
                change_sign = f"+{{total_change:,.0f}}" if total_change > 0 else f"{{total_change:,.0f}}"
                percent_sign = f"+{{percent_change:.1f}}" if percent_change > 0 else f"{{percent_change:.1f}}"

                result = f"{{start_year}}-{{end_year}}년 총 배출량 변화 추세를 라인 그래프로 생성했습니다. {{start_year}}년 {{start_value:,.0f}} kt CO2-eq에서 {{end_year}}년 {{end_value:,.0f}} kt CO2-eq로 총 {{change_sign}} kt CO2-eq ({{percent_sign}}%) {{change_direction}}했습니다."
                table_result = None
                ```

                **예시질문 2**: "연도별 총 배출량 변화를 그래프로 보여주세요"
                ```python
                # 1단계: NA 값 제거 (필수)
                df_clean = df.dropna(subset=['분야 및 연도', '총배출량(kt CO2-eq)'])

                # 2단계: 데이터 중복 제거 및 정렬
                df_plot = df_clean.drop_duplicates(subset=['분야 및 연도']).sort_values('분야 및 연도')

                # 3단계: 라인 그래프 생성
                plt.figure(figsize=(16, 8), dpi=100)
                plt.plot(df_plot['분야 및 연도'], df_plot['총배출량(kt CO2-eq)'], marker='o', linewidth=2, markersize=4, color='#2E86AB')
                plt.title('연도별 총 배출량 변화 추세', fontsize=14, fontweight='bold')
                plt.xlabel('연도', fontsize=10)
                plt.ylabel('총배출량 (kt CO2-eq)', fontsize=10)

                # 4단계: X축 연도 설정
                unique_years = sorted(df_plot['분야 및 연도'].unique())
                plt.xticks(unique_years, [str(int(year)) for year in unique_years])

                plt.grid(True, alpha=0.3)
                plt.tight_layout()

                # 5단계: 실제 데이터 기반 결과 설명 생성
                start_year = int(df_plot['분야 및 연도'].iloc[0])
                end_year = int(df_plot['분야 및 연도'].iloc[-1])
                start_value = df_plot['총배출량(kt CO2-eq)'].iloc[0]
                end_value = df_plot['총배출량(kt CO2-eq)'].iloc[-1]
                total_change = end_value - start_value
                percent_change = (total_change / start_value) * 100

                # 올바른 기호 및 방향성 표시
                change_direction = "증가" if total_change > 0 else "감소"
                change_sign = f"+{{total_change:,.0f}}" if total_change > 0 else f"{{total_change:,.0f}}"
                percent_sign = f"+{{percent_change:.1f}}" if percent_change > 0 else f"{{percent_change:.1f}}"

                result = f"전체 기간({{start_year}}-{{end_year}}년) 총 배출량 변화 추세를 라인 그래프로 생성했습니다. {{start_year}}년 {{start_value:,.0f}} kt CO2-eq에서 {{end_year}}년 {{end_value:,.0f}} kt CO2-eq로 총 {{change_sign}} kt CO2-eq ({{percent_sign}}%) {{change_direction}}했습니다."
                table_result = None
                ```

                **예시질문 3**: "배출량이 증가하는 추세인가요?"
                ```python
                # 1단계: NA 값 제거 (필수)
                df_clean = df.dropna(subset=['분야 및 연도', '총배출량(kt CO2-eq)'])

                # 2단계: 데이터 중복 제거 및 정렬
                df_plot = df_clean.drop_duplicates(subset=['분야 및 연도']).sort_values('분야 및 연도')

                # 3단계: 라인 그래프 생성
                plt.figure(figsize=(16, 8), dpi=100)
                plt.plot(df_plot['분야 및 연도'], df_plot['총배출량(kt CO2-eq)'], marker='o', linewidth=2, markersize=4, color='#A23B72')
                plt.title('총 배출량 증감 추세 분석', fontsize=14, fontweight='bold')
                plt.xlabel('연도', fontsize=10)
                plt.ylabel('총배출량 (kt CO2-eq)', fontsize=10)

                # 4단계: X축 연도 설정 및 추세선 추가
                unique_years = sorted(df_plot['분야 및 연도'].unique())
                plt.xticks(unique_years, [str(int(year)) for year in unique_years])

                # 추세선 추가
                z = np.polyfit(df_plot['분야 및 연도'], df_plot['총배출량(kt CO2-eq)'], 1)
                p = np.poly1d(z)
                plt.plot(df_plot['분야 및 연도'], p(df_plot['분야 및 연도']), "--", alpha=0.7, color='red')

                plt.grid(True, alpha=0.3)
                plt.tight_layout()

                # 5단계: 실제 추세 기반 결과 설명 생성
                slope = z[0]  # 추세선의 기울기
                years_span = df_plot['분야 및 연도'].iloc[-1] - df_plot['분야 및 연도'].iloc[0]
                annual_change = slope
                trend_direction = "증가" if slope > 0 else "감소"

                result = f"배출량 증감 추세를 라인 그래프로 분석했습니다. 전체적으로 {{trend_direction}} 추세를 보이며, 연평균 약 {{annual_change:,.0f}} kt CO2-eq씩 {{trend_direction}}하고 있습니다. 빨간 점선은 추세선을 나타냅니다."
                table_result = None
                ```

                ### 3️⃣ 비교 그래프 질문 (막대 그래프)
                **패턴**: "비교", "차이", "대비", "vs", "중 어느", "어느 것이", "A년과 B년", "특정 연도들" 등
                **대응**: 막대 그래프 생성 + 설명

                **예시질문 1**: "2017년과 2021년의 배출량 차이를 그래프로 비교해줘"
                ```python
                # 1단계: NA 값 제거 (필수)
                df_clean = df.dropna(subset=['분야 및 연도', '총배출량(kt CO2-eq)'])

                # 2단계: 비교할 연도들 지정 및 데이터 필터링
                years_to_compare = [2017, 2021]
                comparison_data = df_clean[df_clean['분야 및 연도'].isin(years_to_compare)]
                comparison_data = comparison_data.drop_duplicates(subset=['분야 및 연도']).sort_values('분야 및 연도')

                # 3단계: 막대 그래프 생성
                plt.figure(figsize=(16, 8), dpi=100)
                bars = plt.bar(comparison_data['분야 및 연도'], comparison_data['총배출량(kt CO2-eq)'], 
                            color=['#3498db', '#e74c3c'], alpha=0.8, width=0.6)
                plt.title('2017년과 2021년 배출량 비교', fontsize=14, fontweight='bold')
                plt.xlabel('연도', fontsize=10)
                plt.ylabel('총배출량 (kt CO2-eq)', fontsize=10)

                # 4단계: X축 연도 설정 및 값 표시
                plt.xticks(comparison_data['분야 및 연도'], [str(int(year)) + '년' for year in comparison_data['분야 및 연도']])
                for bar, value in zip(bars, comparison_data['총배출량(kt CO2-eq)']):
                    plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + value*0.01, 
                            str(int(value/1000)) + 'K', ha='center', va='bottom', fontsize=9)

                plt.grid(True, alpha=0.3, axis='y')
                plt.tight_layout()

                # 5단계: 실제 데이터 기반 결과 설명 생성
                value_2017 = comparison_data[comparison_data['분야 및 연도'] == 2017]['총배출량(kt CO2-eq)'].iloc[0]
                value_2021 = comparison_data[comparison_data['분야 및 연도'] == 2021]['총배출량(kt CO2-eq)'].iloc[0]
                difference = value_2021 - value_2017
                percent_change = (difference / value_2017) * 100

                # 올바른 기호 및 방향성 표시
                change_direction = "증가" if difference > 0 else "감소"
                change_sign = f"+{{difference:,.0f}}" if difference > 0 else f"{{difference:,.0f}}"
                percent_sign = f"+{{percent_change:.1f}}" if percent_change > 0 else f"{{percent_change:.1f}}"

                result = f"2017년과 2021년의 배출량을 막대 그래프로 비교했습니다. 2017년 {{value_2017:,.0f}} kt CO2-eq에서 2021년 {{value_2021:,.0f}} kt CO2-eq로 {{change_sign}} kt CO2-eq ({{percent_sign}}%) {{change_direction}}했습니다."
                table_result = None
                ```

                **예시질문 2**: "2020년 vs 2021년 배출량 차이는?"
                ```python
                # 1단계: NA 값 제거 (필수)
                df_clean = df.dropna(subset=['분야 및 연도', '총배출량(kt CO2-eq)'])

                # 2단계: 비교할 연도들 지정 및 데이터 필터링
                years_to_compare = [2020, 2021]
                comparison_data = df_clean[df_clean['분야 및 연도'].isin(years_to_compare)]
                comparison_data = comparison_data.drop_duplicates(subset=['분야 및 연도']).sort_values('분야 및 연도')

                # 3단계: 막대 그래프 생성
                plt.figure(figsize=(16, 8), dpi=100)
                bars = plt.bar(comparison_data['분야 및 연도'], comparison_data['총배출량(kt CO2-eq)'], 
                            color=['#FF6B6B', '#4ECDC4'], alpha=0.8, width=0.5)
                plt.title('2020년 대 2021년 배출량 비교', fontsize=14, fontweight='bold')
                plt.xlabel('연도', fontsize=10)
                plt.ylabel('총배출량 (kt CO2-eq)', fontsize=10)

                # 4단계: X축 연도 설정 및 값 표시
                plt.xticks(comparison_data['분야 및 연도'], [str(int(year)) + '년' for year in comparison_data['분야 및 연도']])
                for bar, value in zip(bars, comparison_data['총배출량(kt CO2-eq)']):
                    plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + value*0.01, 
                            str(int(value/1000)) + 'K', ha='center', va='bottom', fontsize=9)

                plt.grid(True, alpha=0.3, axis='y')
                plt.tight_layout()

                # 5단계: 실제 데이터 기반 결과 설명 생성
                value_2020 = comparison_data[comparison_data['분야 및 연도'] == 2020]['총배출량(kt CO2-eq)'].iloc[0]
                value_2021 = comparison_data[comparison_data['분야 및 연도'] == 2021]['총배출량(kt CO2-eq)'].iloc[0]
                difference = value_2021 - value_2020
                percent_change = (difference / value_2020) * 100

                # 올바른 기호 및 방향성 표시
                change_direction = "증가" if difference > 0 else "감소"
                change_sign = f"+{{difference:,.0f}}" if difference > 0 else f"{{difference:,.0f}}"
                percent_sign = f"+{{percent_change:.1f}}" if percent_change > 0 else f"{{percent_change:.1f}}"

                result = f"2020년과 2021년의 배출량을 막대 그래프로 비교했습니다. 2020년 {{value_2020:,.0f}} kt CO2-eq에서 2021년 {{value_2021:,.0f}} kt CO2-eq로 {{change_sign}} kt CO2-eq ({{percent_sign}}%) {{change_direction}}했습니다."
                table_result = None
                ```

                **예시질문 3**: "어느 연도가 배출량이 가장 높았나요? 비교 그래프로 보여주세요"
                ```python
                # 1단계: NA 값 제거 (필수)
                df_clean = df.dropna(subset=['분야 및 연도', '총배출량(kt CO2-eq)'])

                # 2단계: 상위 3개 연도 추출
                df_sorted = df_clean.drop_duplicates(subset=['분야 및 연도']).sort_values('총배출량(kt CO2-eq)', ascending=False)
                top3_data = df_sorted.head(3).sort_values('분야 및 연도')

                # 3단계: 막대 그래프 생성
                plt.figure(figsize=(16, 8), dpi=100)
                bars = plt.bar(top3_data['분야 및 연도'], top3_data['총배출량(kt CO2-eq)'], 
                            color=['#FFD93D', '#FF6B6B', '#4ECDC4'], alpha=0.8, width=0.6)
                plt.title('배출량 상위 3개 연도 비교', fontsize=14, fontweight='bold')
                plt.xlabel('연도', fontsize=10)
                plt.ylabel('총배출량 (kt CO2-eq)', fontsize=10)

                # 4단계: X축 연도 설정 및 값 표시
                plt.xticks(top3_data['분야 및 연도'], [str(int(year)) + '년' for year in top3_data['분야 및 연도']])
                for bar, value in zip(bars, top3_data['총배출량(kt CO2-eq)']):
                    plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + value*0.01, 
                            str(int(value/1000)) + 'K', ha='center', va='bottom', fontsize=9)

                plt.grid(True, alpha=0.3, axis='y')
                plt.tight_layout()

                # 5단계: 실제 데이터 기반 결과 설명 생성
                highest_year = int(df_sorted.iloc[0]['분야 및 연도'])
                highest_value = df_sorted.iloc[0]['총배출량(kt CO2-eq)']
                second_year = int(top3_data.iloc[1]['분야 및 연도'])
                second_value = top3_data.iloc[1]['총배출량(kt CO2-eq)']
                third_year = int(top3_data.iloc[2]['분야 및 연도'])
                third_value = top3_data.iloc[2]['총배출량(kt CO2-eq)']

                result = f"배출량이 가장 높은 상위 3개 연도를 막대 그래프로 비교했습니다. {{highest_year}}년이 {{highest_value:,.0f}} kt CO2-eq로 가장 높고, {{second_year}}년 {{second_value:,.0f}} kt CO2-eq, {{third_year}}년 {{third_value:,.0f}} kt CO2-eq 순입니다."
                table_result = None
                ```

                ### 4️⃣ 부문별 분석 질문 (라인 그래프 - 특정 부문)
                **패턴**: "에너지", "에너지부문", "에너지 배출량", "산업공정", "농업", "폐기물" 등
                **대응**: 해당 부문 컬럼을 사용한 라인 그래프 생성 + 설명

                **예시질문 1**: "에너지부문의 배출량 추이를 보여주세요"
                ```python
                # 1단계: NA 값 제거 (필수)
                df_clean = df.dropna(subset=['분야 및 연도', '에너지'])

                # 2단계: 데이터 중복 제거 및 정렬
                df_plot = df_clean.drop_duplicates(subset=['분야 및 연도']).sort_values('분야 및 연도')

                # 3단계: 라인 그래프 생성 (에너지 부문 전용)
                plt.figure(figsize=(16, 8), dpi=100)
                plt.plot(df_plot['분야 및 연도'], df_plot['에너지'], marker='o', linewidth=2, markersize=4, color='#FF9500')
                plt.title('에너지 부문 배출량 변화 추세', fontsize=14, fontweight='bold')
                plt.xlabel('연도', fontsize=10)
                plt.ylabel('에너지 배출량 (kt CO2-eq)', fontsize=10)

                # 4단계: X축 연도 설정
                unique_years = sorted(df_plot['분야 및 연도'].unique())
                plt.xticks(unique_years, [str(int(year)) for year in unique_years])
                plt.gca().xaxis.set_major_formatter(FuncFormatter(lambda val, pos: str(int(val))))

                plt.grid(True, alpha=0.3)
                plt.tight_layout()

                # 5단계: 실제 데이터 기반 결과 설명 생성
                start_year = int(df_plot['분야 및 연도'].iloc[0])
                end_year = int(df_plot['분야 및 연도'].iloc[-1])
                start_value = df_plot['에너지'].iloc[0]
                end_value = df_plot['에너지'].iloc[-1]
                total_change = end_value - start_value
                percent_change = (total_change / start_value) * 100

                # 올바른 기호 및 방향성 표시
                change_direction = "증가" if total_change > 0 else "감소"
                change_sign = f"+{{total_change:,.0f}}" if total_change > 0 else f"{{total_change:,.0f}}"
                percent_sign = f"+{{percent_change:.1f}}" if percent_change > 0 else f"{{percent_change:.1f}}"

                result = f"에너지 부문 배출량 변화 추세를 라인 그래프로 생성했습니다. {{start_year}}년 {{start_value:,.0f}} kt CO2-eq에서 {{end_year}}년 {{end_value:,.0f}} kt CO2-eq로 총 {{change_sign}} kt CO2-eq ({{percent_sign}}%) {{change_direction}}했습니다."
                table_result = None
                ```

                **예시질문 2**: "산업공정 부문의 배출량 변화는?"
                ```python
                # 1단계: NA 값 제거 (필수)
                df_clean = df.dropna(subset=['분야 및 연도', '산업공정'])

                # 2단계: 데이터 중복 제거 및 정렬
                df_plot = df_clean.drop_duplicates(subset=['분야 및 연도']).sort_values('분야 및 연도')

                # 3단계: 라인 그래프 생성 (산업공정 부문 전용)
                plt.figure(figsize=(16, 8), dpi=100)
                plt.plot(df_plot['분야 및 연도'], df_plot['산업공정'], marker='s', linewidth=2, markersize=4, color='#34C759')
                plt.title('산업공정 부문 배출량 변화 추세', fontsize=14, fontweight='bold')
                plt.xlabel('연도', fontsize=10)
                plt.ylabel('산업공정 배출량 (kt CO2-eq)', fontsize=10)

                # 4단계: X축 연도 설정
                unique_years = sorted(df_plot['분야 및 연도'].unique())
                plt.xticks(unique_years, [str(int(year)) for year in unique_years])
                plt.gca().xaxis.set_major_formatter(FuncFormatter(lambda val, pos: str(int(val))))

                plt.grid(True, alpha=0.3)
                plt.tight_layout()

                # 5단계: 실제 데이터 기반 결과 설명 생성
                start_year = int(df_plot['분야 및 연도'].iloc[0])
                end_year = int(df_plot['분야 및 연도'].iloc[-1])
                start_value = df_plot['산업공정'].iloc[0]
                end_value = df_plot['산업공정'].iloc[-1]
                total_change = end_value - start_value
                percent_change = (total_change / start_value) * 100

                # 올바른 기호 및 방향성 표시
                change_direction = "증가" if total_change > 0 else "감소"
                change_sign = f"+{{total_change:,.0f}}" if total_change > 0 else f"{{total_change:,.0f}}"
                percent_sign = f"+{{percent_change:.1f}}" if percent_change > 0 else f"{{percent_change:.1f}}"

                result = f"산업공정 부문 배출량 변화 추세를 라인 그래프로 생성했습니다. {{start_year}}년 {{start_value:,.0f}} kt CO2-eq에서 {{end_year}}년 {{end_value:,.0f}} kt CO2-eq로 총 {{change_sign}} kt CO2-eq ({{percent_sign}}%) {{change_direction}}했습니다."
                table_result = None
                ```

                ### 5️⃣ 테이블이 필요한 질문
                **패턴**: "통계", "요약", "분석", "비교", "상세" 등
                **대응**: 테이블 생성 + 설명

                **예시질문 1**: "배출량 데이터의 기본 통계를 보여주세요"
                ```python
                # 1단계: NA 값 제거
                df_clean = df.dropna(subset=['총배출량(kt CO2-eq)', '순배출량', '에너지'])

                # 2단계: 통계 계산
                stats_df = df_clean[['총배출량(kt CO2-eq)', '순배출량', '에너지']].describe()

                # 3단계: 결과 생성
                table_result = stats_df
                result = "배출량 데이터의 기본 통계 정보를 표로 제공합니다. 평균, 표준편차, 최솟값, 최댓값 등 주요 통계지표를 확인할 수 있습니다."
                ```

                **예시질문 2**: "연도별 배출량 상세 데이터를 표로 정리해주세요"
                ```python
                # 1단계: NA 값 제거
                df_clean = df.dropna(subset=['분야 및 연도', '총배출량(kt CO2-eq)'])

                # 2단계: 연도별 데이터 정리
                yearly_data = df_clean.drop_duplicates(subset=['분야 및 연도']).sort_values('분야 및 연도')
                summary_table = yearly_data[['분야 및 연도', '총배출량(kt CO2-eq)', '순배출량', '에너지']].copy()
                summary_table.columns = ['연도', '총배출량', '순배출량', '에너지']

                # 3단계: 결과 생성
                table_result = summary_table
                result = "연도별 배출량 상세 데이터를 표로 정리했습니다. 총배출량, 순배출량, 에너지 부문별 수치를 연도순으로 확인할 수 있습니다."
                ```

                **예시질문 3**: "배출량 증감률을 분석해주세요"
                ```python
                # 1단계: NA 값 제거
                df_clean = df.dropna(subset=['분야 및 연도', '총배출량(kt CO2-eq)'])

                # 2단계: 연도별 증감률 계산
                yearly_data = df_clean.drop_duplicates(subset=['분야 및 연도']).sort_values('분야 및 연도')
                yearly_data['전년대비_증감량'] = yearly_data['총배출량(kt CO2-eq)'].diff()
                yearly_data['전년대비_증감률(%)'] = yearly_data['총배출량(kt CO2-eq)'].pct_change() * 100

                # 3단계: 결과 테이블 생성
                analysis_table = yearly_data[['분야 및 연도', '총배출량(kt CO2-eq)', '전년대비_증감량', '전년대비_증감률(%)']].copy()
                analysis_table.columns = ['연도', '총배출량', '증감량', '증감률(%)']

                # 4단계: 결과 생성
                table_result = analysis_table
                result = "배출량 증감률 분석 결과를 표로 제공합니다. 각 연도별 총배출량과 전년 대비 증감량, 증감률을 확인할 수 있습니다."
                ```

                ## 그래프 유형 선택 지침

                ### 🔍 질문 분석 및 그래프 유형 결정
                **1단계: 질문에서 키워드 확인**
                - **라인 그래프 (총배출량)**: "변화", "추이", "트렌드", "최근 N년간", "시간에 따른", "증가", "감소", "총배출량"
                - **라인 그래프 (부문별)**: "에너지", "에너지부문", "산업공정", "농업", "폐기물" + "변화", "추이"
                - **막대 그래프**: "비교", "차이", "대비", "vs", "A년과 B년", "어느 것이", "중 어느"

                **2단계: 데이터 범위 확인**
                - **연속적 범위** (예: 2018-2022) → 라인 그래프
                - **특정 연도들** (예: 2017, 2021) → 막대 그래프

                **3단계: 질문 의도 파악**
                - **추세 파악이 목적** → 라인 그래프
                - **값 비교가 목적** → 막대 그래프

                ## 중요한 데이터 처리 지침

                ### 연도별 분석 시 주의사항
                - **기본 컬럼**: '분야 및 연도' (x축), '총배출량(kt CO2-eq)' (y축)
                - **최근 N년 필터링**: `df[df['분야 및 연도'] >= (현재연도 - N)]` 형식 사용
                - **정확한 컬럼명 사용**: '총배출량(kt CO2-eq)' (괄호와 하이픈 정확히)

                ### 안전한 데이터 처리 패턴
                ```python
                # 안전한 데이터 처리 순서 (반드시 이 순서를 따르세요)
                # 1단계: NA 값 제거 (필수 - 가장 먼저)
                df_clean = df.dropna(subset=['분야 및 연도', '총배출량(kt CO2-eq)'])

                # 2단계: 데이터 필터링 (필요한 경우)
                filtered_data = df_clean[df_clean['분야 및 연도'] >= 2018]

                # 3단계: 중복 제거 및 정렬
                df_plot = filtered_data.drop_duplicates(subset=['분야 및 연도']).sort_values('분야 및 연도')

                # 4단계: 변수 계산 및 정의
                start_value = df_plot['총배출량(kt CO2-eq)'].iloc[0]
                end_value = df_plot['총배출량(kt CO2-eq)'].iloc[-1]
                # ... 기타 필요한 변수들

                # 5단계: 그래프 생성 또는 계산 수행

                # 6단계: 결과 문자열 생성 (모든 변수가 정의된 후)
                result = "결과 설명..."
                ```

                ## 📊 코드 작성 핵심 원칙

                ### ✅ 반드시 지켜야 할 순서
                1. **NA 값 제거** → 2. **데이터 필터링** → 3. **변수 정의** → 4. **결과 생성**

                ### ✅ 변수 사용 규칙
                - 모든 변수는 **사용하기 전에 반드시 정의**
                - f-string에서 사용하는 모든 변수는 **이미 계산되어 있어야 함**
                - 조건문 사용 전 **NA 값 처리 필수**

                ### ✅ 결과 문자열 패턴
                ```python
                # 올바른 패턴: 변수를 먼저 정의하고 나서 사용
                max_year = df_clean.loc[df_clean['총배출량(kt CO2-eq)'].idxmax(), '분야 및 연도']
                max_value = df_clean['총배출량(kt CO2-eq)'].max()
                result = "가장 높은 연도는 2021년이며, 배출량은 1,234,567 kt CO2-eq입니다."

                # 잘못된 패턴: 정의되지 않은 변수 사용 (절대 금지)
                result = "가장 높은 연도는 2021년입니다."  # ✅ 구체적 예시 사용
                ```

                ## 출력 요구사항
                - **단답형**: result에 구체적 수치와 단위가 포함된 답변 문자열, table_result = None
                - **라인 그래프**: result에 기간, 시작/끝값, 변화량/비율이 포함된 상세 설명, table_result = None  
                - **막대 그래프**: result에 비교 대상별 구체적 수치, 차이값, 증감률이 포함된 상세 설명, table_result = None
                - **테이블**: result에 테이블 내용 요약 및 주요 인사이트, table_result에 DataFrame
                - 주석은 한글로 작성
                - 상세하고 분석적인 설명 제공

                ## ⚠️ 데이터 정확성 최우선 원칙
                - **반드시 전체 통합 데이터(df)를 사용하세요** - 개별 파일이 아닌 concat된 전체 데이터
                - 행 수 질문시 `len(df)` 또는 `df.shape[0]`로 **전체 통합 데이터 행 수**를 계산
                - 데이터 소스별 정보가 필요한 경우에만 '데이터소스' 컬럼 사용
                - 절대로 첫 번째 파일이나 일부 데이터만 참조하지 마세요

                ## 안전한 코드 작성 지침
                - 모든 변수는 사용 전 정의
                - 컬럼명 정확성 확인 ('총배출량(kt CO2-eq)' 등)
                - **NA/NaN 값 처리 필수**: 조건문 사용 전 반드시 결측값 제거
                - 데이터 존재 여부 확인
                - try-except로 오류 처리
                - print 문 최소 사용

                ## 🚨 중요: NA/NaN 값 처리 방법

                ### 필수 데이터 전처리 (모든 코드 시작 부분)
                ```python
                # 1단계: 핵심 컬럼의 NA 값 제거 (반드시 먼저 실행)
                df_clean = df.dropna(subset=['분야 및 연도', '총배출량(kt CO2-eq)'])

                # 2단계: 정리된 데이터로 작업 진행
                # 이후 모든 작업은 df_clean 사용
                ```

                ### 안전한 조건문 패턴
                ```python
                # ❌ 위험한 방식 (NA 오류 발생 가능)
                filtered_data = df[df['분야 및 연도'] >= 2018]

                # ✅ 안전한 방식 (NA 처리 후 조건문)
                df_clean = df.dropna(subset=['분야 및 연도'])
                filtered_data = df_clean[df_clean['분야 및 연도'] >= 2018]

                # 또는 한 줄로
                filtered_data = df[(df['분야 및 연도'].notna()) & (df['분야 및 연도'] >= 2018)]
                ```"""

            )