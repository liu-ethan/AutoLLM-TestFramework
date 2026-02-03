```markdown
# 农产品销售系统 API 接口文档 v1.0

## 1. 基础信息
- **Base URL:** `http://localhost:1234/api/user`
- **Content-Type:** `application/json`
- **通用响应格式:** ```json
  {
    "code": "0",    // "0" 表示成功，非 "0" 表示业务失败
    "msg": "提示信息",
    "data": {}      // 返回的数据负载
  }

```

## 2. 认证说明

* **方式:** 建议使用 JWT (Bearer Token)
* **Header:** `Authorization: {token}`

---

## 3. 接口列表

### 3.1 用户登录 (User Login)

验证身份并返回用户信息或 Token。

* **URL:** `/login`
* **Method:** `POST`
* **认证:** 否

以下是一个正确的用户名和密码：
```json
{
  username: "test_usr123",
  password: "123456",
}
```

#### 请求参数 (Body - JSON)

| 字段名 | 类型 | 必填 | 描述 |
| --- | --- | --- | --- |
| username | string | 是 | 用户名 |
| password | string | 是 | 密码 |

#### 响应示例 (成功 - 200)

```json
{
  "code": "0",
  "msg": "成功",
  "data": {
    "id": 1,
    "username": "admin",
    "role": "ADMIN"
  }
}

```

---

### 3.2 分页查询用户 (Get Users By Page)

根据多维度条件筛选并进行分页查询。

* **URL:** `/page`
* **Method:** `GET`
* **认证:** 是

#### 请求参数 (Query)

| 字段名 | 类型 | 必填 | 默认值 | 描述 |
| --- | --- | --- | --- | --- |
| username | string | 否 | "" | 用户名模糊查询 |
| name | string | 否 | "" | 姓名模糊查询 |
| role | string | 否 | "" | 角色过滤 |
| status | string | 否 | "" | 状态过滤 |
| currentPage | integer | 否 | 1 | 当前页码 |
| size | integer | 否 | 10 | 每页行数 |

#### 响应示例 (成功 - 200)

```json
{
  "code": "0",
  "data": {
    "records": [...],
    "total": 50,
    "size": 10,
    "current": 1
  }
}

```

---

### 3.3 创建新用户 (Create User)

新增系统用户。

* **URL:** `/add`
* **Method:** `POST`
* **认证:** 是

#### 请求参数 (Body - JSON)

| 字段名 | 类型 | 必填 | 描述 |
| --- | --- | --- | --- |
| username | string | 是 | 用户名 |
| password | string | 是 | 密码 |
| email | string | 是 | 邮箱 |
| role | string | 是 | 角色 |

#### 响应示例 (失败 - 业务异常)

```json
{
  "code": "-1",
  "msg": "用户名已存在" // 或 "邮箱已存在！"
}

```

---

### 3.4 修改密码 (Update Password)

用户通过旧密码验证后修改新密码。

* **URL:** `/password/{id}`
* **Method:** `PUT`
* **认证:** 是

#### 请求参数 (Path)

| 字段名 | 类型 | 必填 | 描述 |
| --- | --- | --- | --- |
| id | integer | 是 | 用户 ID |

#### 请求参数 (Body - JSON)

| 字段名 | 类型 | 必填 | 描述 |
| --- | --- | --- | --- |
| oldPassword | string | 是 | 旧密码 |
| newPassword | string | 是 | 新密码 |

---

### 3.5 忘记密码/重置 (Forget Password)

通过邮箱验证重置密码。

* **URL:** `/forget`
* **Method:** `GET`
* **认证:** 否

#### 请求参数 (Query)

| 字段名 | 类型 | 必填 | 描述 |
| --- | --- | --- | --- |
| email | string | 是 | 注册邮箱 |
| newPassword | string | 是 | 新密码 |

---

### 3.6 删除用户 (Delete)

#### 单个删除

* **URL:** `/delete/{id}`
* **Method:** `DELETE`

#### 批量删除

* **URL:** `/deleteBatch`
* **Method:** `DELETE`
* **Query Params:** `ids` (示例: `?ids=1,2,3`)

#### 业务错误响应 (针对删除操作)

| code | msg |
| --- | --- |
| -1 | 删除失败,请检查关联商家 |
| -2 | 删除失败，请检查关联库存 |

---

### 3.7 基础查询接口 (Basic Queries)

| 功能 | URL | Method | 描述 |
| --- | --- | --- | --- |
| 获取详情 | `/{id}` | GET | 根据 ID 查询用户信息 |
| 按名查询 | `/username/{username}` | GET | 根据用户名精确查询 |
| 按角色查询 | `/role/{role}` | GET | 获取该角色下的用户列表 |
| 获取全部 | `/` | GET | 返回所有用户列表 (不分页) |

```