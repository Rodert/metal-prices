# 贵金属价格数据服务

Python Flask 服务，用于接收、存储和查询贵金属价格数据。

## 功能特性

- ✅ 接收采集器发送的价格数据
- ✅ SQLite 数据库存储
- ✅ 最新价格表 + 历史记录表
- ✅ RESTful API 查询接口
- ✅ 数据来源标记
- ✅ 统计信息查询
- ✅ systemd 服务管理

## 数据库结构

### 1. 最新价格表 (latest_prices)

存储每个产品的最新价格，自动更新。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| product_code | TEXT | 产品代码（唯一） |
| product_name | TEXT | 产品名称 |
| current_price | REAL | 当前价格 |
| current_time | TEXT | 价格时间点 |
| min_price | REAL | 最低价 |
| max_price | REAL | 最高价 |
| data_timestamp | TEXT | 数据源时间戳 |
| source | TEXT | 数据来源 |
| updated_at | TEXT | 更新时间 |

### 2. 历史记录表 (price_history)

存储所有历史价格记录，只增不改。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| product_code | TEXT | 产品代码 |
| product_name | TEXT | 产品名称 |
| current_price | REAL | 当前价格 |
| current_time | TEXT | 价格时间点 |
| min_price | REAL | 最低价 |
| max_price | REAL | 最高价 |
| data_timestamp | TEXT | 数据源时间戳 |
| collect_timestamp | TEXT | 采集时间戳 |
| source | TEXT | 数据来源 |
| created_at | TEXT | 记录创建时间 |

## API 接口

### 1. 健康检查

```bash
GET /health
```

**响应示例:**
```json
{
  "status": "ok",
  "timestamp": "2025-11-11 14:30:00"
}
```

### 2. 接收价格数据

```bash
POST /api/prices
Content-Type: application/json
```

**请求体:**
```json
{
  "prices": [
    {
      "product_code": "Au99.99",
      "product_name": "黄金99.99",
      "current_price": 949.0,
      "current_time": "11:06",
      "min_price": 934.0,
      "max_price": 950.0,
      "data_timestamp": "2025年11月11日 11:06:59",
      "collect_timestamp": "2025-11-11 11:08:03"
    }
  ],
  "collect_time": "2025-11-11 11:08:03",
  "source": "SGE"
}
```

**响应示例:**
```json
{
  "success": true,
  "message": "数据保存成功",
  "result": {
    "success": 5,
    "failed": 0,
    "total": 5
  }
}
```

### 3. 获取最新价格

```bash
# 获取所有产品最新价格
GET /api/prices/latest

# 获取指定产品最新价格
GET /api/prices/latest?product_code=Au99.99
```

**响应示例:**
```json
{
  "success": true,
  "count": 1,
  "data": [
    {
      "id": 1,
      "product_code": "Au99.99",
      "product_name": "黄金99.99",
      "current_price": 949.0,
      "current_time": "11:06",
      "min_price": 934.0,
      "max_price": 950.0,
      "data_timestamp": "2025年11月11日 11:06:59",
      "source": "SGE",
      "updated_at": "2025-11-11 11:08:03"
    }
  ]
}
```

### 4. 获取历史价格

```bash
# 获取所有历史记录（最近100条）
GET /api/prices/history

# 获取指定产品历史
GET /api/prices/history?product_code=Au99.99

# 指定时间范围
GET /api/prices/history?start_time=2025-11-11 00:00:00&end_time=2025-11-11 23:59:59

# 指定返回数量
GET /api/prices/history?product_code=Au99.99&limit=50
```

**响应示例:**
```json
{
  "success": true,
  "count": 10,
  "data": [
    {
      "id": 1,
      "product_code": "Au99.99",
      "product_name": "黄金99.99",
      "current_price": 949.0,
      "current_time": "11:06",
      "min_price": 934.0,
      "max_price": 950.0,
      "data_timestamp": "2025年11月11日 11:06:59",
      "collect_timestamp": "2025-11-11 11:08:03",
      "source": "SGE",
      "created_at": "2025-11-11 11:08:03"
    }
  ]
}
```

### 5. 获取统计信息

```bash
GET /api/statistics
```

**响应示例:**
```json
{
  "success": true,
  "data": {
    "total_products": 16,
    "total_history_records": 1280,
    "last_update": "2025-11-11 14:30:00",
    "product_statistics": [
      {
        "product_code": "Au99.99",
        "product_name": "黄金99.99",
        "count": 120
      }
    ]
  }
}
```

## 部署指南

### 方式一：自动部署（推荐）

1. **上传文件到服务器**
```bash
scp server.py server-requirements.txt metal-prices.service deploy.sh user@your-server:/tmp/
```

2. **运行部署脚本**
```bash
ssh user@your-server
cd /tmp
chmod +x deploy.sh
sudo ./deploy.sh
```

3. **验证服务**
```bash
curl http://localhost:5000/health
```

### 方式二：手动部署

1. **安装依赖**
```bash
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv sqlite3
```

2. **创建目录**
```bash
sudo mkdir -p /opt/metal-prices/data
cd /opt/metal-prices
```

3. **创建虚拟环境**
```bash
python3 -m venv venv
source venv/bin/activate
```

4. **安装Python包**
```bash
pip install Flask gunicorn
```

5. **复制服务文件**
```bash
# 将 server.py 复制到 /opt/metal-prices/
```

6. **配置systemd服务**
```bash
sudo cp metal-prices.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable metal-prices
sudo systemctl start metal-prices
```

## 配置说明

### 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| DATABASE_PATH | metal_prices.db | 数据库文件路径 |
| HOST | 0.0.0.0 | 监听地址 |
| PORT | 5000 | 监听端口 |

### 修改配置

编辑 `/etc/systemd/system/metal-prices.service`:

```ini
Environment="DATABASE_PATH=/opt/metal-prices/data/metal_prices.db"
Environment="HOST=0.0.0.0"
Environment="PORT=5000"
```

重启服务:
```bash
sudo systemctl daemon-reload
sudo systemctl restart metal-prices
```

## 服务管理

```bash
# 查看状态
sudo systemctl status metal-prices

# 启动服务
sudo systemctl start metal-prices

# 停止服务
sudo systemctl stop metal-prices

# 重启服务
sudo systemctl restart metal-prices

# 查看日志
sudo journalctl -u metal-prices -f

# 查看最近100行日志
sudo journalctl -u metal-prices -n 100
```

## 配置采集器

修改采集器的目标API地址为服务器地址：

### GitHub Actions 配置

在 GitHub Secrets 中设置:
```
TARGET_API_URL=http://your-server-ip:5000/api/prices
```

### 本地测试

```bash
export TARGET_API_URL="http://your-server-ip:5000/api/prices"
python collector.py
```

## 数据库管理

### 备份数据库

```bash
sqlite3 /opt/metal-prices/data/metal_prices.db .dump > backup.sql
```

### 恢复数据库

```bash
sqlite3 /opt/metal-prices/data/metal_prices.db < backup.sql
```

### 查看数据库

```bash
sqlite3 /opt/metal-prices/data/metal_prices.db

# 查看表结构
.schema

# 查看最新价格
SELECT * FROM latest_prices;

# 查看历史记录
SELECT * FROM price_history ORDER BY created_at DESC LIMIT 10;

# 退出
.quit
```

## 性能优化

### 1. 使用 Nginx 反向代理

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 2. 增加 Gunicorn 工作进程

编辑 `metal-prices.service`:
```ini
ExecStart=/opt/metal-prices/venv/bin/gunicorn -w 8 -b 0.0.0.0:5000 server:app
```

### 3. 定期清理历史数据

```bash
# 删除30天前的历史记录
sqlite3 /opt/metal-prices/data/metal_prices.db "DELETE FROM price_history WHERE created_at < datetime('now', '-30 days');"
```

## 故障排查

### 服务无法启动

```bash
# 查看详细日志
sudo journalctl -u metal-prices -n 50 --no-pager

# 检查端口占用
sudo netstat -tlnp | grep 5000

# 检查文件权限
ls -la /opt/metal-prices/
```

### 数据库锁定

```bash
# 检查数据库文件权限
ls -la /opt/metal-prices/data/metal_prices.db

# 修复权限
sudo chown www-data:www-data /opt/metal-prices/data/metal_prices.db
```

### API 无响应

```bash
# 测试本地连接
curl http://localhost:5000/health

# 测试外部连接
curl http://your-server-ip:5000/health

# 检查防火墙
sudo ufw status
sudo ufw allow 5000/tcp
```

## 安全建议

1. **使用 HTTPS**
   - 配置 Nginx + Let's Encrypt SSL证书

2. **添加认证**
   - 使用 API Key 或 JWT 认证

3. **限制访问**
   - 配置防火墙规则
   - 使用 IP 白名单

4. **定期备份**
   - 设置定时任务备份数据库

## 监控

### 添加监控脚本

```bash
#!/bin/bash
# /opt/metal-prices/monitor.sh

if ! systemctl is-active --quiet metal-prices; then
    echo "服务已停止，正在重启..."
    systemctl start metal-prices
    # 发送告警通知
fi
```

### 定时任务

```bash
# 每5分钟检查一次
crontab -e
*/5 * * * * /opt/metal-prices/monitor.sh
```

## 许可证

MIT License
