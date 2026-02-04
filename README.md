# AutoLLM-TestFramework

基于大模型的智能接口自动化测试框架。覆盖“文档解析 → 用例生成 → 执行 → 报告”的半自动化流程，并支持 AI/非 AI 双模式断言与动态化 Allure 报告。

## 核心能力

- 文档驱动：从接口文档自动生成标准 JSON 用例
- 数据驱动：基于 Pytest 动态参数化执行
- 语义断言：支持 AI 判定与非 AI 启发式判定
- 报告输出：支持 Allure 结果与报告生成
- 动态标签：基于用例字段自动注入 feature/story/title

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

1. [src/core/case_generator.py](src/core/case_generator.py) 读取文档并调用 LLM 生成测试用例
2. [test_runner/conftest.py](test_runner/conftest.py) 自动加载用例并参数化
3. [src/core/ai_judge.py](src/core/ai_judge.py) 执行断言（AI 或非 AI 模式）
4. [run.py](run.py) 驱动 Pytest 并生成 Allure 报告

## 用例字段规范

生成的 JSON 用例应包含以下字段：

- title: 用例标题（报告展示）
- module: 模块名（Allure feature）
- story: 功能名（Allure story）
- name: 用例名称（可与 title 相同）
- url / method / headers / params / data
- expected / assert_type / use_ai_assertion

提示词模板见 [config/prompt_templates.yaml](config/prompt_templates.yaml)。

## Allure 报告逻辑

- 运行测试时：Pytest 写入 Allure 结果目录（allure-results）
- 测试结束后：调用 Allure CLI 生成报告目录（allure-report）
- 用例执行时：动态注入 feature/story/title

入口位置：

- 结果写入： [run.py](run.py#L14-L38)
- 报告生成： [run.py](run.py#L40-L63)
- 动态标签： [test_runner/test_executor.py](test_runner/test_executor.py#L18-L56)

### AutoLLM-TestFramework 项目架构

```text
                    +---------------------------+
                    |       CLI 入口: run.py     |
                    +-------------+-------------+
                                  |
                          { 模式选择 (Mode) }
            ____________/         |         \____________
           /                      |                      \
    [ generate ]               [ all ]                  [ run ]
         |                        |                        |
         V                        V                        V
+-------------------+      +--------------+      +-----------------------+
|   CaseGenerator   | <----+ 一键全流程模式 +----> | pytest + test_executor |
+---------+---------+      +--------------+      +-----------+-----------+
          |                                                  |
    +-----+-----+           +----------------+         +-----+-----+
    | DocParser | --------> |    LLMClient   | <-------+  AIJudge  |
    +-----+-----+           +-------+--------+         +-----+-----+
          |                         |                        |
    +-----+-----+           +-------+--------+         +-----+-----+
    | Prompt模板|           | settings.yaml  |         |  requests |
    +-----------+           +----------------+         +-----+-----+
          |                                                  |
    +-----+-----+           +----------------+         +-----+-----+
    | 生成用例  | --------> |data/test_cases | <-------+ 参数化加载|
    +-----------+           +----------------+         +-----------+
                                                             |
                                                    +--------+--------+
                                                    | 动态 Allure 标签 |
                                                    | feature/story/title |
                                                    +--------+--------+
                                                             |
                                                       +-----+-----+
                                                       |allure-res |
                                                       +-----+-----+
                                                             |
                                                       +-----+-----+
                                                       |allure-repo|
                                                       +-----------+

 [ 辅助工具 ]
 +-----------------------+      +-----------------------+      +--------------------+
 | utils/logger (日志)    | <--> | utils/file (文件处理)  | <--> | json5 兼容解析      |
 +-----------------------+      +-----------------------+      +--------------------+

```

---

### 💡 核心链路解读

1. **生成链路**：从 `raw_docs` 开始，经过 `DocParser` 解析，配合 `prompt_templates.yaml` 的提示词，由 `LLMClient` 调用大模型生成 JSON 用例并存入 `data/test_cases`，支持 json5 兼容解析。
2. **执行链路**：`pytest` 自动加载 `data/test_cases` 下的 JSON 文件进行参数化测试，通过 `requests` 发送请求。
3. **判定链路**：`AIJudge` 根据配置选择 `semantic_match` 或 `exact_match`；当禁用 AI 时，使用启发式规则匹配响应内容。
4. **报告链路**：测试结果写入 `allure-results`，同时在执行阶段注入动态标签（feature/story/title），最终由 **Allure CLI** 生成 `allure-report`。


## 配置说明

在 [config/settings.yaml](config/settings.yaml) 中配置：

- LLM 连接参数（api_key/base_url/model）
- 路径配置（allure_results_dir/allure_report_dir）
- 执行配置（超时、SSL、默认断言模式）

## 快速开始

建议先阅读 [START.md](START.md)。常用命令：

- 仅生成用例：python run.py --mode generate --doc data/raw_docs/farm.md
- 仅执行用例：python run.py --mode run
- 生成 + 执行 + 报告：python run.py --mode all

## 注意事项

- 需要在 [config/settings.yaml](config/settings.yaml) 配置 LLM Key 与 Base URL
- Allure 报告需要单独安装 Allure CLI
- 若关闭 AI 断言（use_ai_assertion=false），将使用启发式语义匹配规则
