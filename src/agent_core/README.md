# agent_core

## 概述

本目录实现了一个 Agentic 循环：从文档切片生成测试用例，评审后若不通过则带反馈重试。核心角色如下：

- `AgentGenerator`：基于切片内容与可选评审反馈生成用例。
- `AgentJudge`：评审用例质量，返回通过/不通过与反馈文本。
- `AgentOrchestrator`：编排生成-评审循环，控制重试次数与 fail_fast 行为。

## 逻辑简述

1. `AgentOrchestrator.run()` 读取重试配置（`max_rounds`、`fail_fast`）。
2. 每一轮：
   - `AgentGenerator.generate()` 组装提示词，将切片与反馈交给 LLM 生成用例。
   - 将 LLM 输出解析为 JSON 用例列表（支持 JSON 与 JSON5）。
   - `AgentJudge.review()` 评审生成用例并返回结果。
3. 通过则直接返回；不通过则把反馈传入下一轮。
4. `fail_fast` 为真时首轮失败立即退出。

## 调用图（txt）

```text
                         +---------------------------+
                         |                           |
                         | AgentOrchestrator.run     |
                         +-------------+-------------+
                                       |
                         +-------------+-------------+
                         |                           |
                         V                           V
               +--------------------+      +--------------------+
               | AgentGenerator     |      | AgentJudge         |
               | .generate          |      | .review            |
               +---------+----------+      +---------+----------+
                         |                           |
                         V                           V
               +--------------------+      +--------------------+
               | LLMClient          |      | LLMClient          |
               | .chat_completion   |      | .chat_completion   |
               +---------+----------+      +---------+----------+
                         |
                         V
               +--------------------+
               | _extract_json      |
               +---------+----------+
                         |
                         V
               +--------------------+
               | _parse_json        |
               +---------+----------+
                         |
                         V
               +--------------------+
               | cases (List[Dict]) |
               +---------+----------+
                         |
                         V
               +--------------------+
               | (Pass?)            |
               +----+---------+-----+
                    |         |
                    | Pass    | Fail
                    V         V
             +------+---+  +--+----------------------+
             | return |  | feedback -> next round    |
             +--------+  | (or stop if fail_fast)    |
                         +---------------------------+
```
