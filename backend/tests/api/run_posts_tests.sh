#!/bin/bash

# 帖子API测试执行脚本
# 用于简化测试执行过程

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# 默认配置
TOKEN=""
ADMIN_TOKEN=""
TEST_HOST="localhost:8000"
RUN_NORMAL=true
RUN_EDGE=true
AUTO_AUTH=true
USERNAME="admin"
PASSWORD="admin123"
TEST_TOKEN=""
CAPTCHA_ID="test123"
CAPTCHA_CODE="test123"
SECTION_ID="15"
CATEGORY_ID="35"
AUTHOR_ID="46"

# 显示帮助
show_help() {
    echo -e "${BLUE}帖子API端点测试工具 v1.1${NC}"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help             显示此帮助信息"
    echo "  -t, --token TOKEN      设置用户访问令牌"
    echo "  -a, --admin TOKEN      设置管理员访问令牌"
    echo "  --host HOST            设置API主机地址 (默认: localhost:8000)"
    echo "  --normal-only          只运行标准功能测试"
    echo "  --edge-only            只运行边缘情况测试"
    echo "  --no-auto-auth         禁用自动认证 (默认启用)"
    echo "  --username USERNAME    设置登录用户名 (默认: admin)"
    echo "  --password PASSWORD    设置登录密码 (默认: admin123)"
    echo "  --test-token TOKEN     直接使用此测试令牌，跳过认证过程"
    echo "  --captcha-id ID        设置验证码ID (默认: test123)"
    echo "  --captcha-code CODE    设置验证码代码 (默认: test123)"
    echo "  --section-id ID        设置测试使用的版块ID (默认: 1)"
    echo "  --category-id ID       设置测试使用的分类ID (默认: 1)"
    echo "  --author-id ID         设置测试使用的作者ID (默认: 1)"
    echo ""
    echo "示例:"
    echo "  $0 --token \"eyJhbGciOiJIUzI1NiIsIn...\" --host api.example.com"
    echo "  $0 --username \"testuser\" --password \"testpass123\""
    echo "  $0 --test-token \"your-test-token\""
    echo "  $0 --captcha-id \"your-captcha-id\""
    echo "  $0 --section-id 2 --category-id 3 --author-id 1"
    echo ""
}

# 参数解析
while [[ $# -gt 0 ]]; do
  case $1 in
    -h|--help)
      show_help
      exit 0
      ;;
    -t|--token)
      TOKEN="$2"
      shift 2
      ;;
    -a|--admin)
      ADMIN_TOKEN="$2"
      shift 2
      ;;
    --host)
      TEST_HOST="$2"
      shift 2
      ;;
    --normal-only)
      RUN_EDGE=false
      shift
      ;;
    --edge-only)
      RUN_NORMAL=false
      shift
      ;;
    --no-auto-auth)
      AUTO_AUTH=false
      shift
      ;;
    --username)
      USERNAME="$2"
      shift 2
      ;;
    --password)
      PASSWORD="$2"
      shift 2
      ;;
    --test-token)
      TEST_TOKEN="$2"
      shift 2
      ;;
    --captcha-id)
      CAPTCHA_ID="$2"
      shift 2
      ;;
    --captcha-code)
      CAPTCHA_CODE="$2"
      shift 2
      ;;
    --section-id)
      SECTION_ID="$2"
      shift 2
      ;;
    --category-id)
      CATEGORY_ID="$2"
      shift 2
      ;;
    --author-id)
      AUTHOR_ID="$2"
      shift 2
      ;;
    *)
      echo -e "${RED}未知选项: $1${NC}"
      show_help
      exit 1
      ;;
  esac
done

# 检查Python和依赖
check_dependencies() {
    echo -e "${BLUE}检查依赖...${NC}"
    
    # 检查Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}错误: 未找到Python 3${NC}"
        echo "请安装Python 3后再运行此脚本"
        exit 1
    fi
    
    # 检查requests库
    if ! python3 -c "import requests" &> /dev/null; then
        echo -e "${YELLOW}警告: 未安装requests库${NC}"
        read -p "是否立即安装? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            python3 -m pip install requests
            if [ $? -ne 0 ]; then
                echo -e "${RED}安装失败${NC}"
                exit 1
            fi
        else
            echo -e "${RED}requests库是必需的，无法继续${NC}"
            exit 1
        fi
    fi
    
    echo -e "${GREEN}所有依赖已满足${NC}"
}

# 检查API服务是否可用
check_api() {
    echo -e "${BLUE}检查API服务可用性...${NC}"
    
    # 尝试连接API
    if ! curl -s -o /dev/null "http://${TEST_HOST}/api/v1/health-check" 2> /dev/null; then
        echo -e "${YELLOW}警告: 无法连接到API服务 (http://${TEST_HOST})${NC}"
        echo -e "请确保API服务正在运行"
        read -p "是否继续测试? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        echo -e "${GREEN}API服务可用${NC}"
    fi
}

# 询问令牌
ask_for_token() {
    if [ -z "$TOKEN" ]; then
        if [ "$AUTO_AUTH" = true ]; then
            echo -e "${BLUE}自动认证已启用，将使用以下凭据:${NC}"
            echo -e "用户名: ${YELLOW}${USERNAME}${NC}"
            echo -e "密码: ${YELLOW}******${NC}"
        else
            echo -e "${YELLOW}未提供访问令牌${NC}"
            read -p "请输入访问令牌 (回车跳过): " TOKEN
        fi
    fi
}

# 获取访问令牌
get_token() {
    if [ "$AUTO_AUTH" = true ] && [ -z "$TOKEN" ]; then
        echo -e "${BLUE}尝试获取访问令牌...${NC}"
        
        # 使用独立的认证测试脚本获取令牌
        cd $(dirname "$0")  # 确保在脚本所在目录执行
        chmod +x test_auth.py
        
        # 构建测试脚本参数
        AUTH_CMD="./test_auth.py --username \"$USERNAME\" --password \"$PASSWORD\" --host \"$TEST_HOST\""
        
        # 如果设置了测试令牌，则传递它
        if [ ! -z "$TEST_TOKEN" ]; then
            AUTH_CMD="$AUTH_CMD --test-token \"$TEST_TOKEN\""
        fi
        
        # 如果设置了验证码ID，则传递它
        if [ ! -z "$CAPTCHA_ID" ]; then
            AUTH_CMD="$AUTH_CMD --captcha-id \"$CAPTCHA_ID\" --captcha-code \"$CAPTCHA_CODE\""
        fi
        
        # 执行认证测试脚本
        CREDS_RESULT=$(eval $AUTH_CMD)
        
        # 从输出中提取token
        TOKEN=$(echo "$CREDS_RESULT" | grep "成功获取令牌" | grep -o '[^:]*$' | tr -d ' .' | sed 's/^.*\(..........\).*$/\1/')
        
        if [ ! -z "$TOKEN" ]; then
            echo -e "${GREEN}成功获取访问令牌${NC}"
        else
            echo -e "${RED}自动获取令牌失败${NC}"
            echo -e "详细信息: $CREDS_RESULT"
            echo -e "如果看到验证码错误，请尝试以下命令获取有效的验证码ID："
            echo -e "${YELLOW}curl -s http://$TEST_HOST/api/v1/captcha | jq${NC}"
            echo -e "然后使用 --captcha-id 参数提供验证码ID"
            read -p "是否手动输入令牌? (y/n) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                read -p "请输入访问令牌: " TOKEN
            fi
        fi
    fi
}

# 运行测试
run_tests() {
    # 设置环境变量
    export API_HOST="${TEST_HOST}"
    export TOKEN
    export ADMIN_TOKEN
    
    # 设置环境变量控制自动认证
    if [ "$AUTO_AUTH" = false ]; then
        export AUTO_AUTH=0
    else
        export AUTO_AUTH=1
    fi
    
    export TEST_SECTION_ID="${SECTION_ID}"
    export TEST_CATEGORY_ID="${CATEGORY_ID}"
    export TEST_AUTHOR_ID="${AUTHOR_ID}"
    
    if [ "$RUN_NORMAL" = true ]; then
        echo -e "\n${BLUE}===============================================${NC}"
        echo -e "${BLUE}开始运行标准功能测试${NC}"
        echo -e "${BLUE}===============================================${NC}"
        
        # 运行标准测试
        python3 test_posts_endpoints.py
        NORMAL_EXIT_CODE=$?
    fi
    
    if [ "$RUN_EDGE" = true ]; then
        echo -e "\n${BLUE}===============================================${NC}"
        echo -e "${BLUE}开始运行边缘情况测试${NC}"
        echo -e "${BLUE}===============================================${NC}"
        
        # 运行边缘情况测试
        python3 test_posts_edge_cases.py
        EDGE_EXIT_CODE=$?
    fi
    
    echo -e "\n${BLUE}===============================================${NC}"
    echo -e "${BLUE}               测试完成${NC}"
    echo -e "${BLUE}===============================================${NC}"
    
    if [ "$RUN_NORMAL" = true ]; then
        if [ $NORMAL_EXIT_CODE -eq 0 ]; then
            echo -e "${GREEN}标准功能测试通过${NC}"
        else
            echo -e "${RED}标准功能测试失败${NC}"
        fi
    fi
    
    if [ "$RUN_EDGE" = true ]; then
        if [ $EDGE_EXIT_CODE -eq 0 ]; then
            echo -e "${GREEN}边缘情况测试通过${NC}"
        else
            echo -e "${RED}边缘情况测试失败${NC}"
        fi
    fi
}

# 主函数
main() {
    echo -e "${BLUE}===============================================${NC}"
    echo -e "${BLUE}       帖子API端点测试工具 v1.1${NC}"
    echo -e "${BLUE}===============================================${NC}"
    
    # 检查依赖
    check_dependencies
    
    # 检查API服务
    check_api
    
    # 询问令牌
    ask_for_token
    
    # 获取令牌
    get_token
    
    # 运行测试
    run_tests
}

# 执行主函数
main 