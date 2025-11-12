# 数据库表结构说明

## 数据库信息
- **类型**: SQLite
- **文件**: `metal_prices.db`
- **字符集**: UTF-8

## 表结构

### 1. latest_prices (最新价格表)

存储每个产品的最新价格，自动更新。

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|--------|------|------|--------|------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | - | 主键ID |
| product_code | TEXT | NOT NULL, UNIQUE | - | 产品代码（唯一） |
| product_name | TEXT | NOT NULL | - | 产品名称 |
| current_price | REAL | NOT NULL | - | 当前价格 |
| current_time | TEXT | NOT NULL | - | 价格时间点（如 "10:45"） |
| min_price | REAL | - | - | 当日最低价 |
| max_price | REAL | - | - | 当日最高价 |
| data_timestamp | TEXT | NOT NULL | - | 数据源时间戳 |
| source | TEXT | NOT NULL | - | 数据来源（如 "SGE"） |
| **created_at** | TEXT | NOT NULL | datetime('now', 'localtime') | **创建时间（数据库自动设置）** |
| **updated_at** | TEXT | NOT NULL | datetime('now', 'localtime') | **更新时间（数据库自动更新）** |
| **deleted_at** | TEXT | - | NULL | **删除时间（软删除标记）** |

#### 索引
- UNIQUE INDEX on `product_code`

#### 触发器
- `update_latest_prices_timestamp`: 更新记录时自动更新 `updated_at` 字段

#### 特性
- **UPSERT**: 使用 `ON CONFLICT(product_code) DO UPDATE` 实现自动更新
- **自动时间戳**: `created_at` 在插入时自动设置，`updated_at` 在更新时自动更新
- **软删除**: 通过设置 `deleted_at` 实现软删除，不实际删除记录

---

### 2. price_history (历史记录表)

存储所有历史价格记录，只增不改。

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|--------|------|------|--------|------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | - | 主键ID |
| product_code | TEXT | NOT NULL | - | 产品代码 |
| product_name | TEXT | NOT NULL | - | 产品名称 |
| current_price | REAL | NOT NULL | - | 当前价格 |
| current_time | TEXT | NOT NULL | - | 价格时间点 |
| min_price | REAL | - | - | 当日最低价 |
| max_price | REAL | - | - | 当日最高价 |
| data_timestamp | TEXT | NOT NULL | - | 数据源时间戳 |
| collect_timestamp | TEXT | NOT NULL | - | 采集时间戳 |
| source | TEXT | NOT NULL | - | 数据来源 |
| **created_at** | TEXT | NOT NULL | datetime('now', 'localtime') | **创建时间（数据库自动设置）** |
| **updated_at** | TEXT | NOT NULL | datetime('now', 'localtime') | **更新时间（数据库自动更新）** |
| **deleted_at** | TEXT | - | NULL | **删除时间（软删除标记）** |

#### 索引
- INDEX `idx_history_product` on `product_code`
- INDEX `idx_history_time` on `created_at`

#### 触发器
- `update_price_history_timestamp`: 更新记录时自动更新 `updated_at` 字段

#### 特性
- **只增不改**: 历史记录表通常只插入新记录，不更新
- **自动时间戳**: `created_at` 和 `updated_at` 由数据库自动管理
- **软删除**: 支持通过 `deleted_at` 标记删除

---

## 时间字段说明

### created_at (创建时间)
- **用途**: 记录数据首次插入数据库的时间
- **设置方式**: 数据库自动设置（DEFAULT）
- **格式**: `YYYY-MM-DD HH:MM:SS`（本地时间）
- **特点**: 
  - 插入时自动设置
  - 不会被更新
  - 永久保持首次创建时间

### updated_at (更新时间)
- **用途**: 记录数据最后一次更新的时间
- **设置方式**: 
  - 插入时自动设置（DEFAULT）
  - 更新时通过触发器自动更新
- **格式**: `YYYY-MM-DD HH:MM:SS`（本地时间）
- **特点**:
  - 插入时等于 `created_at`
  - 每次更新时自动刷新
  - 反映最新修改时间

### deleted_at (删除时间)
- **用途**: 软删除标记，记录逻辑删除时间
- **设置方式**: 应用层手动设置
- **格式**: `YYYY-MM-DD HH:MM:SS` 或 NULL
- **特点**:
  - 默认为 NULL（未删除）
  - 设置时间表示已删除
  - 数据仍保留在数据库中
  - 查询时可过滤 `deleted_at IS NULL`

---

## 时间字段使用示例

### 1. 查询未删除的最新价格
```sql
SELECT * FROM latest_prices 
WHERE deleted_at IS NULL
ORDER BY updated_at DESC;
```

### 2. 查询最近1小时的更新
```sql
SELECT * FROM latest_prices 
WHERE updated_at >= datetime('now', '-1 hour', 'localtime')
AND deleted_at IS NULL;
```

### 3. 查询历史记录（按创建时间）
```sql
SELECT * FROM price_history 
WHERE created_at >= '2025-11-12 00:00:00'
AND deleted_at IS NULL
ORDER BY created_at DESC;
```

### 4. 软删除记录
```sql
UPDATE latest_prices 
SET deleted_at = datetime('now', 'localtime')
WHERE product_code = 'Au99.99';
```

### 5. 恢复软删除的记录
```sql
UPDATE latest_prices 
SET deleted_at = NULL
WHERE product_code = 'Au99.99';
```

### 6. 查询已删除的记录
```sql
SELECT * FROM latest_prices 
WHERE deleted_at IS NOT NULL
ORDER BY deleted_at DESC;
```

---

## 触发器详情

### update_latest_prices_timestamp
```sql
CREATE TRIGGER IF NOT EXISTS update_latest_prices_timestamp 
AFTER UPDATE ON latest_prices
FOR EACH ROW
BEGIN
    UPDATE latest_prices 
    SET updated_at = datetime('now', 'localtime')
    WHERE id = NEW.id;
END;
```

**作用**: 当 `latest_prices` 表的任何记录被更新时，自动更新该记录的 `updated_at` 字段为当前时间。

### update_price_history_timestamp
```sql
CREATE TRIGGER IF NOT EXISTS update_price_history_timestamp 
AFTER UPDATE ON price_history
FOR EACH ROW
BEGIN
    UPDATE price_history 
    SET updated_at = datetime('now', 'localtime')
    WHERE id = NEW.id;
END;
```

**作用**: 当 `price_history` 表的任何记录被更新时，自动更新该记录的 `updated_at` 字段为当前时间。

---

## 数据示例

### latest_prices 表数据示例
```json
{
  "id": 1,
  "product_code": "Au99.99",
  "product_name": "黄金99.99",
  "current_price": 949.0,
  "current_time": "10:45",
  "min_price": 934.0,
  "max_price": 950.0,
  "data_timestamp": "2025年11月12日 10:45:00",
  "source": "SGE",
  "created_at": "2025-11-12 10:56:23",
  "updated_at": "2025-11-12 11:00:51",
  "deleted_at": null
}
```

### price_history 表数据示例
```json
{
  "id": 1,
  "product_code": "Au99.99",
  "product_name": "黄金99.99",
  "current_price": 949.0,
  "current_time": "10:45",
  "min_price": 934.0,
  "max_price": 950.0,
  "data_timestamp": "2025年11月12日 10:45:00",
  "collect_timestamp": "2025-11-12 10:45:00",
  "source": "SGE",
  "created_at": "2025-11-12 10:56:23",
  "updated_at": "2025-11-12 10:56:23",
  "deleted_at": null
}
```

---

## 时间字段对比

| 时间字段 | 最新价格表 | 历史记录表 | 自动管理 | 可修改 | 用途 |
|---------|-----------|-----------|---------|--------|------|
| created_at | ✅ | ✅ | ✅ 数据库 | ❌ | 记录创建时间 |
| updated_at | ✅ | ✅ | ✅ 触发器 | ❌ | 记录更新时间 |
| deleted_at | ✅ | ✅ | ❌ | ✅ | 软删除标记 |

---

## 注意事项

1. **时区**: 所有时间字段使用本地时间（localtime），确保服务器时区设置正确
2. **自动更新**: `created_at` 和 `updated_at` 完全由数据库管理，应用层不需要设置
3. **软删除**: 使用 `deleted_at` 实现软删除，查询时需要过滤 `deleted_at IS NULL`
4. **触发器**: 触发器会在每次 UPDATE 时执行，确保 `updated_at` 始终准确
5. **历史记录**: `price_history` 表通常只插入不更新，但仍支持更新时自动刷新 `updated_at`
6. **性能**: 索引已创建在常用查询字段上，确保查询性能

---

## 迁移说明

如果从旧版本升级，需要：

1. **备份数据库**
```bash
cp metal_prices.db metal_prices.db.backup
```

2. **删除旧数据库**（或执行 ALTER TABLE 添加字段）
```bash
rm metal_prices.db
```

3. **重启服务**（自动创建新表结构）
```bash
python server.py
```

4. **验证新字段**
```bash
# 查询验证
curl http://localhost:5000/api/prices/latest
```

---

## API 返回示例

### 查询最新价格
```bash
GET /api/prices/latest?product_code=Au99.99
```

**响应**:
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
      "current_time": "10:45",
      "min_price": 934.0,
      "max_price": 950.0,
      "data_timestamp": "2025年11月12日 10:45:00",
      "source": "SGE",
      "created_at": "2025-11-12 10:56:23",
      "updated_at": "2025-11-12 11:00:51",
      "deleted_at": null
    }
  ]
}
```

### 查询历史记录
```bash
GET /api/prices/history?product_code=Au99.99&limit=2
```

**响应**:
```json
{
  "success": true,
  "count": 2,
  "data": [
    {
      "id": 4,
      "product_code": "Au99.99",
      "product_name": "黄金99.99",
      "current_price": 949.0,
      "current_time": "10:45",
      "min_price": 934.0,
      "max_price": 950.0,
      "data_timestamp": "2025年11月12日 10:45:00",
      "collect_timestamp": "2025-11-12 10:45:00",
      "source": "SGE",
      "created_at": "2025-11-12 11:00:51",
      "updated_at": "2025-11-12 11:00:51",
      "deleted_at": null
    },
    {
      "id": 1,
      "product_code": "Au99.99",
      "product_name": "黄金99.99",
      "current_price": 949.0,
      "current_time": "10:45",
      "min_price": 934.0,
      "max_price": 950.0,
      "data_timestamp": "2025年11月12日 10:45:00",
      "collect_timestamp": "2025-11-12 10:45:00",
      "source": "SGE",
      "created_at": "2025-11-12 10:56:23",
      "updated_at": "2025-11-12 10:56:23",
      "deleted_at": null
    }
  ]
}
```
