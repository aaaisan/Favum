#!/bin/bash

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}===== 论坛系统启动脚本 =====${NC}"

# 检查 Redis 是否运行
echo -e "${YELLOW}检查 Redis 服务...${NC}"
if ! pgrep -x "redis-server" > /dev/null; then
    echo -e "${RED}Redis 服务未运行，正在尝试启动...${NC}"
    if command -v brew &> /dev/null; then
        brew services start redis
    else
        echo -e "${RED}无法自动启动 Redis，请手动启动 Redis 服务${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}Redis 服务正在运行${NC}"
fi

# 启动后端服务
echo -e "${YELLOW}启动后端服务...${NC}"
cd backend
# 检查是否有虚拟环境
if [ -d "venv" ]; then
    echo -e "${GREEN}使用虚拟环境${NC}"
    source venv/bin/activate
fi

# 启动后端服务
python run.py &
BACKEND_PID=$!
echo -e "${GREEN}后端服务已启动，PID: $BACKEND_PID${NC}"

# 返回到项目根目录
cd ..

# 启动前端服务
echo -e "${YELLOW}启动前端服务...${NC}"
cd frontend
npm run dev &
FRONTEND_PID=$!
echo -e "${GREEN}前端服务已启动，PID: $FRONTEND_PID${NC}"

# 返回到项目根目录
cd ..

echo -e "${GREEN}===== 所有服务已启动 =====${NC}"
echo -e "${YELLOW}前端地址: http://localhost:8080${NC}"
echo -e "${YELLOW}后端地址: http://127.0.0.1:8000${NC}"
echo -e "${YELLOW}API文档: http://127.0.0.1:8000/api/v1/docs${NC}"
echo -e "${YELLOW}按 Ctrl+C 停止所有服务${NC}"

# 捕获 SIGINT 信号（Ctrl+C）
trap "echo -e '${RED}正在停止服务...${NC}'; kill $BACKEND_PID $FRONTEND_PID; exit" INT

# 等待子进程
wait 