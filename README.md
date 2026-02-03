# AutoLLM-TestFramework

基于大模型的智能接口自动化测试框架。覆盖“文档解析 → 用例生成 → 执行 → 报告”的半自动化流程，并支持 AI 语义断言。

## 核心能力

- 文档驱动：从接口文档自动生成标准 JSON 用例
- 数据驱动：基于 Pytest 动态参数化执行
- AI 语义断言：`AIJudge` 支持 `semantic_match`
- 报告输出：兼容 Allure 报告

## 目录结构

- [config/settings.yaml](config/settings.yaml)
- [config/prompt_templates.yaml](config/prompt_templates.yaml)
- [data/raw_docs](data/raw_docs)
- [data/test_cases](data/test_cases)
- [src/core](src/core)
- [src/llm_client](src/llm_client)
- [src/utils](src/utils)
- [test_runner](test_runner)
- [run.py](run.py)

## 关键流程

1. `CaseGenerator` 读取文档并调用 LLM 生成测试用例
2. `pytest_generate_tests` 自动加载用例并参数化
3. `AIJudge.verify()` 进行断言
4. 可选输出 Allure 报告

## 示例用例亮点

- 模糊匹配场景：预期“搜索结果应包含手机相关商品”，返回包含 iPhone/Xiaomi/Phone Case，AI 判定 True
- 异常场景：注册邮箱校验自动生成 `""` / `"abc"` / `"@@@"` 等负向用例

## 注意事项

- 需要在 [config/settings.yaml](config/settings.yaml) 配置 LLM Key 与 Base URL
- Allure 报告需要单独安装 Allure CLI

## 快速开始

请阅读 [START.md](START.md)
