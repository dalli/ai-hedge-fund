# src/agents/example_agent.py
from __future__ import annotations

import json
from typing_extensions import Literal
from pydantic import BaseModel

from src.graph.state import AgentState, show_agent_reasoning
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage

from src.tools.api import (
    get_financial_metrics,
    get_market_cap,
    search_line_items,
)
from src.utils.api_key import get_api_key_from_state
from src.utils.llm import call_llm
from src.utils.progress import progress


class ExampleAgentSignal(BaseModel):
    signal: Literal["bullish", "bearish", "neutral"]
    confidence: float          # 0‒100
    reasoning: str


def example_agent(state: AgentState, agent_id: str = "example_agent"):
    """
    새로운 AI 에이전트의 설명을 여기에 작성합니다.
    
    주요 분석 방법:
    - 분석 방법 1
    - 분석 방법 2
    - 분석 방법 3
    """
    data = state["data"]
    end_date = data["end_date"]
    tickers = data["tickers"]
    api_key = get_api_key_from_state(state, "FINANCIAL_DATASETS_API_KEY")

    analysis_data: dict[str, dict] = {}
    example_signals: dict[str, dict] = {}

    for ticker in tickers:
        progress.update_status(agent_id, ticker, "데이터 수집 중...")
        
        # 1. 필요한 데이터 수집
        metrics = get_financial_metrics(ticker, end_date, period="ttm", limit=5, api_key=api_key)
        
        line_items = search_line_items(
            ticker,
            [
                "revenue",
                "net_income",
                "total_assets",
                "total_debt",
                "free_cash_flow",
            ],
            end_date,
            api_key=api_key,
        )
        
        market_cap = get_market_cap(ticker, end_date, api_key=api_key)

        # 2. 핵심 분석 수행
        progress.update_status(agent_id, ticker, "핵심 지표 분석 중...")
        core_analysis = analyze_core_metrics(metrics, line_items)
        
        progress.update_status(agent_id, ticker, "고급 분석 수행 중...")
        advanced_analysis = perform_advanced_analysis(metrics, line_items)
        
        progress.update_status(agent_id, ticker, "종합 평가 중...")
        comprehensive_score = calculate_comprehensive_score(core_analysis, advanced_analysis)

        # 3. 신호 생성
        signal, confidence, reasoning = generate_signal(comprehensive_score, market_cap)
        
        # 4. 결과 저장
        example_signals[ticker] = {
            "signal": signal,
            "confidence": confidence,
            "reasoning": reasoning,
            "analysis_details": {
                "core_score": core_analysis["score"],
                "advanced_score": advanced_analysis["score"],
                "comprehensive_score": comprehensive_score,
            }
        }

        progress.update_status(agent_id, ticker, "완료")

    # 5. LLM을 통한 최종 검증 및 설명
    final_signals = validate_with_llm(example_signals, state, agent_id)

    # 6. 메시지 생성 및 반환
    message = HumanMessage(
        content=json.dumps(final_signals),
        name=agent_id,
    )

    if state["metadata"]["show_reasoning"]:
        show_agent_reasoning(final_signals, "Example Agent")

    progress.update_status(agent_id, None, "완료")

    return {
        "messages": state["messages"] + [message],
        "data": state["data"],
    }


def analyze_core_metrics(metrics, line_items):
    """핵심 지표 분석"""
    score = 0
    max_score = 0
    reasoning = {}
    
    # 수익성 분석
    if metrics and len(metrics) > 0:
        latest = metrics[0]
        
        # ROE 분석
        if latest.return_on_equity:
            if latest.return_on_equity > 0.15:
                score += 3
                reasoning["roe"] = "우수한 ROE (15% 이상)"
            elif latest.return_on_equity > 0.10:
                score += 2
                reasoning["roe"] = "양호한 ROE (10-15%)"
            elif latest.return_on_equity > 0.05:
                score += 1
                reasoning["roe"] = "보통 ROE (5-10%)"
            else:
                reasoning["roe"] = "낮은 ROE (5% 미만)"
            max_score += 3
        
        # 부채비율 분석
        if latest.debt_to_equity:
            if latest.debt_to_equity < 0.3:
                score += 2
                reasoning["debt"] = "보수적 부채비율 (30% 미만)"
            elif latest.debt_to_equity < 0.5:
                score += 1
                reasoning["debt"] = "적정 부채비율 (30-50%)"
            else:
                reasoning["debt"] = "높은 부채비율 (50% 이상)"
            max_score += 2
    
    return {
        "score": score,
        "max_score": max_score,
        "reasoning": reasoning
    }


def perform_advanced_analysis(metrics, line_items):
    """고급 분석 수행"""
    score = 0
    max_score = 0
    reasoning = {}
    
    # 성장성 분석
    if metrics and len(metrics) > 1:
        current = metrics[0]
        previous = metrics[1]
        
        # 매출 성장률
        if current.revenue_growth:
            if current.revenue_growth > 0.20:
                score += 3
                reasoning["revenue_growth"] = "높은 매출 성장 (20% 이상)"
            elif current.revenue_growth > 0.10:
                score += 2
                reasoning["revenue_growth"] = "양호한 매출 성장 (10-20%)"
            elif current.revenue_growth > 0.05:
                score += 1
                reasoning["revenue_growth"] = "보통 매출 성장 (5-10%)"
            else:
                reasoning["revenue_growth"] = "낮은 매출 성장 (5% 미만)"
            max_score += 3
        
        # 이익 성장률
        if current.earnings_growth:
            if current.earnings_growth > 0.25:
                score += 2
                reasoning["earnings_growth"] = "높은 이익 성장 (25% 이상)"
            elif current.earnings_growth > 0.15:
                score += 1
                reasoning["earnings_growth"] = "양호한 이익 성장 (15-25%)"
            else:
                reasoning["earnings_growth"] = "보통 이익 성장 (15% 미만)"
            max_score += 2
    
    return {
        "score": score,
        "max_score": max_score,
        "reasoning": reasoning
    }


def calculate_comprehensive_score(core_analysis, advanced_analysis):
    """종합 점수 계산"""
    total_score = core_analysis["score"] + advanced_analysis["score"]
    max_possible_score = core_analysis["max_score"] + advanced_analysis["max_score"]
    
    if max_possible_score == 0:
        return 0
    
    return (total_score / max_possible_score) * 100


def generate_signal(comprehensive_score, market_cap):
    """신호 생성"""
    if comprehensive_score >= 80:
        signal = "bullish"
        confidence = comprehensive_score
        reasoning = f"종합 점수 {comprehensive_score:.1f}%로 매우 우수한 투자 대상"
    elif comprehensive_score >= 60:
        signal = "bullish"
        confidence = comprehensive_score
        reasoning = f"종합 점수 {comprehensive_score:.1f}%로 양호한 투자 대상"
    elif comprehensive_score >= 40:
        signal = "neutral"
        confidence = 50
        reasoning = f"종합 점수 {comprehensive_score:.1f}%로 중립적인 투자 대상"
    else:
        signal = "bearish"
        confidence = 100 - comprehensive_score
        reasoning = f"종합 점수 {comprehensive_score:.1f}%로 투자에 주의가 필요한 대상"
    
    return signal, confidence, reasoning


def validate_with_llm(signals, state, agent_id):
    """LLM을 통한 최종 검증 및 설명"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", """당신은 투자 분석 전문가입니다. 
        주어진 분석 결과를 검토하고 최종 투자 신호를 결정해야 합니다.
        
        분석 결과:
        {analysis_data}
        
        각 종목에 대해 다음을 제공하세요:
        1. 최종 신호 (bullish/bearish/neutral)
        2. 신뢰도 (0-100)
        3. 간결한 근거 설명
        
        JSON 형식으로 응답하세요:
        {
            "ticker": {
                "signal": "signal",
                "confidence": confidence,
                "reasoning": "reasoning"
            }
        }"""),
        ("human", "분석 결과를 검토하고 최종 신호를 결정해주세요.")
    ])
    
    try:
        result = call_llm(
            prompt,
            {"analysis_data": json.dumps(signals, indent=2, ensure_ascii=False)},
            state,
            agent_id
        )
        
        # LLM 결과 파싱
        parsed_result = json.loads(result)
        return parsed_result
        
    except Exception as e:
        # LLM 호출 실패 시 원본 신호 사용
        return signals