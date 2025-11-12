# 服务端文件清单

## 📦 文件列表

### 核心文件

| 文件名 | 大小 | 说明 |
|--------|------|------|
| **server.py** | ~17KB | Flask API服务主文件，包含所有接口和数据库逻辑 |
| **requirements.txt** | ~30B | Python依赖包列表（Flask, gunicorn） |
| **metal-prices.service** | ~450B | systemd服务配置文件 |
| **deploy.sh** | ~1.8KB | Linux自动化部署脚本 |

### 文档文件

| 文件名 | 大小 | 说明 |
|--------|------|------|
| **README.md** | ~8.6KB | 完整的部署和使用文档 |
| **DATABASE_SCHEMA.md** | ~9.6KB | 数据库表结构和字段说明 |

---

## 🚀 快速开始

### 1. 部署到Linux服务器

```bash
# 上传文件到服务器
scp -r server/* user@your-server:/tmp/metal-prices/

# SSH登录服务器
ssh user@your-server

# 运行部署脚本
cd /tmp/metal-prices
chmod +x deploy.sh
sudo ./deploy.sh
```

### 2. 手动部署

```bash
# 安装依赖
sudo apt-get install python3 python3-pip python3-venv

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装Python包
pip install -r requirements.txt

# 运行服务
python server.py
```

---

## 📋 文件说明

### server.py
主服务文件，包含：
- Flask应用初始化
- SQLite数据库管理
- 5个API接口（接收数据、查询最新价格、查询历史、统计信息、健康检查）
- 数据库表结构定义
- 自动时间戳触发器

**主要功能**:
- 接收采集器发送的价格数据
- 存储到SQLite数据库（2张表）
- 提供RESTful API查询接口
- 自动管理时间字段（created_at, updated_at, deleted_at）

### requirements.txt
Python依赖包：
```
Flask>=3.0.0
gunicorn>=21.2.0
```

### metal-prices.service
systemd服务配置，用于：
- 开机自启动
- 进程管理
- 日志记录
- 自动重启

### deploy.sh
自动化部署脚本，执行：
1. 安装系统依赖
2. 创建安装目录
3. 配置虚拟环境
4. 安装Python包
5. 设置文件权限
6. 注册systemd服务
7. 启动服务

### README.md
完整文档，包含：
- 功能特性
- 数据库结构
- API接口文档
- 部署指南
- 配置说明
- 服务管理
- 故障排查

### DATABASE_SCHEMA.md
数据库文档，包含：
- 表结构详情
- 字段说明
- 时间字段用法
- SQL查询示例
- 触发器说明
- 软删除用法

---

## 🔗 相关文件

### 采集器文件（在上级目录）
- `collector.py` - 数据采集脚本
- `requirements.txt` - 采集器依赖
- `.github/workflows/collect-prices.yml` - GitHub Actions定时任务

### 配置文件
- 采集器通过环境变量 `TARGET_API_URL` 指定服务器地址
- 服务器通过环境变量配置数据库路径、监听地址和端口

---

## 📊 数据库

### 表结构
1. **latest_prices** - 最新价格表（16条记录）
2. **price_history** - 历史记录表（持续增长）

### 时间字段
- **created_at** - 创建时间（数据库自动设置）
- **updated_at** - 更新时间（触发器自动更新）
- **deleted_at** - 删除时间（软删除标记）

---

## 🌐 API接口

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 健康检查 | GET | `/health` | 检查服务状态 |
| 接收数据 | POST | `/api/prices` | 接收采集器数据 |
| 最新价格 | GET | `/api/prices/latest` | 查询最新价格 |
| 历史记录 | GET | `/api/prices/history` | 查询历史价格 |
| 统计信息 | GET | `/api/statistics` | 查询统计数据 |

---

## 📝 版本信息

- **版本**: 1.0.0
- **Python**: 3.8+
- **数据库**: SQLite 3
- **Web框架**: Flask 3.0+
- **WSGI服务器**: Gunicorn 21.2+

---

## 📄 许可证

MIT License
