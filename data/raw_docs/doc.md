```markdown
# 用户管理系统 API 接口文档 v1.0

## 1. 基础信息
- **Base URL:** `https://api.example.com`
- **Content-Type:** `application/json`
- **默认超时时间:** 5s

## 2. 认证说明
部分接口需要鉴权。
- **方式:** Bearer Token
- **Header:** `Authorization: Bearer {your_token_here}`

---

## 3. 接口列表

### 3.1 用户注册 (User Register)
创建新用户，验证字段约束。

- **URL:** `/api/v1/users/register`
- **Method:** `POST`
- **认证:** 否

#### 请求参数 (Body - JSON)
| 字段名 | 类型 | 必填 | 描述 | 约束条件 |
| :--- | :--- | :--- | :--- | :--- |
| username | string | 是 | 用户名 | 长度 5-20 位，仅限字母数字 |
| password | string | 是 | 密码 | 长度 >= 8，必须包含大写字母 |
| email | string | 是 | 邮箱 | 必须符合 Email 格式 |
| age | integer | 否 | 年龄 | 范围 18 - 100 |

#### 响应示例 (成功 - 200)
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "user_id": 1001,
    "username": "demo_user",
    "created_at": "2023-10-01T12:00:00Z"
  }
}

```

#### 响应示例 (失败 - 400)

```json
{
  "code": 400,
  "message": "Invalid parameter: password must contain at least one uppercase letter"
}

```

---

### 3.2 用户登录 (User Login)

验证身份并获取访问 Token。

* **URL:** `/api/v1/auth/login`
* **Method:** `POST`
* **认证:** 否

#### 请求参数 (Body - JSON)

| 字段名 | 类型 | 必填 | 描述 |
| --- | --- | --- | --- |
| username | string | 是 | 用户名 |
| password | string | 是 | 密码 |

#### 响应示例 (200)

```json
{
  "code": 200,
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.e30.Et9...",
    "expires_in": 3600
  }
}

```

---

### 3.3 查询用户信息 (Get User Info)

获取指定用户的详情数据。

* **URL:** `/api/v1/users/{user_id}`
* **Method:** `GET`
* **认证:** 是 (Need Token)

#### 请求参数 (Path)

| 字段名 | 类型 | 必填 | 描述 |
| --- | --- | --- | --- |
| user_id | integer | 是 | 目标用户 ID |

#### 请求参数 (Query)

| 字段名 | 类型 | 必填 | 描述 | 示例 |
| --- | --- | --- | --- | --- |
| detail | boolean | 否 | 是否返回详细日志 | true / false (默认 false) |

#### 响应示例 (200)

```json
{
  "code": 200,
  "data": {
    "user_id": 1001,
    "username": "demo_user",
    "email": "demo@test.com",
    "role": "user",
    "last_login": "2023-10-20"
  }
}

```

#### 响应示例 (404)

```json
{
  "code": 404,
  "message": "User not found"
}

```

---

### 3.4 删除用户 (Delete User)

注销用户账号，仅限管理员操作。

* **URL:** `/api/v1/users/{user_id}`
* **Method:** `DELETE`
* **认证:** 是 (Admin Token)

#### 请求参数 (Path)

| 字段名 | 类型 | 必填 | 描述 |
| --- | --- | --- | --- |
| user_id | integer | 是 | 待删除的用户 ID |

#### 响应示例 (204)

*(无响应体)*

```

```