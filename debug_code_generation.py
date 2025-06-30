#!/usr/bin/env python3
"""
코드 생성 디버깅 스크립트
LLM이 어떤 코드를 생성하는지 확인합니다.
"""

import os
import sys
from pathlib import Path

# 프로젝트 루트 디렉토리 추가
sys.path.append(str(Path(__file__).parent))

from agent.enhanced_carbon_rag_agent import EnhancedCarbonRAGAgent

def debug_code_generation():
    """코드 생성 과정 디버깅"""
    print("🔍 코드 생성 디버깅 시작")
    print("=" * 50)
    
    # 에이전트 초기화
    agent = EnhancedCarbonRAGAgent()
    
    # 테스트 질문
    question = "연도별 총 배출량 변화를 그래프로 보여줘"
    print(f"📝 질문: {question}")
    
    # 코드 생성
    print("\n🔧 코드 생성 중...")
    code = agent._generate_code(question)
    
    if code:
        print("\n✅ 생성된 코드:")
        print("-" * 40)
        print(code)
        print("-" * 40)
        
        # 코드 실행
        print("\n⚡ 코드 실행 중...")
        result, has_plot, table_data, figure_obj = agent._execute_code(code)
        
        print(f"\n📊 실행 결과:")
        print(f"   - 결과: {result}")
        print(f"   - 그래프 생성: {has_plot}")
        print(f"   - 테이블 데이터: {table_data is not None}")
        print(f"   - Figure 객체: {figure_obj is not None}")
        
    else:
        print("❌ 코드 생성 실패")

if __name__ == "__main__":
    debug_code_generation() 