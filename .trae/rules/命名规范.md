# LibraryDream Naming Convention — AI Reference

> **Brand**: LibraryDream (图书馆之梦) | **Prefix**: `ld` / `LD_` | **Version**: 2.0.0  
> This document is the AI-optimized, token-efficient version. Every rule is a directive. No explanations.  
> For human-readable rationale, see `NAMING_CONVENTION.md`.

---

## QUICK INDEX
- 1. Universal Rules — 2. MySQL — 3. Redis — 4. Python — 5. TypeScript — 6. Vue — 7. CSS — 8. Files/Dirs — 9. API — 10. Docker — 11. Env Vars — 12. Logging — 13. Git — 14. No Magic Numbers — 15. Constants — 16. Versioning — 17. Forbidden Words

---

## 1. UNIVERSAL RULES (apply everywhere)

- **Case conventions per language — no mixing within a project.**
- **Clarity > Brevity.** `user_password` not `usr_pwd`. Exception: loop vars `i`, comprehension vars `u`.
- **No Hungarian notation.** `username` not `str_username`.
- **Positive boolean names.** `is_enabled` not `disabled`.
- **Symmetry.** `start/stop`, `open/close`, `addItem/removeItem`, `loadData/saveData`.
- **Forbidden generic words**: `data`, `info`, `temp`, `utils`, `helper`, `common`, `manager`, `handler`, `process`, `item`(non-generic), `flag`, `result`.

### Allowed Abbreviations
`id`, `url`, `api`, `db`, `sql`, `http`, `json`, `html`, `css`, `js`, `ts`, `ui`, `os`, `io`, `max`, `min`, `avg`, `num`(local), `src`, `dst`, `arg`, `args`, `param`, `params`, `ctx`, `req`, `res`(HTTP only), `msg`, `err`(except block), `cfg`(local), `init`, `sync`, `async`, `ttl`, `rpc`.

### Forbidden Abbreviations
`usr`, `pwd`, `txt`, `cnt`, `idx`(except MySQL), `ptr`, `obj`, `btn`, `lbl`, `tbl`, `cols`, `desc`, `stat`, `auth`, `mod`, `img`(dirs OK).

---

## 2. MySQL

### Database
```
ld_{project}
Charset: utf8mb4, Collation: utf8mb4_unicode_ci, Max 30 chars.
```

### Tables
```
snake_case, SINGULAR.  Max 50 chars.  No reserved words.
user, user_profile, article_comment    ✓
users, UserProfile, videoComment       ✗
M2M: {table_a}_{table_b} in alphabetical order.  e.g., role_user (R<U).
```

### Columns
```
{qualifier}_{property}
```

| Category | Pattern | Examples |
|----------|---------|----------|
| PK | `id` | `id` |
| FK | `{table}_id` | `user_id`, `article_id` |
| Boolean | `is_{adj}` | `is_active`, `is_deleted`, `is_verified` |
| Timestamp | `{action}_at` | `created_at`, `updated_at`, `deleted_at`, `published_at` |
| Date | `{action}_date` | `birth_date`, `expiry_date` |
| Status | `status` or `{type}_status` | `status`, `order_status` |
| Enum type | `{name}_type` | `user_type`, `media_type` |
| Count | `{thing}_count` | `view_count`, `comment_count` |
| Rate | `{thing}_rate` or `{thing}_ratio` | `completion_rate` |
| JSON | `{name}_data` | `settings_data`, `metadata_data` |
| Money | `{name}_amount` or `{name}_price` | `total_amount`, `unit_price` |
| Sort | `sort_order` | `sort_order` |
| Soft delete | `deleted_at` (TIMESTAMP NULL) | `deleted_at` |

**Column comment MANDATORY.** Status fields must list all values:
```sql
`user_type` TINYINT UNSIGNED NOT NULL DEFAULT 1 COMMENT '用户类型: 1=普通用户, 2=管理员'
```

**FK column name MUST match referenced table name.**
```sql
FOREIGN KEY (user_id) REFERENCES user(id)   ✓
FOREIGN KEY (owner) REFERENCES user(id)     ✗
```

### Indexes
```
{prefix}_{table}_{columns}
idx = normal, uk = unique, fk = foreign key, ft = fulltext, sp = spatial.
Composite: columns joined by _, highest-selectivity first.
idx_user_status_created, uk_order_user_product
```

### Views / Procedures / Functions / Triggers
```
v_{descriptive_name}                                    -- view
sp_{action}_{entity}                                    -- stored procedure
fn_{computation}                                        -- function
tr_{table}_{before|after}_{insert|update|delete}        -- trigger
```

### Migration Files
```
{YYYYMMDDHHMMSS}_{description}.sql
20260717083000_create_user_table.sql
```

### Data Types
- PK: `BIGINT UNSIGNED AUTO_INCREMENT` (never INT)
- UUID PK: `BINARY(16)` (saves 50% vs CHAR(36))
- Short text: `VARCHAR(N)` — N = actual max, not 255
- Long text: `TEXT`/`MEDIUMTEXT`/`LONGTEXT`
- Boolean: `TINYINT(1)` (never ENUM)
- Status enum: `TINYINT UNSIGNED` (never MySQL ENUM type)
- Timestamp: `TIMESTAMP`
- Money: `DECIMAL(M,D)` (never FLOAT/DOUBLE)
- Percentage: `DECIMAL(5,2)`
- JSON: `JSON` type (never TEXT)
- File path: `VARCHAR(500)` (files go to OSS)
- IP: `VARCHAR(45)` (IPv6 compatible)

---

## 3. Redis

### Key Format
```
ld:{project}:{category}:{entity}:{id}[:{attr}]
Separator: colon (:). All lowercase.
```

### Key Patterns by Purpose

| Purpose | Pattern | Example |
|---------|---------|---------|
| Cache | `ld:{p}:cache:{entity}:{id}` | `ld:blog:cache:article:123` |
| Cache sub-field | `ld:{p}:cache:{entity}:{id}:{attr}` | `ld:blog:cache:user:456:profile` |
| Session | `ld:{p}:session:{type}:{token}` | `ld:blog:session:access:abc` |
| Session by user | `ld:{p}:session:user:{uid}` | `ld:blog:session:user:789` |
| Distributed lock | `ld:{p}:lock:{resource}:{id}` | `ld:blog:lock:order:456` |
| Counter | `ld:{p}:counter:{entity}:{attr}` | `ld:blog:counter:article:view` |
| Counter periodic | `ld:{p}:counter:{entity}:{attr}:{period}` | `ld:blog:counter:article:view:daily` |
| Leaderboard | `ld:{p}:rank:{entity}:{period}` | `ld:blog:rank:article:weekly` |
| Queue | `ld:{p}:queue:{task_type}` | `ld:blog:queue:email` |
| Rate limit | `ld:{p}:ratelimit:{uid}:{action}` | `ld:blog:ratelimit:123:login` |
| Verification | `ld:{p}:verify:{type}:{target}` | `ld:blog:verify:email:x@y.com` |
| Temp data | `ld:{p}:temp:{purpose}:{id}` | `ld:blog:temp:import:batch_001` |
| Config | `ld:{p}:config:{key}` | `ld:blog:config:feature_flags` |
| Pub/Sub channel | `ld:{p}:channel:{event}` | `ld:blog:channel:order.created` |

### Key Rules
- Key length ≤ 512 chars.
- No dynamic prefixes. No raw user input in keys (hash first).
- Prefixes must be static and predictable.

### Data Structure Selection
- String: single-value cache, counters
- Hash: object with <100 fields, <1MB, frequent field-level reads
- List: queue/stack
- Set: dedup collections
- Sorted Set: leaderboards
- Stream: event sourcing
- Bitmap: check-in, online status
- Geo: proximity
- Pub/Sub: real-time notifications

### TTL (mandatory, never rely on defaults)

| Type | TTL |
|------|-----|
| Hot data cache | 60s–300s |
| Normal cache | 600s–3600s |
| Config cache | 3600s–86400s |
| Session | 7200s–86400s |
| Verification code | 300s–600s |
| Rate limit | per window |
| Distributed lock | ≤30s |
| Temp data | ≤3600s |

### Forbidden
- `KEYS *` → use `SCAN`
- `FLUSHDB`/`FLUSHALL` in production
- Big keys: String>10MB, collection>10000 without sharding
- Hot keys: single key QPS>1000 must be sharded
- Keys without TTL

---

## 4. Python

### Naming

| Element | Case | Example |
|---------|------|---------|
| module/file | `snake_case` | `user_service.py` |
| package/dir | `snake_case` | `api/`, `services/` |
| class | `PascalCase` | `UserRepository` |
| exception | `PascalCase` + `Error` | `ValidationError` |
| function/method | `snake_case` | `get_user_by_id()` |
| variable | `snake_case` | `user_id` |
| constant | `UPPER_SNAKE_CASE` | `MAX_RETRY_COUNT` |
| private member | `_snake_case` | `_cache` |
| internal private | `__snake_case` | `__internal_state` |
| enum member | `UPPER_SNAKE_CASE` | `Status.PENDING` |
| type alias | `PascalCase` | `JsonDict = dict[str, Any]` |

### Function Verbs
`get_`(single), `list_`(multiple), `search_`(with query), `create_`, `update_`, `delete_`, `save_`, `load_`, `parse_`, `validate_`, `convert_`, `fetch_`, `compute_`, `build_`.
Boolean: `is_`, `has_`, `can_`.

### Class Suffixes
`Repository`(data access), `Service`(business logic), `Config`/`Settings`(config), `Error`(exception), `Abstract`/`Base`(base classes).

### Enums
```python
from enum import IntEnum
class OrderStatus(IntEnum):
    PENDING = 10     # start from 1+, step 10
    CONFIRMED = 20
    COMPLETED = 30
```

### Import Order
```python
# 1. stdlib
# 2. third-party
# 3. project modules
```

---

## 5. TypeScript / JavaScript

| Element | Case | Example |
|---------|------|---------|
| variable | `camelCase` | `userId` |
| compile-time const | `UPPER_SNAKE_CASE` | `MAX_PAGE_SIZE` |
| runtime const | `camelCase` | `defaultPageSize` |
| function | `camelCase` | `getUserById()` |
| class | `PascalCase` | `UserApi` |
| interface | `PascalCase` | `UserProfile` |
| type alias | `PascalCase` | `UserId = string` |
| enum | `PascalCase` | `OrderStatus` |
| enum member | `PascalCase` | `OrderStatus.Pending` |
| generic param | single uppercase | `T`, `K`, `V` |
| private field | `#camelCase` | `#cache` |
| private method | `_camelCase` (no native #) | `_parseRaw()` |

### Rules
- **No `I` prefix on interfaces.** `UserProfile` not `IUserProfile`.
- **No `Type` suffix** unless it is a business "type" concept.
- **String enums preferred** (readable, debuggable). For numeric enums, use `const object + union type`.
- Event handlers: `handle` prefix for component events, `on` prefix for DOM events.
- Boolean functions: `is`, `has`, `can` prefix.
- Action verbs: `get`, `list`, `search`, `create`, `update`, `delete`, `save`, `load`, `parse`, `validate`.

---

## 6. Vue

### Components
- **File name**: `PascalCase`, always multi-word. `AppHeader.vue`, `UserProfileCard.vue`.
- **name option**: matches file name, `PascalCase`.
- **Base components**: `Base` prefix. `BaseButton.vue`.
- **Singleton components**: `The` prefix. `TheHeader.vue`.
- **Page components**: `Page` suffix. `LoginPage.vue`.

### Props: `camelCase` in `<script>`, `kebab-case` in `<template>`.
### Emits: `kebab-case`.
### Composables: `camelCase` file, `use` prefix function. `useAuthStatus.ts`.
### Stores: `camelCase` file, `use` prefix + `Store` suffix. `useUserStore`.
### Routes: path `kebab-case` + plural resources, name `PascalCase`.

```typescript
{ path: '/user-settings', name: 'UserSettings' }
{ path: '/articles/:id', name: 'ArticleDetail' }
```

---

## 7. CSS / SCSS

### Class Names: BEM + kebab-case
```css
.block {}
.block__element {}
.block--modifier {}
.block__element--modifier {}
```

### Custom Properties: `--kebab-case`, semantic naming.
```css
--color-primary, --color-bg, --color-text, --color-border
--font-size-xs|sm|base|lg|xl|2xl|3xl   (t-shirt sizes)
--spacing-xs|sm|md|lg|xl
--radius-sm|md|lg|xl|full
--z-dropdown(100)|sticky(200)|overlay(300)|modal(400)|toast(500)
```

### Animations: `kebab-case`. `@keyframes fade-in {}`
### Breakpoints: xs:360, sm:480, md:768, lg:1024, xl:1280, 2xl:1536.

---

## 8. Files & Directories

### Universal
- All lowercase. No spaces. Only `a-z`, `0-9`, `-`, `_`, `.`.
- Extensions lowercase: `.py`, `.ts`, `.vue`.

### Python Project Layout
```
src/{project_name}/
  api/ (routes.py, endpoints/)
  models/
  services/
  repositories/
  utils/
  config.py
tests/ (unit/, integration/)
migrations/ (YYYYMMDDHHMMSS_desc.sql)
```

### Frontend Project Layout
```
src/
  assets/ (images/, fonts/, styles/)
  components/ (base/, business/)
  composables/
  layouts/
  pages/
  router/
  stores/
  api/
  types/
  utils/
```

### Special Files
`NAMING_CONVENTION.md`, `NAMING_CONVENTION_AI.md`, `README.md`, `CHANGELOG.md`, `.env.example`, `.gitignore`, `.editorconfig`.

---

## 9. API

### URL Path
```
/api/v{version}/{resource}[/{id}][/{sub-resource}]
kebab-case, plural resources.
GET|POST|PUT|PATCH|DELETE — actions via HTTP method, NOT in URL.
Non-CRUD: POST /api/v1/articles/123/like
Nesting: max 2 levels. /api/v1/articles/123/comments ✓
```

### Query Params: `camelCase`. `?pageSize=20&sortBy=createdAt`
### JSON Keys: `camelCase`. `{ "userId": "123", "createdAt": "..." }`
### Response Envelope
```json
{ "code": 0, "message": "success", "data": {}, "requestId": "uuid" }
```
### HTTP Codes: 200, 201, 204, 400, 401, 403, 404, 409, 422, 429, 500, 503.

---

## 10. Docker

### Images: `librarydream/{service}:{version}` e.g. `librarydream/api:2.0.0`
### Containers: `ld-{project}-{service}` e.g. `ld-blog-api`
### Networks: `ld-{project}-net`
### Volumes: `ld-{project}-{data_name}` e.g. `ld-blog-mysql-data`
### Compose service names: short, no project prefix (Compose adds it).
### Dockerfile stages: all lowercase. `AS builder`, `AS runtime`.

---

## 11. Environment Variables

### Format: `LD_{SERVICE}_{KEY}` — all UPPER_SNAKE_CASE.
```
LD_API_DATABASE_URL=mysql://...
LD_API_REDIS_URL=redis://...
LD_WEB_API_BASE_URL=https://...
```

### Standard Vars
`LD_ENV`(development|staging|production), `LD_DEBUG`, `LD_LOG_LEVEL`, `LD_TIMEZONE`.

### Files
`.env`(local, gitignored), `.env.example`(template, committed), `.env.staging`, `.env.production`.

---

## 12. Logging

### Files: `{project}_{date}.log`, `{project}_error_{date}.log`, `{project}_access_{date}.log`.

### Levels: DEBUG, INFO, WARNING, ERROR, CRITICAL.

### Structured Log Format (JSON):
```json
{
  "timestamp": "ISO8601",
  "level": "INFO",
  "service": "ld-blog-api",
  "request_id": "uuid",
  "user_id": "123",
  "action": "snake_case_action_name",
  "duration_ms": 45
}
```

---

## 13. Git

### Branches: `{type}/{kebab-case-description}`
`feature/`, `fix/`, `hotfix/`, `release/`, `refactor/`, `docs/`, `chore/`, `test/`

### Commits: `{type}({scope}): {description}`
`feat`, `fix`, `refactor`, `docs`, `style`, `test`, `chore`, `perf`

### Tags: `v{major}.{minor}.{patch}`

---

## 14. NO MAGIC NUMBERS

- **Extract to named constants or enums.** User types, status codes, thresholds, TTLs — all must be named.
- **Enums**: start from 1, step 10. `class OrderStatus(IntEnum): PENDING=10`
- **SQL**: parameterize, never inline literals: `WHERE user_type = :normal_user_type`
- **CSS**: use variables: `var(--radius-lg)` not `12px`
- **Exceptions**: math constants, loop indices 0..N, `if count == 0` are OK.

---

## 15. Constants & Config Management

| Type | Location |
|------|----------|
| App config | `.env` + `config.py` |
| Business enums | `constants.py` or `models/enums.py` |
| Numeric limits | `constants.py` |
| Feature flags | `.env` or config center |
| API endpoints | dedicated constants file |
| CSS tokens | `theme.css` |
| Error codes | `errors.py` or `error_codes.py` |

**Error codes**: `{MODULE}_{NNN}` e.g. `USER_001`, `ORDER_003`. Module: 3-5 uppercase chars. Number: 3 digits.

---

## 16. Versioning

### SemVer: `v{major}.{minor}.{patch}`
### LibraryDream rule: each change +0.1, cap at x.x.9, then carry to x.{x+1}.0.
### Sync version in: config file, frontend display, CHANGELOG.md, changelog page, modification record.

---

## 17. NAMING ANTI-PATTERNS (quick reference)

| WRONG | RIGHT |
|-------|-------|
| `get_data()` | `get_user_profile()` |
| `process()` | `process_payment()` |
| `handle()` | `handle_error()` |
| `check()` | `is_valid_email()` |
| `temp`, `tmp` | `intermediate_result` |
| `result` | `search_results` |
| `flag` | `is_loading` |
| `new_`, `old_` | `updated_user`, `original_user` |

---

*End of AI Reference. For rationale and examples, see NAMING_CONVENTION.md.*
