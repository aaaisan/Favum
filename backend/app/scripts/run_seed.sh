#!/bin/bash

# 导航到脚本所在目录
cd "$(dirname "$0")"

# 设置Python环境变量（如果需要）
export PYTHONPATH=$PYTHONPATH:../../

echo "准备执行数据库种子脚本..."

# 运行Python脚本
# 如果使用Python虚拟环境，请取消下面注释并修改路径
# source /path/to/your/venv/bin/activate
python3 custom_seed_data.py "$@"

echo "脚本执行完成！" 