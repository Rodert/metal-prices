#!/bin/bash
# 部署脚本 - 在Linux服务器上运行

set -e

echo "=== 贵金属价格服务部署脚本 ==="

# 配置
INSTALL_DIR="/opt/metal-prices"
DATA_DIR="$INSTALL_DIR/data"
SERVICE_NAME="metal-prices"

# 检查是否为root用户
if [ "$EUID" -ne 0 ]; then 
    echo "请使用 sudo 运行此脚本"
    exit 1
fi

# 1. 安装系统依赖
echo "1. 安装系统依赖..."
apt-get update
apt-get install -y python3 python3-pip python3-venv sqlite3

# 2. 创建安装目录
echo "2. 创建安装目录..."
mkdir -p $INSTALL_DIR
mkdir -p $DATA_DIR

# 3. 复制文件
echo "3. 复制服务文件..."
cp server.py $INSTALL_DIR/
cp server-requirements.txt $INSTALL_DIR/requirements.txt

# 4. 创建虚拟环境
echo "4. 创建Python虚拟环境..."
cd $INSTALL_DIR
python3 -m venv venv
source venv/bin/activate

# 5. 安装Python依赖
echo "5. 安装Python依赖..."
pip install --upgrade pip
pip install -r requirements.txt

# 6. 设置权限
echo "6. 设置文件权限..."
chown -R www-data:www-data $INSTALL_DIR
chmod -R 755 $INSTALL_DIR
chmod -R 775 $DATA_DIR

# 7. 安装systemd服务
echo "7. 安装systemd服务..."
cp metal-prices.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable $SERVICE_NAME
systemctl start $SERVICE_NAME

# 8. 检查服务状态
echo "8. 检查服务状态..."
sleep 2
systemctl status $SERVICE_NAME --no-pager

echo ""
echo "=== 部署完成 ==="
echo "服务地址: http://localhost:5000"
echo "数据库路径: $DATA_DIR/metal_prices.db"
echo ""
echo "常用命令:"
echo "  查看状态: sudo systemctl status $SERVICE_NAME"
echo "  启动服务: sudo systemctl start $SERVICE_NAME"
echo "  停止服务: sudo systemctl stop $SERVICE_NAME"
echo "  重启服务: sudo systemctl restart $SERVICE_NAME"
echo "  查看日志: sudo journalctl -u $SERVICE_NAME -f"
