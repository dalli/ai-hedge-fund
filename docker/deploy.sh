#!/bin/bash

# AI Hedge Fund Docker Compose 배포 스크립트

set -e

echo "🚀 AI Hedge Fund Docker Compose 배포 시작"
echo ""

# Docker 데몬 확인
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker 데몬이 실행되지 않았습니다."
    echo "   Docker Desktop을 시작한 후 다시 시도해주세요."
    exit 1
fi

echo "✅ Docker 데몬 확인 완료"
echo ""

# 현재 디렉토리 확인
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ docker-compose.yml 파일을 찾을 수 없습니다."
    echo "   docker/ 디렉토리에서 실행해주세요."
    exit 1
fi

# 기존 서비스 중지 및 제거
echo "📦 기존 서비스 중지 및 제거 중..."
docker compose down
echo "✅ 기존 서비스 제거 완료"
echo ""

# 이미지 재빌드
echo "🔨 이미지 재빌드 중..."
docker compose build --no-cache backend frontend
echo "✅ 이미지 빌드 완료"
echo ""

# 서비스 시작
echo "🚀 서비스 시작 중..."
docker compose up -d backend frontend ollama
echo "✅ 서비스 시작 완료"
echo ""

# 서비스 상태 확인
echo "📊 서비스 상태 확인 중..."
sleep 3
docker compose ps
echo ""

# 접속 정보 출력
echo "🌐 접속 정보:"
echo "   - 프론트엔드: http://localhost:15173"
echo "   - 백엔드 API: http://localhost:18000"
echo "   - API 문서: http://localhost:18000/docs"
echo "   - Ollama: http://localhost:11434"
echo ""

# 로그 확인 안내
echo "📝 로그 확인:"
echo "   docker compose logs -f backend    # 백엔드 로그"
echo "   docker compose logs -f frontend  # 프론트엔드 로그"
echo ""

echo "✨ 배포 완료!"

