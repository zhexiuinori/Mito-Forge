#!/bin/bash

# Mito-Forge Linux 快速安装脚本
# 专为生物信息学环境设计

set -e

echo "🧬 Mito-Forge Linux 安装"
echo "======================="

# 检测系统
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "✓ Linux系统检测通过"
else
    echo "❌ 此脚本仅支持Linux系统"
    exit 1
fi

# 检查Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    echo "✓ Python版本: $PYTHON_VERSION"
else
    echo "❌ 需要Python 3.8+"
    exit 1
fi

# 创建虚拟环境
echo "📦 创建Python虚拟环境..."
python3 -m venv ~/.mito-forge-env
source ~/.mito-forge-env/bin/activate

# 安装依赖
echo "📥 安装Python依赖..."
pip install --upgrade pip
pip install click rich loguru typer psutil biopython

# 创建启动脚本
echo "🔧 创建启动脚本..."
cat > ~/.local/bin/mito-forge << 'EOF'
#!/bin/bash
source ~/.mito-forge-env/bin/activate
python $(dirname $(readlink -f $0))/../../../demo_cli.py "$@"
EOF

chmod +x ~/.local/bin/mito-forge
mkdir -p ~/.local/bin

# 添加到PATH
if ! grep -q "/.local/bin" ~/.bashrc; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
fi

echo "✅ Mito-Forge安装完成！"
echo ""
echo "使用方法:"
echo "  source ~/.bashrc"
echo "  mito-forge --help"
echo ""
echo "或者直接运行:"
echo "  python demo_cli.py --help"