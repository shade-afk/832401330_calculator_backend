# 计算器后端 (Calculator Backend)

前后端分离计算器系统的**后端**，基于 **Flask + SQLite**，负责表达式解析与计算、输入校验、异常处理以及计算历史的持久化。

## 架构

```
前端 (HTML/JS)
     │  HTTP + JSON
     ▼
Flask REST API
     │
     ▼
SQLite 数据库 (calculation_history)
```

核心计算逻辑**全部在后端完成**，前端只负责提交表达式与展示结果。

## 技术栈

| 用途 | 技术 |
| --- | --- |
| Web 框架 | Flask 3.x |
| 跨域 | flask-cors |
| 数据库 | SQLite（Python 内置 `sqlite3`） |
| 表达式解析 | 自研「词法分析 + 递归下降解析器」，不依赖 `eval` / `exec` |

## 目录结构

```
calculator_backend/
├── app.py                     # 应用入口 / 工厂函数
├── requirements.txt
├── src/
│   ├── config.py              # 配置（端口、数据库路径、CORS）
│   ├── calculator/            # 安全表达式计算引擎
│   │   ├── errors.py          # 异常定义
│   │   ├── tokenizer.py       # 词法分析
│   │   └── parser.py          # 递归下降解析 + 求值
│   ├── controller/
│   │   └── api.py             # REST 接口
│   ├── service/
│   │   └── calculator_service.py  # 业务逻辑
│   └── model/
│       └── database.py        # SQLite 访问层
├── tests/
│   └── test_calculator.py     # 单元测试 + 集成测试
├── README.md
└── codestyle.md
```

## 快速开始

```bash
# 1. 创建虚拟环境（可选，推荐）
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux

# 2. 安装依赖
pip install -r requirements.txt

# 3. 启动服务（默认 0.0.0.0:5000）
python app.py
```

启动后数据库文件 `data/calculator.db` 会自动创建并初始化表结构。

访问 `http://127.0.0.1:5000/` 可查看服务信息。

## 配置项（环境变量）

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `CALC_HOST` | `0.0.0.0` | 监听地址 |
| `CALC_PORT` | `5000` | 监听端口 |
| `CALC_DEBUG` | `1` | 调试模式 |
| `CALC_DB_PATH` | `data/calculator.db` | SQLite 文件路径 |
| `CALC_CORS_ORIGINS` | `*` | 允许的前端来源 |
| `CALC_HISTORY_LIMIT` | `200` | 历史查询上限 |

## 数据库设计

```sql
CREATE TABLE calculation_history (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    expression  TEXT NOT NULL,   -- 计算表达式
    result      TEXT NOT NULL,   -- 计算结果
    created_at  TEXT NOT NULL    -- 计算时间
);
```

## API 说明

### 1. 计算表达式

```
POST /api/calculate
Content-Type: application/json

{ "expression": "(1+2)*3" }
```

成功响应 `201 Created`：

```json
{
  "success": true,
  "id": 1,
  "expression": "(1+2)*3",
  "result": 9,
  "createdAt": "2026-10-01 10:20:00"
}
```

失败响应 `400 Bad Request`：

```json
{ "success": false, "message": "Division by zero" }
```

### 2. 查询历史

```
GET /api/history
```

```json
{
  "success": true,
  "history": [
    { "id": 1, "expression": "(1+2)*3", "result": "9", "createdAt": "2026-10-01 10:20:00" }
  ]
}
```

### 3. 删除单条历史

```
DELETE /api/history/{id}
```

成功返回 `200`，记录不存在返回 `404`。

### 4. 清空历史（扩展功能）

```
DELETE /api/history
```

### 5. 健康检查

```
GET /api/health
```

## 表达式支持范围

- 四则运算：`+ - * /`（同时兼容 UI 的 `× ÷` 符号）
- 括号：`( )`
- 一元正负号：`-5`、`3*-2`、`--5`
- 小数：`0.1`、`1.5`
- 运算优先级按数学规则处理
- 非法表达式、括号不匹配、除零、非法字符均返回 `400` 与错误信息
- **不使用 `eval` / `exec`**，非法输入不会被当作代码执行

## 运行测试

```bash
python -m unittest discover -s tests -v
```

## 部署要点

- 使用生产 WSGI 服务器，例如 `waitress`：

  ```bash
  pip install waitress
  waitress-serve --host=0.0.0.0 --port=5000 app:app
  ```

- 生产环境请把 `CALC_CORS_ORIGINS` 设置为前端实际域名。
- 如需持久化，将 `CALC_DB_PATH` 指向挂载的数据卷目录。
