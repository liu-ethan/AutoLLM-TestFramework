# 运行说明

## 1. 环境依赖

- Python 3.10+
- 已配置可访问的 LLM 服务
- 可选：如需使用 LangChain 切片器，额外安装 langchain

## 2. 安装依赖

在项目根目录执行：

pip install -r requirements.txt

如需使用 LangChain 切片器：

pip install langchain

## 3. 配置项说明

- [config/settings.yaml](config/settings.yaml)
	- llm: api_key / base_url / model
	- llm_profiles: 多模型档位配置（small/large）
	- llm_modules: 模块到模型档位的映射
	- rag: enabled / header_levels / output_per_chunk / min_content_length / include_keywords / exclude_keywords
	- agentic: enabled / max_rounds / max_rounds_by_module / fail_fast
	- global_vars: enabled / path
	- auth: login_url / username / password / token_prefix / auto_refresh_token
	- execution: auto_inject_token / auth_header_name
- [config/prompt_templates.yaml](config/prompt_templates.yaml)
	- generation_prompt / agent_generation_prompt
	- judge_prompt / agent_judge_prompt
- [config/global_vars.yaml](config/global_vars.yaml)
	- 全局变量池（账号、通用请求头、base_url 等）

## 4. 准备接口文档

将接口说明文档放入 [data/raw_docs](data/raw_docs)

## 5. 生成用例（含 RAG + Agentic）

python run.py --mode generate

或指定单个文档：

python run.py --mode generate --doc data/raw_docs/your_doc.md

生成结果默认写入 [data/test_cases](data/test_cases)，如开启 output_per_chunk 会按模块拆分文件。

如果需要过滤非正文模块（LICENSE/示例/接口类型等），请配置 rag.include_keywords 与 rag.exclude_keywords。

## 6. 执行测试（含 Token 注入）

python run.py --mode run

如需自动获取 Token：

- 在 [config/settings.yaml](config/settings.yaml) 填写 auth 配置
- 将 execution.auto_inject_token 设为 true

## 6.1 多模型配置示例

在 [config/settings.yaml](config/settings.yaml) 中设置：

llm_profiles:
	small:
		model: "gpt-4o-mini"
	large:
		model: "gpt-5.2"

llm_modules:
	case_generator: "small"
	agent_generator: "small"
	agent_judge: "large"
	ai_judge: "large"

## 6.2 Agentic 循环次数配置示例

agentic:
	max_rounds: 3
	max_rounds_by_module:
		default: 3
		agentic_loop: 3

## 7. 一键生成与执行

python run.py --mode all

如需 Allure 报告，请先安装 Allure CLI，随后使用：

allure generate allure-results -o allure-report --clean

allure serve allure-results

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
- use_auth: true 或 false（可选，控制单条用例是否注入 Token）
