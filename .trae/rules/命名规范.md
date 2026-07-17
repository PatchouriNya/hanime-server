# LibraryDream 命名规范

> **品牌**: LibraryDream（图书馆之梦）  
> **版本**: 2.0.0  
> **适用范围**: 所有 LibraryDream 品牌下的项目，包含但不限于 Web 应用、API 服务、移动端、小程序、脚本工具、中间件配置等。  
> **核心理念**: 像图书馆的目录卡片一样——任何人仅凭名字就知道它是什么、属于哪里、该往哪放。

---

## 目录

1. [命名哲学](#1-命名哲学)
2. [核心原则](#2-核心原则)
3. [通用缩写规范](#3-通用缩写规范)
4. [数据库命名规范 (MySQL)](#4-数据库命名规范-mysql)
5. [Redis 命名规范](#5-redis-命名规范)
6. [Python 代码命名规范](#6-python-代码命名规范)
7. [TypeScript / JavaScript 命名规范](#7-typescript--javascript-命名规范)
8. [Vue 组件命名规范](#8-vue-组件命名规范)
9. [CSS / SCSS 命名规范](#9-css--scss-命名规范)
10. [文件与目录命名规范](#10-文件与目录命名规范)
11. [API 命名规范](#11-api-命名规范)
12. [Docker 命名规范](#12-docker-命名规范)
13. [环境变量命名规范](#13-环境变量命名规范)
14. [日志命名规范](#14-日志命名规范)
15. [Git 命名规范](#15-git-命名规范)
16. [魔数禁止规范](#16-魔数禁止规范)
17. [配置与常量管理规范](#17-配置与常量管理规范)
18. [版本号规范](#18-版本号规范)
19. [附录](#19-附录)

---

## 1. 命名哲学

### 1.1 品牌隐喻

LibraryDream 的命名体系以"图书馆"为隐喻：

| 概念 | 隐喻 | 说明 |
|------|------|------|
| **数据库** | 图书馆建筑 | 容纳所有知识的基础设施 |
| **表 (Table)** | 书架 (Shelf) | 同一类实体的集合 |
| **行 (Row)** | 藏书 (Tome) | 每一条数据都是一本值得珍藏的书 |
| **列 (Column)** | 目录卡片字段 | 精确描述一个属性 |
| **索引 (Index)** | 检索目录 | 让查找更快 |
| **主键 (PK)** | ISBN | 全球唯一、不可变 |
| **外键 (FK)** | 交叉引用 | 连接不同书架的桥梁 |
| **视图 (View)** | 主题展台 | 为特定目的组织的临时集合 |
| **存储过程** | 图书管理员规程 | 标准化的操作流程 |
| **Redis** | 速查便签墙 | 临时、快速的查询入口 |
| **API** | 借阅柜台 | 对外服务的统一窗口 |
| **Docker 镜像** | 图书装订厂 | 标准化的封装与分发 |

### 1.2 命名的三问检验法

每次命名时，问自己三个问题：

1. **这是什么？** — 名字必须准确描述其本质
2. **它属于哪里？** — 名字必须体现层级归属
3. **它和同类有什么区别？** — 名字必须有区分度，禁用 `data`、`info`、`temp` 等万能词

---

## 2. 核心原则

### 2.1 统一胜过个性

同一语言、同一框架内，命名风格必须统一。Python 文件不允许混用 `snake_case` 和 `camelCase`。

### 2.2 明确胜过简短

```python
# ✗ 坏：缩写到看不懂
usr_pwd = "xxx"
get_usr_perm()

# ✓ 好：清晰完整
user_password = "xxx"
get_user_permission()
```

**例外**: 循环变量、闭包参数等作用域极小的场景，单字母可接受：

```python
for i in range(10):
    items[i].process()

users = [u for u in all_users if u.is_active]
```

### 2.3 语义胜过类型

不要在名字中编码类型信息（匈牙利命名法已过时）：

```python
# ✗ 坏
str_username = "Alice"
list_videos = []
int_count = 5

# ✓ 好
username = "Alice"
videos = []
count = 5
```

### 2.4 正向命名

布尔值始终使用正向语义：

```python
# ✗ 坏
is_not_found = True
disabled = False

# ✓ 好
is_found = False
is_enabled = True
```

### 2.5 对称性原则

```typescript
start() / stop()
open() / close()
beginTransaction() / commitTransaction() / rollbackTransaction()
addItem() / removeItem()
loadData() / saveData()
```

### 2.6 避免万能词

| 禁止词 | 原因 |
|--------|------|
| `data` | 所有东西都是数据 |
| `info` | 无法和 data 区分 |
| `temp` | 所有变量都是临时的 |
| `util` / `utils` | 垃圾桶目录 |
| `helper` | 同 utils |
| `common` | 同 utils |
| `manager` | 过于宽泛 |
| `handler` | 同 manager |
| `process` | 动词用作名词，含义模糊 |
| `item` | 非泛型场景禁用 |
| `flag` | 改用具体含义的布尔名 |
| `result` | 所有函数都返回结果 |

---

## 3. 通用缩写规范

### 3.1 允许使用的缩写

| 缩写 | 全称 | 说明 |
|------|------|------|
| `id` | identifier | 标识符 |
| `url` | Uniform Resource Locator | 网址 |
| `api` | Application Programming Interface | 接口 |
| `db` | database | 数据库 |
| `sql` | Structured Query Language | 查询 |
| `http` | Hypertext Transfer Protocol | 协议 |
| `json` | JavaScript Object Notation | 数据格式 |
| `html` | HyperText Markup Language | 标记语言 |
| `css` | Cascading Style Sheets | 样式 |
| `js` / `ts` | JavaScript / TypeScript | 脚本语言 |
| `ui` | User Interface | 界面 |
| `os` | Operating System | 操作系统 |
| `io` | Input / Output | 输入输出 |
| `max` / `min` | maximum / minimum | 最大/最小 |
| `avg` | average | 平均值 |
| `num` | number | 数量（仅局部作用域） |
| `src` / `dst` | source / destination | 来源/目标 |
| `arg` / `args` | argument(s) | 参数 |
| `param` / `params` | parameter(s) | 参数 |
| `ctx` | context | 上下文 |
| `req` / `res` | request / response | 仅 HTTP 层 |
| `msg` | message | 消息 |
| `err` | error | 仅 `except` 块中 |
| `cfg` | configuration | 仅局部作用域 |
| `init` | initialize | 初始化 |
| `sync` / `async` | synchronous / asynchronous | 同步/异步 |
| `ttl` | time to live | 过期时间 |
| `rpc` | remote procedure call | 远程调用 |

### 3.2 严禁使用的缩写

| 缩写 | 原因 |
|------|------|
| `usr` | 写 `user` |
| `pwd` | 写 `password`，且 pwd 在 Unix 中有歧义 |
| `txt` | 写 `text` |
| `cnt` | 写 `count` |
| `idx` | 写 `index`（MySQL 索引前缀除外） |
| `ptr` | 现代语言无指针 |
| `obj` | 写 `object` |
| `btn` | 写 `button` |
| `lbl` | 写 `label` |
| `tbl` | 写 `table` |
| `cols` | 与 CSS columns 混淆 |
| `desc` | MySQL 关键字 + 歧义 |
| `stat` | statistic 还是 status？ |
| `auth` | authentication 还是 authorization？必须写全 |
| `mod` | module 还是 modify？ |
| `img` | 写 `image`（目录名除外） |

---

## 4. 数据库命名规范 (MySQL)

### 4.1 数据库命名

```
格式: ld_{project_name}
示例: ld_blog, ld_shop, ld_cms
```

- 统一使用 `ld_` 品牌前缀
- 全小写 + 下划线
- 不超过 30 字符
- 字符集 `utf8mb4`，排序规则 `utf8mb4_unicode_ci`

```sql
CREATE DATABASE ld_blog
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;
```

### 4.2 表命名

```
格式: {namespace}_{entity}
```

- **表名用单数**（一个表 = 一个实体类型）
- 关联表（多对多）按字母序：`role_user`（不是 `user_role`，R < U）
- 全小写 + 下划线，不超过 50 字符
- 禁用 MySQL 保留字

```sql
-- ✓ 好
user
user_profile
video_comment
role_user              -- 多对多，字母序

-- ✗ 坏
users                  -- 复数
UserProfile            -- 大写
videoComment           -- camelCase
```

### 4.3 字段命名

```
格式: {qualifier}_{property}
```

| 类别 | 格式 | 示例 |
|------|------|------|
| 主键 | `id` | `id` |
| 外键 | `{table}_id` | `user_id`, `video_id` |
| 文本 | `{qualifier}_{name}` | `user_display_name`, `product_title` |
| 数值 | `{qualifier}_{name}` | `product_price`, `item_weight_grams` |
| 布尔 | `is_{adjective}` | `is_active`, `is_deleted`, `is_verified` |
| 时间戳 | `{action}_at` | `created_at`, `updated_at`, `deleted_at` |
| 日期 | `{action}_date` | `birth_date`, `expiry_date` |
| 状态 | `status` 或 `{type}_status` | `status`, `order_status` |
| 排序 | `sort_order` | `sort_order` |
| 枚举类型 | `{name}_type` | `user_type`, `media_type` |
| 计数 | `{thing}_count` | `view_count`, `comment_count` |
| 百分比 | `{thing}_rate` 或 `{thing}_ratio` | `completion_rate` |
| JSON | `{name}_data` | `settings_data`, `metadata_data` |
| 金额 | `{name}_amount` 或 `{name}_price` | `total_amount`, `unit_price` |
| 软删除 | `deleted_at` (TIMESTAMP NULL) | `deleted_at` |

**字段注释强制规范**:

```sql
-- 所有字段必须有 COMMENT，状态字段必须列出所有可能值
`user_type` TINYINT UNSIGNED NOT NULL DEFAULT 1 COMMENT '用户类型: 1=普通用户, 2=管理员, 3=超级管理员'
`status`    TINYINT UNSIGNED NOT NULL DEFAULT 10 COMMENT '订单状态: 10=待支付, 20=已支付, 30=已发货, 40=已完成, 50=已取消'
```

**布尔字段**:

```sql
is_active     TINYINT(1) NOT NULL DEFAULT 1
is_deleted    TINYINT(1) NOT NULL DEFAULT 0
is_verified   TINYINT(1) NOT NULL DEFAULT 0
```

**时间字段**:

```sql
created_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
updated_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
deleted_at    TIMESTAMP NULL DEFAULT NULL
published_at  TIMESTAMP NULL DEFAULT NULL
expired_at    TIMESTAMP NULL DEFAULT NULL
birth_date    DATE NULL
```

**金额字段**:

```sql
-- 永远用 DECIMAL，禁止 FLOAT/DOUBLE
unit_price          DECIMAL(12, 2) NOT NULL DEFAULT 0.00
total_amount        DECIMAL(12, 2) NOT NULL DEFAULT 0.00
tax_amount          DECIMAL(10, 2) NOT NULL DEFAULT 0.00
```

**外键字段**: 字段名必须与引用的表名一致：

```sql
-- ✓ 好
FOREIGN KEY (user_id) REFERENCES user(id)
FOREIGN KEY (video_id) REFERENCES video(id)

-- ✗ 坏
FOREIGN KEY (owner) REFERENCES user(id)
FOREIGN KEY (comment_video) REFERENCES video(id)
```

### 4.4 索引命名

```
格式: {prefix}_{table}_{columns}
```

| 索引类型 | 前缀 | 示例 |
|----------|------|------|
| 普通索引 | `idx` | `idx_user_email` |
| 唯一索引 | `uk` | `uk_user_username` |
| 外键索引 | `fk` | `fk_comment_user_id` |
| 全文索引 | `ft` | `ft_article_content` |
| 空间索引 | `sp` | `sp_location_coord` |

联合索引列名按下划线连接，高选择性列在前：

```sql
idx_user_status_created      -- (status, created_at)
uk_order_user_product        -- (user_id, product_id)
```

### 4.5 视图命名

```
格式: v_{descriptive_name}
示例: v_active_user_summary, v_monthly_sales_report
```

`v_` 前缀区分表和视图。名称描述用途，不描述底层表。

### 4.6 存储过程 / 函数 / 触发器

```
sp_{action}_{entity}         -- 存储过程，如 sp_create_order
fn_{computation}             -- 函数，如 fn_calculate_tax
tr_{table}_{before|after}_{insert|update|delete}  -- 触发器，如 tr_order_after_update
```

### 4.7 数据库迁移文件

```
格式: {YYYYMMDDHHMMSS}_{description}.sql
示例: 20260717083000_create_user_table.sql
      20260717090000_add_email_to_user.sql
```

时间戳精确到秒，按执行顺序自然排列。

### 4.8 数据类型约定

| 场景 | 类型 | 说明 |
|------|------|------|
| 主键 | `BIGINT UNSIGNED AUTO_INCREMENT` | 不用 INT，上限太低 |
| UUID 主键 | `BINARY(16)` | 比 CHAR(36) 节省一半空间 |
| 短文本 (≤255) | `VARCHAR(N)` | N 取实际最大值，不无脑 255 |
| 长文本 | `TEXT` / `MEDIUMTEXT` | 禁止 VARCHAR(10000) |
| 超长文本 | `LONGTEXT` | 如文章正文 |
| 布尔 | `TINYINT(1)` | 禁止 ENUM/CHAR |
| 状态枚举 | `TINYINT UNSIGNED` | 禁止 MySQL ENUM 类型 |
| 时间戳 | `TIMESTAMP` | 自动时区转换 |
| 日期 | `DATE` | 如生日 |
| 金额 | `DECIMAL(M, D)` | 禁止 FLOAT/DOUBLE |
| 百分比 | `DECIMAL(5, 2)` | 范围 0.00~100.00 |
| JSON | `JSON` (MySQL 5.7+) | 不用 TEXT 存 JSON |
| 文件路径 | `VARCHAR(500)` | 文件存 OSS，数据库存路径 |
| IP 地址 | `VARCHAR(45)` | 兼容 IPv6 |
| UUID | `CHAR(36)` | 通用格式；内部可用 BINARY(16) |

### 4.9 表结构完整示例

```sql
CREATE TABLE `ld_blog`.`user` (
    `id`              BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `username`        VARCHAR(50)     NOT NULL COMMENT '用户名',
    `display_name`    VARCHAR(100)    NOT NULL DEFAULT '' COMMENT '显示名称',
    `email`           VARCHAR(200)    NOT NULL DEFAULT '' COMMENT '邮箱',
    `password_hash`   VARCHAR(255)    NOT NULL COMMENT '密码哈希',
    `user_type`       TINYINT UNSIGNED NOT NULL DEFAULT 1 COMMENT '用户类型: 1=普通用户, 2=管理员',
    `is_active`       TINYINT(1)      NOT NULL DEFAULT 1 COMMENT '是否激活',
    `is_verified`     TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '是否已验证邮箱',
    `avatar_path`     VARCHAR(500)    NOT NULL DEFAULT '' COMMENT '头像路径',
    `created_at`      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at`      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `deleted_at`      TIMESTAMP       NULL DEFAULT NULL COMMENT '软删除时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_user_username` (`username`),
    UNIQUE KEY `uk_user_email` (`email`),
    KEY `idx_user_status_created` (`is_active`, `created_at`),
    KEY `idx_user_type` (`user_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';
```

---

## 5. Redis 命名规范

### 5.1 Key 总体格式

```
格式: {brand}:{project}:{category}:{entity}:{identifier}[:{attribute}]
分隔符: 冒号 (:)
品牌前缀: ld
```

### 5.2 Key 分类命名

| 用途 | 格式 | 示例 |
|------|------|------|
| 业务缓存 | `ld:{project}:cache:{entity}:{id}` | `ld:blog:cache:article:123` |
| 业务缓存(子属性) | `ld:{project}:cache:{entity}:{id}:{attr}` | `ld:blog:cache:user:456:profile` |
| 会话 | `ld:{project}:session:{type}:{token}` | `ld:blog:session:access:abc123` |
| 会话(用户) | `ld:{project}:session:user:{user_id}` | `ld:blog:session:user:789` |
| 分布式锁 | `ld:{project}:lock:{resource}:{id}` | `ld:blog:lock:order:456` |
| 计数器 | `ld:{project}:counter:{entity}:{attr}` | `ld:blog:counter:article:view` |
| 计数器(周期) | `ld:{project}:counter:{entity}:{attr}:{period}` | `ld:blog:counter:article:view:daily` |
| 排行榜 | `ld:{project}:rank:{entity}:{period}` | `ld:blog:rank:article:weekly` |
| 消息队列 | `ld:{project}:queue:{task_type}` | `ld:blog:queue:email` |
| 限流 | `ld:{project}:ratelimit:{user_id}:{action}` | `ld:blog:ratelimit:123:login` |
| 验证码 | `ld:{project}:verify:{type}:{target}` | `ld:blog:verify:email:user@x.com` |
| 临时数据 | `ld:{project}:temp:{purpose}:{id}` | `ld:blog:temp:import:batch_001` |
| 配置 | `ld:{project}:config:{key}` | `ld:blog:config:feature_flags` |
| Pub/Sub 频道 | `ld:{project}:channel:{event}` | `ld:blog:channel:order.created` |

### 5.3 Key 命名规则

1. **全小写**，冒号分隔，单词间用下划线（如有需要）
2. **不包含空格和特殊字符**
3. **Key 长度不超过 512 字符**（Redis 限制且长 Key 浪费内存）
4. **禁止动态前缀**，前缀必须是可预测的静态字符串
5. **禁止将用户输入直接拼入 Key**，必须先做哈希或编码

```bash
# ✗ 坏：动态前缀，无法批量管理
{user_id}:profile
{article_id}:comments

# ✗ 坏：Key 过长
ld:blog:cache:article_content_with_all_comments_and_user_info_and_tags:123456

# ✓ 好
ld:blog:cache:article:123456
```

### 5.4 数据结构选择

| 场景 | 使用类型 | 说明 |
|------|----------|------|
| 简单键值 | `String` | 缓存单个对象（JSON 序列化）、计数器 |
| 对象属性 | `Hash` | 需要单独读写字段的场景 |
| 队列/栈 | `List` | 消息队列、最近N条记录 |
| 去重集合 | `Set` | 标签、关注关系 |
| 排行榜 | `Sorted Set` | 积分排行、时间排序 |
| 消息流 | `Stream` | 事件溯源、消息持久化 |
| 位图 | `Bitmap` | 签到、在线状态 |
| 地理位置 | `Geo` | 附近的人、距离计算 |
| 发布订阅 | `Pub/Sub` | 实时通知、聊天 |

**Hash 和 String 的选择**:

```
Hash 适用于: 需要频繁读写单个字段、字段数 < 100、数据量 < 1MB
String (JSON) 适用于: 一次性读写整个对象、字段数多但在应用层解析
```

### 5.5 TTL 约定

所有缓存 Key 必须设置 TTL，禁止永久缓存：

| 类型 | TTL | 说明 |
|------|-----|------|
| 热点数据缓存 | 60s ~ 300s | 首页数据、热门文章 |
| 普通业务缓存 | 600s ~ 3600s | 用户信息、文章详情 |
| 配置缓存 | 3600s ~ 86400s | 系统配置、功能开关 |
| 会话 | 7200s ~ 86400s | JWT token 有效期 |
| 验证码 | 300s ~ 600s | 短信/邮件验证码 |
| 限流计数器 | 按窗口设置 | 如 60s 窗口 |
| 分布式锁 | ≤ 30s | 必须设置，防死锁 |
| 临时数据 | ≤ 3600s | 导入临时文件等 |

**TTL 必须在代码中显式设置，不允许依赖默认值。**

```python
# ✓ 好：显式 TTL
await redis.setex("ld:blog:cache:article:123", 3600, json_data)

# ✗ 坏：无 TTL
await redis.set("ld:blog:cache:article:123", json_data)
```

### 5.6 禁用项

- **禁止 `KEYS *`**，生产环境使用 `SCAN`
- **禁止 `FLUSHDB` / `FLUSHALL`**，除非在测试环境
- **禁止大 Key**（String > 10MB，集合 > 10000 元素不设拆分策略）
- **禁止 Hot Key**（单个 Key QPS > 1000 需拆分）
- **禁止不设 TTL 的 Key**

---

## 6. Python 代码命名规范

### 6.1 总览

| 元素 | 风格 | 示例 |
|------|------|------|
| 模块（文件） | `snake_case` | `user_service.py`, `cache_utils.py` |
| 包（目录） | `snake_case` | `api/`, `services/`, `data_access/` |
| 类 | `PascalCase` | `UserRepository`, `OrderParser` |
| 异常类 | `PascalCase` + `Error` | `ValidationError`, `ConnectionTimeoutError` |
| 函数 / 方法 | `snake_case` | `get_user_by_id()`, `parse_content()` |
| 变量 | `snake_case` | `user_id`, `page_content` |
| 常量 | `UPPER_SNAKE_CASE` | `MAX_RETRY_COUNT`, `DEFAULT_TTL` |
| 私有成员 | `_snake_case` | `_cache`, `_parse_raw()` |
| 内部私有 | `__snake_case` | `__internal_state` |
| 枚举成员 | `UPPER_SNAKE_CASE` | `Status.PENDING`, `Color.RED` |
| 类型别名 | `PascalCase` | `JsonDict = dict[str, Any]` |

### 6.2 函数动词规范

```python
get_user_by_id()        # 获取单个
list_active_users()     # 获取列表
search_content()        # 搜索（有查询条件）
create_order()          # 创建
update_profile()        # 更新
delete_comment()        # 删除
save_settings()         # 持久化
load_config()           # 加载
parse_content()         # 解析
validate_input()        # 验证
convert_format()        # 转换
fetch_remote_data()     # 远程获取
compute_total()         # 计算
build_query()           # 构建

# 布尔返回值
is_valid_email(email: str) -> bool
has_permission(user_id: int) -> bool
can_access(resource_id: int) -> bool
```

### 6.3 类命名

```python
class UserRepository:      # Repository: 数据访问层
class OrderService:        # Service: 业务逻辑层
class AppConfig:           # Config: 配置类
class ValidationError:     # Error: 异常类
class AbstractParser:      # Abstract: 抽象基类
class BaseRepository:      # Base: 基类
```

### 6.4 枚举定义

```python
from enum import IntEnum

class UserType(IntEnum):
    NORMAL = 1        # 不从 0 开始（0 是 falsy）
    ADMIN = 2
    SUPER_ADMIN = 3

class OrderStatus(IntEnum):
    PENDING = 10      # 间隔 10，方便插入
    CONFIRMED = 20
    PROCESSING = 30
    COMPLETED = 40
    CANCELLED = 50
```

### 6.5 导入顺序

```python
# 1. 标准库
import os
from datetime import datetime

# 2. 第三方库
from fastapi import APIRouter

# 3. 项目内模块
from app.config import settings
```

---

## 7. TypeScript / JavaScript 命名规范

### 7.1 总览

| 元素 | 风格 | 示例 |
|------|------|------|
| 变量 | `camelCase` | `userId`, `isLoading` |
| 编译时常量 | `UPPER_SNAKE_CASE` | `MAX_PAGE_SIZE`, `API_BASE_URL` |
| 运行时常量 | `camelCase` | `defaultPageSize` |
| 函数 | `camelCase` | `getUserById()`, `formatDate()` |
| 类 | `PascalCase` | `UserApi`, `CacheManager` |
| 接口 | `PascalCase` | `UserProfile`, `SearchResult` |
| 类型别名 | `PascalCase` | `UserId = string`, `UserMap` |
| 枚举 | `PascalCase` | `OrderStatus`, `ThemeMode` |
| 枚举成员 | `PascalCase` | `OrderStatus.Pending` |
| 泛型参数 | 单大写字母 | `T`, `K`, `V` |
| 私有成员 | `#camelCase` | `#cache`, `#internalState` |
| 私有方法 | `_camelCase` (仅限 TS 无原生私有时) | `_parseRaw()` |

### 7.2 函数动词规范

```typescript
function getUserById(id: string): Promise<User>
function listUsers(): User[]
function searchContent(query: string): Result[]
function createOrder(data: OrderInput): Order
function updateProfile(data: ProfileInput): void
function deleteComment(id: string): void
function saveSettings(settings: Settings): void

// 事件处理
function handleSubmit(): void
function onSearchInput(value: string): void

// 布尔
function isActive(user: User): boolean
function hasRole(user: User, role: string): boolean
function canEdit(resource: Resource): boolean
```

### 7.3 接口 / 类型

```typescript
// 禁止 I 前缀
interface UserProfile { }     // ✓
interface IUserProfile { }    // ✗

// 禁止无意义的 Type 后缀（业务类型除外）
type UserId = string          // ✓
type AppConfig = { }          // ✓
type UserType = { }           // ✗ 除非这就是业务"类型"
```

### 7.4 枚举

```typescript
// 字符串枚举优先（可读 + 可调试）
enum OrderStatus {
    Pending = 'pending',
    Confirmed = 'confirmed',
    Completed = 'completed',
}

// 数字枚举用 const object
const UserType = { Normal: 1, Admin: 2 } as const
type UserType = (typeof UserType)[keyof typeof UserType]
```

---

## 8. Vue 组件命名规范

### 8.1 组件名

- **文件名**: `PascalCase`，如 `UserProfileCard.vue`
- **始终多词**：避免与 HTML 原生元素冲突（`Header` → `AppHeader`）
- **基础组件**: `Base` 前缀，如 `BaseButton.vue`, `BaseModal.vue`
- **单例组件**: `The` 前缀，如 `TheHeader.vue`, `TheSidebar.vue`
- **页面组件**: `Page` 后缀，如 `LoginPage.vue`, `HomePage.vue`
- **`name` 选项**: 与文件名一致，`PascalCase`

### 8.2 Props / Emits

```vue
<script setup lang="ts">
// Props: camelCase
const props = defineProps<{
    userId: string
    isEditable?: boolean
    maxItems?: number
}>()

// Emits: kebab-case
const emit = defineEmits<{
    'user-click': [userId: string]
    'form-submit': [data: FormData]
}>()
</script>

<!-- 模板中传 Props: kebab-case -->
<UserCard :user-id="id" :is-editable="true" />
```

### 8.3 Composables / Stores

```typescript
// 文件名: camelCase, use 前缀
useAuthStatus.ts
usePagination.ts

// 导出函数: camelCase
export function useAuthStatus() { }

// Store: use 前缀 + Store 后缀
export const useUserStore = defineStore('user', () => { })
```

### 8.4 路由

```typescript
// 路径: kebab-case，复数
{ path: '/user-settings', name: 'UserSettings', component: UserSettingsPage }
{ path: '/articles/:id', name: 'ArticleDetail', component: ArticleDetailPage }

// 路由 name: PascalCase
// 路径: 全小写 + 连字符 + 复数资源名
```

---

## 9. CSS / SCSS 命名规范

### 9.1 类名

BEM 方法论 + kebab-case：

```css
.block {}                       /* 组件 */
.block__element {}              /* 子元素 */
.block--modifier {}             /* 状态变体 */
.block__element--modifier {}    /* 子元素状态 */

/* 示例 */
.user-card {}
.user-card__avatar {}
.user-card__name {}
.user-card--featured {}
.user-card--loading {}
```

### 9.2 CSS 自定义属性

```css
:root {
    /* 颜色: 语义化 + 层级 */
    --color-primary: #ec4899;
    --color-primary-hover: #db2777;
    --color-primary-light: rgba(236, 72, 153, 0.1);
    --color-bg: #18181b;
    --color-bg-secondary: #27272a;
    --color-text: #f4f4f5;
    --color-text-secondary: #a1a1aa;
    --color-text-muted: #71717a;
    --color-border: rgba(255, 255, 255, 0.08);
    --color-success: #22c55e;
    --color-warning: #f59e0b;
    --color-error: #ef4444;
    --color-info: #3b82f6;

    /* 字体: t-shirt 大小 */
    --font-size-xs: 0.75rem;
    --font-size-sm: 0.875rem;
    --font-size-base: 1rem;
    --font-size-lg: 1.125rem;
    --font-size-xl: 1.25rem;
    --font-size-2xl: 1.5rem;
    --font-size-3xl: 1.875rem;

    /* 间距 */
    --spacing-xs: 0.25rem;
    --spacing-sm: 0.5rem;
    --spacing-md: 1rem;
    --spacing-lg: 1.5rem;
    --spacing-xl: 2rem;

    /* 圆角 */
    --radius-sm: 4px;
    --radius-md: 8px;
    --radius-lg: 12px;
    --radius-xl: 16px;
    --radius-full: 9999px;

    /* z-index */
    --z-dropdown: 100;
    --z-sticky: 200;
    --z-overlay: 300;
    --z-modal: 400;
    --z-toast: 500;
}
```

### 9.3 动画

```css
/* kebab-case */
@keyframes fade-in { }
@keyframes slide-up { }
@keyframes card-enter { }
```

### 9.4 响应式断点

```css
/* 统一断点值 */
/* xs: 360px, sm: 480px, md: 768px, lg: 1024px, xl: 1280px, 2xl: 1536px */

@media (max-width: 768px) { }   /* 移动端 */
@media (min-width: 769px) { }   /* 桌面端 */
```

---

## 10. 文件与目录命名规范

### 10.1 通用规则

| 规则 | 说明 |
|------|------|
| 全小写 | 跨平台兼容 |
| 无空格 | 连字符或下划线 |
| 无特殊字符 | `a-z`, `0-9`, `-`, `_`, `.` |
| 扩展名小写 | `.py`, `.ts`, `.vue` |

### 10.2 Python 项目标准结构

```
project_root/
├── src/{project_name}/         # 源码
│   ├── api/                    # API 层
│   │   ├── routes.py
│   │   └── endpoints/
│   ├── models/                 # 数据模型
│   ├── services/               # 业务逻辑
│   ├── repositories/           # 数据访问层
│   ├── utils/                  # 工具
│   └── config.py               # 配置
├── tests/
│   ├── unit/
│   └── integration/
├── migrations/                 # 数据库迁移
├── docs/
├── scripts/
└── pyproject.toml
```

### 10.3 前端项目标准结构

```
project_root/
├── public/                     # 静态资源
├── src/
│   ├── assets/                 # 构建资源
│   │   ├── images/
│   │   ├── fonts/
│   │   └── styles/
│   ├── components/             # 组件
│   │   ├── base/               # 基础组件
│   │   └── business/           # 业务组件
│   ├── composables/            # Composables
│   ├── layouts/                # 布局
│   ├── pages/                  # 页面
│   ├── router/                 # 路由
│   ├── stores/                 # 状态管理
│   ├── api/                    # API 调用
│   ├── types/                  # 类型定义
│   └── utils/                  # 工具
├── tests/
├── index.html
├── vite.config.ts
└── tsconfig.json
```

### 10.4 特殊文件

| 文件 | 说明 |
|------|------|
| `NAMING_CONVENTION.md` | 命名规范（人版，每项目一份） |
| `NAMING_CONVENTION_AI.md` | 命名规范（AI 浓缩版） |
| `README.md` | 项目说明 |
| `CHANGELOG.md` | 更新日志 |
| `.env.example` | 环境变量示例（无真实密钥） |
| `.gitignore` | Git 忽略规则 |
| `.editorconfig` | 编辑器配置 |

---

## 11. API 命名规范

### 11.1 URL 路径

```
格式: /api/{version}/{resource}[/{id}][/{sub-resource}]
```

**规则**:

1. **全小写 + 连字符**（kebab-case）
2. **资源用复数名词**
3. **动作用 HTTP 方法表达**，不在 URL 里写动词
4. **嵌套不超过两层**

```
GET    /api/v1/articles              → 列表
GET    /api/v1/articles/123          → 详情
POST   /api/v1/articles              → 创建
PUT    /api/v1/articles/123          → 全量更新
PATCH  /api/v1/articles/123          → 部分更新
DELETE /api/v1/articles/123          → 删除

POST   /api/v1/articles/123/like     → 非 CRUD（动词在末尾）
POST   /api/v1/auth/login            → 认证
POST   /api/v1/auth/logout           → 登出

✗ POST /api/v1/articles/create
✗ GET  /api/v1/getAllArticles
```

### 11.2 查询参数与请求体

```
查询参数: camelCase
?pageSize=20&sortBy=createdAt&sortOrder=desc

请求体/响应体: camelCase (JSON)
{
    "userId": "123",
    "articleTitle": "...",
    "isPublished": true,
    "createdAt": "2026-01-01T00:00:00Z"
}
```

### 11.3 统一响应结构

```json
{
    "code": 0,
    "message": "success",
    "data": { },
    "requestId": "uuid"
}
```

### 11.4 HTTP 状态码

| 状态码 | 场景 |
|--------|------|
| 200 | 成功 |
| 201 | 创建成功 |
| 204 | 删除成功（无返回体） |
| 400 | 请求参数错误 |
| 401 | 未认证 |
| 403 | 无权限 |
| 404 | 资源不存在 |
| 409 | 冲突 |
| 422 | 参数验证失败 |
| 429 | 频率限制 |
| 500 | 服务器错误 |
| 503 | 服务暂不可用 |

---

## 12. Docker 命名规范

### 12.1 镜像命名

```
格式: librarydream/{service}:{version}
示例: librarydream/api:2.0.0
      librarydream/web:2.0.0
      librarydream/worker:2.0.0
```

- 仓库名前缀统一为 `librarydream`（Docker Hub 用户名或私有仓库命名空间）
- 服务名全小写，多用单词（不用下划线或连字符）
- 版本号用语义化版本，额外可用 `latest` 和 `stable`
- 基础镜像是例外：如 `python:3.12-slim`, `node:20-alpine`

### 12.2 容器命名

```
格式: ld-{project}-{service}
示例: ld-blog-api
      ld-blog-web
      ld-blog-redis
      ld-blog-mysql
```

### 12.3 网络命名

```
格式: ld-{project}-net
示例: ld-blog-net
```

### 12.4 卷命名

```
格式: ld-{project}-{data_name}
示例: ld-blog-mysql-data
      ld-blog-redis-data
      ld-blog-uploads
```

### 12.5 Compose 服务名

```yaml
services:
  api:         # 不重复 project 名（Compose 会自动加前缀）
  web:
  mysql:
  redis:
```

### 12.6 Dockerfile 中的 stage 命名

```dockerfile
# stage 名全小写
FROM node:20-alpine AS builder
FROM python:3.12-slim AS runtime
```

---

## 13. 环境变量命名规范

### 13.1 格式

```
格式: LD_{SERVICE}_{KEY}
示例: LD_API_DATABASE_URL
      LD_WEB_API_BASE_URL
      LD_WORKER_REDIS_URL
```

- 品牌前缀 `LD_`，全大写 + 下划线
- 第二段为服务名（API, WEB, WORKER 等）
- 后续为具体配置项

### 13.2 通用环境变量

| 变量 | 说明 |
|------|------|
| `LD_ENV` | 运行环境: `development`, `staging`, `production` |
| `LD_DEBUG` | 调试模式: `true`, `false` |
| `LD_LOG_LEVEL` | 日志级别: `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `LD_TIMEZONE` | 时区: `Asia/Shanghai` |

### 13.3 数据库相关

```
LD_API_DATABASE_URL=mysql://user:pass@host:3306/ld_blog
LD_API_DATABASE_POOL_SIZE=20
LD_API_REDIS_URL=redis://host:6379/0
LD_API_REDIS_MAX_CONNECTIONS=50
```

### 13.4 环境变量文件

```
.env                      # 本地开发（不提交 git）
.env.example              # 模板（提交 git，无真实密钥）
.env.staging              # 预发布
.env.production           # 生产

.env 中的格式: KEY=VALUE（无 export，无引号，无空格）
```

---

## 14. 日志命名规范

### 14.1 日志文件

```
格式: {project}_{date}.log          -- 普通日志
      {project}_error_{date}.log    -- 错误日志
      {project}_access_{date}.log   -- 访问日志

示例: blog_2026-07-17.log
      blog_error_2026-07-17.log
      blog_access_2026-07-17.log
```

### 14.2 日志级别

| 级别 | 用途 |
|------|------|
| `DEBUG` | 调试信息，仅开发环境 |
| `INFO` | 关键业务流程节点 |
| `WARNING` | 潜在问题，不影响运行 |
| `ERROR` | 错误但应用可继续 |
| `CRITICAL` | 致命错误，应用可能停止 |

### 14.3 日志格式约定

```python
# 结构化日志格式
{
    "timestamp": "2026-07-17T10:30:00+08:00",
    "level": "INFO",
    "service": "ld-blog-api",
    "request_id": "uuid",
    "user_id": "123",
    "action": "create_order",
    "message": "订单创建成功",
    "duration_ms": 45
}
```

**日志命名字段**:
- `timestamp`: ISO 8601 格式
- `level`: 日志级别
- `service`: 服务名
- `request_id`: 请求追踪 ID
- `user_id`: 操作用户 ID
- `action`: 操作名称 `snake_case`
- `duration_ms`: 耗时（毫秒）

---

## 15. Git 命名规范

### 15.1 分支

```
格式: {type}/{description}
示例: feature/user-login, fix/order-timeout, release/2.0.0
```

| 前缀 | 用途 |
|------|------|
| `feature/` | 新功能 |
| `fix/` | Bug 修复 |
| `hotfix/` | 紧急修复 |
| `release/` | 发布准备 |
| `refactor/` | 重构 |
| `docs/` | 文档 |
| `chore/` | 杂务 |
| `test/` | 测试 |

### 15.2 Commit

```
格式: {type}({scope}): {description}
示例: feat(user): add login with email
      fix(order): resolve timeout after 30s
      refactor(auth): extract token logic to service
```

| 类型 | 说明 |
|------|------|
| `feat` | 新功能 |
| `fix` | Bug 修复 |
| `refactor` | 重构 |
| `docs` | 文档 |
| `style` | 格式 |
| `test` | 测试 |
| `chore` | 构建/工具链 |
| `perf` | 性能 |

### 15.3 Tag

```
格式: v{major}.{minor}.{patch}
示例: v2.0.0
```

---

## 16. 魔数禁止规范

### 16.1 什么是魔数

直接出现在代码中的、没有明确含义的数字字面量。

### 16.2 必须提取的魔数

```python
# ✗ 坏
if user_type == 1: pass
if retry_count >= 3: raise Error()
if len(password) < 8: raise Error()
time.sleep(5 * 60)

# ✓ 好
class UserType(IntEnum):
    NORMAL = 1
    ADMIN = 2

MAX_RETRY_COUNT = 3
MIN_PASSWORD_LENGTH = 8
CACHE_TTL_SECONDS = 5 * 60

if user_type == UserType.NORMAL: pass
if retry_count >= MAX_RETRY_COUNT: raise Error()
if len(password) < MIN_PASSWORD_LENGTH: raise Error()
time.sleep(CACHE_TTL_SECONDS)
```

### 16.3 不需要提取的场景

```python
# 数学常量
circumference = 2 * 3.14159 * radius

# 循环索引
for i in range(10): pass

# 空值判断
if count == 0: pass
if items: pass        # 而不是 len(items) > 0
```

### 16.4 数据库中的魔数

```sql
-- ✗ 坏
SELECT * FROM user WHERE user_type = 1;

-- ✓ 好: 应用层参数化
SELECT * FROM user WHERE user_type = :normal_user_type;

-- ✓ 好: 或使用查找表
CREATE TABLE user_type (id TINYINT UNSIGNED PRIMARY KEY, code VARCHAR(20), name VARCHAR(50));
```

### 16.5 CSS 中的魔数

```css
/* ✗ 坏 */
.card { border-radius: 12px; margin-bottom: 16px; font-size: 14px; }

/* ✓ 好 */
.card {
    border-radius: var(--radius-lg);
    margin-bottom: var(--spacing-md);
    font-size: var(--font-size-sm);
}
```

---

## 17. 配置与常量管理规范

### 17.1 存放位置

| 常量类型 | 位置 | 示例 |
|----------|------|------|
| 应用配置 | `.env` + `config.py` | `LD_DATABASE_URL` |
| 业务枚举 | `constants.py` 或 `models/enums.py` | `UserType`, `OrderStatus` |
| 数值限制 | `constants.py` | `MAX_PAGE_SIZE = 100` |
| 功能开关 | `.env` 或配置中心 | `LD_FEATURE_NEW_UI=false` |
| API 端点 | `api/endpoints.ts` 或类似 | `API_BASE_URL` |
| CSS 令牌 | `theme.css` | `--color-primary` |
| 错误码 | `errors.py` 或 `error_codes.py` | `ERR_USER_NOT_FOUND = 1001` |

### 17.2 枚举值间距

业务枚举值使用间隔 10，方便未来插入：

```python
class OrderStatus(IntEnum):
    PENDING = 10
    CONFIRMED = 20
    PROCESSING = 30
    SHIPPED = 40
    DELIVERED = 50
    CANCELLED = 60
    REFUNDED = 70
```

### 17.3 错误码规范

```
格式: {MODULE}_{NUMBER}
示例: USER_001, ORDER_003, AUTH_010

模块: 3-5 字符大写
编号: 3 位数字
```

---

## 18. 版本号规范

### 18.1 语义化版本

```
格式: v{major}.{minor}.{patch}
示例: v2.4.3

major: 不兼容的 API 修改
minor: 新功能（向后兼容）
patch: Bug 修复（向后兼容）
```

**LibraryDream 特殊规则**:
- 每次修改版本号 +0.1，封顶 x.x.9
- x.x.9 之后进位到 x.{x+1}.0
- 版本号必须同步更新到项目文档中

### 18.2 版本号同步位置

每个项目至少保持以下位置的版本号一致：
1. 项目配置文件中的 `APP_VERSION`
2. 前端的版本展示（如有）
3. `CHANGELOG.md` 更新日志
4. 前端更新记录页（如有）
5. 项目修改记录文档

---

## 19. 附录

### 附录 A: MySQL 保留字速查

以下为高频冲突的 MySQL 保留字，**禁止**作为表名或字段名：

```
ADD, ALL, ALTER, AND, AS, ASC, BETWEEN, BY, CASE, CHECK,
COLUMN, CREATE, DATABASE, DATE, DEFAULT, DELETE, DESC,
DESCRIBE, DISTINCT, DROP, ELSE, END, EXISTS, FOREIGN, FROM,
GRANT, GROUP, HAVING, IN, INDEX, INSERT, INTO, IS, JOIN,
KEY, LIKE, LIMIT, NOT, NULL, ON, OR, ORDER, PRIMARY,
REFERENCES, SELECT, SET, SHOW, TABLE, THEN, TO, UNION,
UNIQUE, UPDATE, USE, VALUES, VIEW, WHERE
```

如必须使用，反引号包裹：`` `desc` ``，但强烈建议换名。

### 附录 B: 命名反模式对照表

| 反模式 | 正确做法 |
|--------|----------|
| `get_data()` | `get_user_profile()` |
| `process()` | `process_payment()` |
| `handle()` | `handle_error()` |
| `check()` | `is_valid_email()` |
| `temp`, `tmp` | `intermediate_result` |
| `result` | `search_results`, `parse_result` |
| `array`, `list` | `user_ids`, `items` |
| `flag`, `status` | `is_loading`, `order_status` |
| `class1`, `class2` | 语义区分 |
| `new_`, `old_` | `updated_user`, `original_user` |
| `data1`, `data2` | 语义区分 |

### 附录 C: 工具推荐

| 工具 | 用途 |
|------|------|
| sqlfluff | SQL Linter |
| ruff | Python Linter + Formatter |
| ESLint + Prettier | JS/TS 规范 |
| Stylelint | CSS 规范 |
| commitlint | Commit 规范 |
| husky | Git Hooks |

---

> *"命名是编程中最难的事之一。一个好的名字能让代码像一本打开的书；一个坏的名字则需要读者不断地翻阅上下文才能理解。"*

---

**本规范版本**: 2.0.0  
**最后更新**: 2026-07-17  
**维护者**: LibraryDream Team
