#!/bin/bash

# Forum后端测试执行脚本
# 用于运行所有测试或指定类型的测试

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# 显示帮助
show_help() {
    echo -e "${BLUE}Forum后端测试执行脚本${NC}"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help       显示此帮助信息"
    echo "  --api            只运行API测试"
    echo "  --unit           只运行单元测试"
    echo "  --integration    只运行集成测试"
    echo "  --all            运行所有测试 (默认)"
    echo ""
    echo "示例:"
    echo "  $0 --api         # 只运行API测试"
    echo "  $0 --all         # 运行所有测试"
    echo ""
}

# 默认配置
RUN_API=true
RUN_UNIT=true
RUN_INTEGRATION=true

# 参数解析
if [ $# -gt 0 ]; then
    RUN_API=false
    RUN_UNIT=false
    RUN_INTEGRATION=false
    
    while [[ $# -gt 0 ]]; do
      case $1 in
        -h|--help)
          show_help
          exit 0
          ;;
        --api)
          RUN_API=true
          shift
          ;;
        --unit)
          RUN_UNIT=true
          shift
          ;;
        --integration)
          RUN_INTEGRATION=true
          shift
          ;;
        --all)
          RUN_API=true
          RUN_UNIT=true
          RUN_INTEGRATION=true
          shift
          ;;
        *)
          echo -e "${RED}未知选项: $1${NC}"
          show_help
          exit 1
          ;;
      esac
    done
fi

# 运行API测试
run_api_tests() {
    echo -e "\n${BLUE}===============================================${NC}"
    echo -e "${BLUE}     API测试${NC}"
    echo -e "${BLUE}===============================================${NC}"
    
    # 运行帖子API测试
    cd "${SCRIPT_DIR}/tests/api"
    ./run_posts_tests.sh
    API_EXIT_CODE=$?
    
    if [ $API_EXIT_CODE -eq 0 ]; then
        echo -e "\n${GREEN}API测试通过${NC}"
    else
        echo -e "\n${RED}API测试失败${NC}"
    fi
    
    return $API_EXIT_CODE
}

# 运行单元测试
run_unit_tests() {
    echo -e "\n${BLUE}===============================================${NC}"
    echo -e "${BLUE}     单元测试${NC}"
    echo -e "${BLUE}===============================================${NC}"
    
    cd "${SCRIPT_DIR}"
    
    # 如果有pytest配置，使用pytest运行
    if [ -f "pytest.ini" ]; then
        python -m pytest tests/unit
    else
        echo -e "${YELLOW}未找到单元测试配置，跳过${NC}"
    fi
    
    UNIT_EXIT_CODE=$?
    
    if [ $UNIT_EXIT_CODE -eq 0 ]; then
        echo -e "\n${GREEN}单元测试通过${NC}"
    else
        echo -e "\n${RED}单元测试失败${NC}"
    fi
    
    return $UNIT_EXIT_CODE
}

# 运行集成测试
run_integration_tests() {
    echo -e "\n${BLUE}===============================================${NC}"
    echo -e "${BLUE}     集成测试${NC}"
    echo -e "${BLUE}===============================================${NC}"
    
    cd "${SCRIPT_DIR}"
    
    # 如果有集成测试配置，使用pytest运行
    if [ -d "tests/integration" ]; then
        python -m pytest tests/integration
    else
        echo -e "${YELLOW}未找到集成测试，跳过${NC}"
    fi
    
    INTEGRATION_EXIT_CODE=$?
    
    if [ $INTEGRATION_EXIT_CODE -eq 0 ]; then
        echo -e "\n${GREEN}集成测试通过${NC}"
    else
        echo -e "\n${RED}集成测试失败${NC}"
    fi
    
    return $INTEGRATION_EXIT_CODE
}

# 主函数
main() {
    echo -e "${BLUE}===============================================${NC}"
    echo -e "${BLUE}       Forum后端测试套件 v1.0${NC}"
    echo -e "${BLUE}===============================================${NC}"
    
    TOTAL_EXIT_CODE=0
    
    # 运行选定的测试
    if [ "$RUN_API" = true ]; then
        run_api_tests
        TOTAL_EXIT_CODE=$((TOTAL_EXIT_CODE + $?))
    fi
    
    if [ "$RUN_UNIT" = true ]; then
        run_unit_tests
        TOTAL_EXIT_CODE=$((TOTAL_EXIT_CODE + $?))
    fi
    
    if [ "$RUN_INTEGRATION" = true ]; then
        run_integration_tests
        TOTAL_EXIT_CODE=$((TOTAL_EXIT_CODE + $?))
    fi
    
    echo -e "\n${BLUE}===============================================${NC}"
    if [ $TOTAL_EXIT_CODE -eq 0 ]; then
        echo -e "${GREEN}所有测试通过!${NC}"
    else
        echo -e "${RED}测试过程中出现错误!${NC}"
    fi
    echo -e "${BLUE}===============================================${NC}"
    
    exit $TOTAL_EXIT_CODE
}

# 执行主函数
main 