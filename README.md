# 贵金属价格采集器

自动从上海黄金交易所（SGE）采集贵金属价格数据，并发送到指定接口。支持通过 GitHub Actions 定时执行。

## 功能特性

- ✅ 自动采集上海黄金交易所实时价格数据
- ✅ 支持多种贵金属产品（黄金、白银、铂金等）
- ✅ 通过 GitHub Actions 定时执行（每小时一次）
- ✅ 自动发送数据到指定API接口
- ✅ 完整的日志记录和错误处理
- ✅ 支持手动触发执行

## 支持的产品

| 产品代码 | 产品名称 |
|---------|---------|
| Au99.99 | 黄金99.99 |
| Au99.95 | 黄金99.95 |
| Au100g | 100克金条 |
| Ag99.99 | 白银99.99 |
| Pt99.95 | 铂金99.95 |
| Au(T+D) | 黄金延期交收 |
| Ag(T+D) | 白银延期交收 |
| iAu99.99 | 国际板黄金99.99 |
| PGC30g | 铂金金条30克 |
| ... | 更多产品见 `collector.py` |

## 快速开始

### 1. 本地测试

```bash
# 克隆仓库
git clone https://github.com/your-username/metal-prices.git
cd metal-prices

# 安装依赖
pip install -r requirements.txt

# 设置环境变量（可选）
export TARGET_API_URL="https://your-api-endpoint.com/api/prices"
export PRODUCTS="Au99.99,Au99.95,Ag99.99"

# 运行采集脚本
python collector.py
```

### 2. GitHub Actions 配置

#### 步骤 1: 配置 Secrets

在 GitHub 仓库中设置以下 Secrets：

1. 进入仓库的 `Settings` → `Secrets and variables` → `Actions`
2. 点击 `New repository secret`
3. 添加以下 Secret：
   - **Name**: `TARGET_API_URL`
   - **Value**: 你的接口地址，例如 `https://your-api.com/api/prices`

#### 步骤 2: 启用 GitHub Actions

1. 进入仓库的 `Actions` 标签页
2. 如果 Actions 未启用，点击启用
3. 工作流会自动按照定时任务执行

#### 步骤 3: 手动触发（可选）

1. 进入 `Actions` 标签页
2. 选择 `Collect Metal Prices` 工作流
3. 点击 `Run workflow`
4. 可以自定义要采集的产品代码（逗号分隔）

## 配置说明

### 环境变量

| 变量名 | 说明 | 必填 | 默认值 |
|-------|------|------|--------|
| `TARGET_API_URL` | 目标API接口地址 | 否 | 无（不发送数据，仅打印） |
| `PRODUCTS` | 要采集的产品代码（逗号分隔） | 否 | Au99.99,Au99.95,Au100g,Ag99.99,Pt99.95 |

### 定时任务配置

在 `.github/workflows/collect-prices.yml` 中修改 cron 表达式：

```yaml
schedule:
  - cron: '0 * * * *'  # 每小时执行一次
```

常用 cron 表达式示例：
- `0 * * * *` - 每小时执行一次
- `0 */2 * * *` - 每2小时执行一次
- `0 9-17 * * *` - 每天9点到17点，每小时执行一次
- `0 0 * * *` - 每天0点执行一次

## 数据格式

### 发送到目标API的数据格式

```json
{
  "prices": [
    {
      "product_code": "Au99.99",
      "product_name": "黄金99.99",
      "current_time": "10:15",
      "current_price": 530.67,
      "min_price": 528.5,
      "max_price": 532.8,
      "data_timestamp": "2025年11月11日 10:15:52",
      "collect_timestamp": "2025-11-11 10:16:00"
    }
  ],
  "collect_time": "2025-11-11 10:16:00",
  "source": "SGE"
}
```

### 字段说明

- `product_code`: 产品代码
- `product_name`: 产品中文名称
- `current_time`: 当前价格对应的时间点
- `current_price`: 当前价格（元/克）
- `min_price`: 当日最低价
- `max_price`: 当日最高价
- `data_timestamp`: 数据源时间戳
- `collect_timestamp`: 采集时间戳
- `source`: 数据来源（SGE = 上海黄金交易所）

## 目录结构

```
metal-prices/
├── .github/
│   └── workflows/
│       └── collect-prices.yml    # GitHub Actions 工作流配置
├── collector.py                   # 主采集脚本
├── requirements.txt               # Python 依赖
├── config.example.json            # 配置文件示例
├── curl.md                        # API 文档和示例
├── .gitignore                     # Git 忽略文件
└── README.md                      # 项目说明文档
```

## 日志说明

脚本会输出详细的日志信息：

```
2025-11-11 10:16:00 - INFO - 开始采集任务，共 5 个产品
2025-11-11 10:16:01 - INFO - 正在获取 Au99.99 (黄金99.99) 的数据...
2025-11-11 10:16:02 - INFO - 成功获取 Au99.99 的数据
2025-11-11 10:16:02 - INFO - Au99.99 当前价格: 530.67 (时间: 10:15)
2025-11-11 10:16:03 - INFO - 正在发送数据到 https://your-api.com/api/prices...
2025-11-11 10:16:04 - INFO - 数据发送成功: 200
2025-11-11 10:16:04 - INFO - 采集完成: 成功 5 个，失败 0 个
```

## 故障排查

### 1. 采集失败

**可能原因**：
- 网络连接问题
- 上海黄金交易所API暂时不可用
- 产品代码错误

**解决方法**：
- 检查网络连接
- 查看 GitHub Actions 日志
- 验证产品代码是否正确

### 2. 数据发送失败

**可能原因**：
- 目标API地址配置错误
- 目标API不可用
- 认证失败

**解决方法**：
- 检查 `TARGET_API_URL` 配置
- 验证目标API是否正常运行
- 如需认证，修改 `collector.py` 中的 `send_to_target_api` 方法

### 3. GitHub Actions 未执行

**可能原因**：
- Actions 未启用
- cron 表达式错误
- 仓库权限问题

**解决方法**：
- 确认 Actions 已启用
- 验证 cron 表达式
- 检查仓库的 Actions 权限设置

## 自定义开发

### 添加新的产品

在 `collector.py` 中的 `PRODUCT_NAMES` 字典中添加：

```python
PRODUCT_NAMES = {
    # ... 现有产品
    "NewProduct": "新产品名称"
}
```

### 修改数据发送逻辑

编辑 `collector.py` 中的 `send_to_target_api` 方法：

```python
def send_to_target_api(self, data: Dict) -> bool:
    # 添加认证 header
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {os.getenv("API_TOKEN")}'
    }
    
    response = requests.post(
        self.target_api_url,
        json=data,
        headers=headers,
        timeout=30
    )
    # ...
```

### 添加数据持久化

可以将数据保存到文件或数据库：

```python
import json
from datetime import datetime

def save_to_file(self, data: Dict):
    filename = f"data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
```

```bash
Au99.99,Au99.95,Au99.5,Au100g,iAu99.99,iAu100g,iAu99.5,Au(T+D),Au(T+N1),Au(T+N2),Ag99.99,Ag(T+D),Pt99.95,PGC30g,NYAuTN06,NYAuTN12
```

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

## 联系方式

如有问题，请提交 Issue 或联系维护者。

