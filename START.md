# 运行说明

## 1. 环境准备

- Python 3.10+
- 已配置可访问的 LLM 服务

## 2. 安装依赖

在项目根目录执行：

pip install -r requirements.txt

## 3. 配置

- 编辑 [config/settings.yaml](config/settings.yaml) 配置 api_key、base_url、model
- 编辑 [config/prompt_templates.yaml](config/prompt_templates.yaml) 调整提示词

## 4. 准备接口文档

将接口说明文档放入 [data/raw_docs](data/raw_docs)

## 5. 生成用例

python run.py --mode generate

或指定单个文档：

python run.py --mode generate --doc data/raw_docs/your_doc.md

## 6. 执行测试

python run.py --mode run

## 7. 一键生成与执行

python run.py --mode all

如需 Allure 报告，请先安装 Allure CLI，随后使用：

allure generate allure-results -o allure-report --clean

## 8. 用例格式约定

- name: 用例名称
- url: 完整请求 URL
- method: HTTP 方法
- headers: 请求头对象
- params: 查询参数对象
- data: 请求体对象
- expected: 预期结果
- assert_type: exact_match 或 semantic_match
- use_ai_assertion: true 或 false
