# 后端代码规范 (Backend Code Style)

> **规范来源**：本项目的 Python 代码遵循
> [PEP 8 — Style Guide for Python Code](https://peps.python.org/pep-0008/)
> 与 [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)。

## 1. 缩进与格式

- 每级缩进使用 **4 个空格**，禁止使用 Tab。
- 每行不超过 **79** 个字符（PEP 8 推荐）。
- 文件末尾保留一个换行符。
- 顶层定义之间空 2 行，类内方法之间空 1 行。

## 2. 命名规范

| 对象 | 约定 | 示例 |
| --- | --- | --- |
| 模块 / 包 | 小写下划线 | `calculator_service` |
| 类 | 大驼峰 | `CalculatorService` |
| 函数 / 变量 | 小写下划线 | `format_result` |
| 常量 | 全大写下划线 | `MAX_DECIMAL_PLACES` |
| 私有成员 | 前缀下划线 | `_db`、`_tokens` |

## 3. 导入

- 导入分为三组：标准库、第三方库、本项目模块，组间空一行。
- 使用绝对 / 显式相对导入，禁止 `from module import *`。
- 按字母顺序排列同一组内的导入。

## 4. 类型注解与文档

- 公共函数一律添加类型注解。
- 每个模块写模块级 docstring；公共类与函数写 docstring。
- docstring 使用三引号，首行简述用途。

## 5. 函数与类

- 单个函数尽量不超过 50 行，职责单一。
- 类使用 `__slots__` 优化高频小对象（如 `Token`）。
- 避免可变默认参数。

## 6. 错误处理

- 自定义异常统一继承 `CalcError`。
- 禁止使用裸 `except:`，必须捕获具体异常或 `Exception` 并说明原因。
- 异常信息面向用户，避免泄露内部细节。

## 7. 安全

- **禁止使用 `eval` / `exec` / `compile`** 执行用户输入。
- 数据库访问统一使用参数化查询（`?` 占位符），防止 SQL 注入。

## 8. 分层约定

- `controller`：只做 HTTP 入参校验与响应封装。
- `service`：编排业务逻辑，是唯一同时访问计算引擎与数据库的层。
- `model`：只负责数据库读写。
- `calculator`：纯计算引擎，不依赖 Web 框架与数据库。
