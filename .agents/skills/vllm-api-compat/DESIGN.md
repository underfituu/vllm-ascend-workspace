# vllm-api-compat Skill 设计文档

## 背景与动机

vLLM 上游社区持续向 `vllm serve` CLI 添加新参数。vllm-ascend 作为 vLLM 在华为昇腾 NPU 上的适配层，无法保证所有上游参数在 Ascend 上行为正常——某些参数可能导致启动崩溃、行为异常，或根本未实现。

手工维护兼容性矩阵成本高、易遗漏。`vllm-api-compat` 的目标是将这个过程自动化：

- 对每个已知 CLI 参数，在真实 Ascend 环境中跑一次最小化验证
- 每日拉取上游 PR，自动发现新参数并纳入测试
- 对 Ascend 特有失败，自动生成 fix stub 并通过 `auto-commit-pr` 提 PR

---

## 整体设计思路

核心思路是「逐参数隔离测试」：每次只在 baseline 启动命令上叠加一个被测参数，启动真实的 `vllm serve` 进程，通过 HTTP 健康检查和推理请求来判定是否 PASS。

这样做的好处：

- 参数之间互不干扰，失败可精确归因到单个参数
- 不依赖 vLLM 的单元测试框架，直接测运行时行为
- 结果 JSON 可被外部系统消费（CI、PR bot、Agent 工作流）

日常运转由 `daily_check.py` 驱动，形成一个闭环：

```
拉取 upstream PR → 检测新参数 → 追加到 YAML → 跑 cli.py 测试 → 写 fix stub → 提 PR
```

---

## 目录结构

```
.agents/skills/vllm-api-compat/
├── SKILL.md                        # Skill 说明与入口点文档
├── summary.json                    # Skill 元信息
├── scripts/
│   ├── cli.py                      # 主测试入口
│   ├── daily_check.py              # 每日例行任务
│   ├── bench_test.py               # 压测入口
│   ├── _common.py                  # 共享工具库
│   └── test_build_args.py          # build_extra_args_simple 的单元测试
└── references/
    ├── params_simple.yaml           # 参数定义（所有测试的数据源）
    ├── serve_cli.md                 # vllm serve --help=all 的完整转录
    ├── serve_cli_params.csv         # 参数表（CSV 格式）
    ├── behavior.md                  # 测试生命周期和 PASS/FAIL 定义
    ├── acceptance.md                # 验收标准
    └── command-recipes.md           # 常用命令速查

.vaws-local/vllm-api-compat/         # 本地运行时状态，untracked
├── daily/
│   ├── state.json                   # 上次运行时间和最高 PR 号
│   └── fixes/                       # fix stub，每个失败参数一个 .md
└── params.yaml                      # daily_check 维护的动态参数注册表
```

---

## 核心组件说明

### `cli.py` — 主测试入口

按 `params_simple.yaml` 中定义的 section/param 顺序，逐一执行测试生命周期。支持：

- `--nodes all` 全量测试或 `--nodes single --section X` 按 section 过滤
- `--param=--flag-name` 测单个参数，`--test-value true` 按值过滤
- `--param=--json-config.subfield` 点号语法支持 JSON 配置参数的子字段测试
- `--bench` 在每个 PASS 之后追加压测
- `--accuracy` 用 temperature=0 与 baseline 输出做文本对比
- `--rerun-failed SUMMARY_JSON` 从上次的 summary.json 中提取 FAIL 条目重跑

最终结果输出到 stdout（JSON），进度输出到 stderr。每个参数的结果实时 upsert 到 `results/summary.json`，支持中断恢复。

### `daily_check.py` — 每日例行

1. 读取 `state.json` 中的上次最高 PR 号
2. 调用 GitHub API 拉取 `vllm-project/vllm` 中比该号更新的已合并 PR
3. 扫描 PR diff，匹配 `add_argument("--param-name", ...)` 模式，检测新增 CLI 参数
4. 从 diff 上下文推断参数类型（bool_flag / Enum / int / float / str）、section 归属和测试值
5. 将新参数追加到 `.vaws-local/vllm-api-compat/params.yaml`
6. 调用 `cli.py --nodes all` 跑全量测试
7. 对包含 Ascend 关键词（`NotImplementedError`、`AscendError`、`npu`、`torch_npu`、`cann`）的 FAIL 结果，写 fix stub 到 `daily/fixes/`
8. 如存在 fix stub，调用 `auto-commit-pr` skill 提 PR
9. 更新 `state.json`

需要环境变量 `GITHUB_TOKEN`。支持 `--dry-run` 只检测不测试。

### `bench_test.py` — 压测

启动 `vllm serve` 后运行 `vllm bench serve`，解析输出中的关键指标（`output_throughput`、`mean_ttft_ms`、`mean_tpot_ms` 等）。支持 `--skip-serve` 连接已运行的服务。此脚本用于 API 兼容性维度的基本可用性压测，不是精确性能基准（那是 `vllm-ascend-benchmark` skill 的职责）。

### `_common.py` — 共享工具库

封装的核心操作：

- **进程管理**：`_kill_existing_vllm()` 清理残留进程 → `start_vllm_serve()` 启动子进程（process group 隔离、日志重定向） → `stop_vllm_serve()` SIGTERM → 10s → SIGKILL → 等待后代进程退出 → 等待 NPU 内存释放
- **健康检查**：`wait_for_ready()` 每 2s 轮询 `/health`
- **推理验证**：`send_completion_request()` POST `/v1/completions`，校验 `choices` 字段
- **精度对比**：`send_accuracy_request()` + `compare_accuracy()` 发 temperature=0 请求，逐 prompt 对比文本
- **参数构建**：`build_extra_args_simple()` 将 YAML 条目转换为 CLI 参数列表，支持 bool flag、子字段 JSON 配置、依赖参数注入
- **Bench 解析**：`run_bench()` 调用 `vllm bench serve` 并解析 JSON 或表格输出

---

## 测试流程

每个参数的完整生命周期：

```
1. kill 现有 vllm 进程 → 等待 NPU 内存释放（npu-smi 确认）

2. 启动 vllm serve：
   vllm serve <model> --port <auto> <baseline_args> <tested_param> [deps]

3. 轮询 GET /health，每 2s 一次，超时判 FAIL

4. POST /v1/completions {"model":"...","prompt":"Hello","max_tokens":1}
   校验响应含 choices 字段

5. （可选，--bench）运行 vllm bench serve，记录吞吐/延迟

6. （可选，--accuracy）temperature=0 发多个 prompt，与 baseline 输出做文本对比

7. SIGTERM → 10s grace → SIGKILL 停止服务
   等待后代进程退出 + NPU 内存释放
```

**判定规则**：

| 状态 | 条件 |
|------|------|
| PASS | `/health` 返回 200 且 `/v1/completions` 返回含 `choices` 的有效 JSON |
| FAIL | 启动崩溃、健康超时、HTTP 非 200、JSON 无效或缺字段 |
| SKIP | 参数无法独立测试（如 `--ssl-certfile` 需要真实证书） |

---

## 参数注册机制

所有被测参数定义在 `references/params_simple.yaml`，按 section 组织：

```yaml
GlobalOptions:
  baseline:                          # 该 section 的基础启动命令
  - /home/weights/Qwen3-0.6B
  - --data-parallel-size 2
  - --tensor-parallel-size 2
  - --seed 1024
  - --served-model-name qwen
  - --max-num-seqs 28
  - --max-model-len 16384
  - --trust-remote-code
  - --gpu-memory-utilization 0.8
  params:
  - name: --disable-log-stats        # bool flag
    test_value: true
  - name: --enable-auto-tool-choice  # 有依赖参数
    test_value: true
    deps:
      --tool-call-parser: qwen3_coder
  - name: --structured-outputs-config  # JSON 子字段
    subfields:
    - name: disable_any_whitespace
      test_value: true
      deps:
        backend: xgrammar
```

关键设计点：

- **每个 section 独立 baseline**：不同 section 可用不同的模型和启动参数组合
- **deps 字段**：声明被测参数生效所需的前置参数，测试时自动注入
- **subfields 支持**：JSON 配置类参数（如 `--structured-outputs-config`）通过点号语法测试内部子字段
- **双向 bool 测试**：有 `--no-` 变体的参数会分别测 `--flag` 和 `--no-flag`

新参数来源：

1. 手工追加到 `params_simple.yaml`
2. `daily_check.py` 自动从 upstream PR diff 检测并追加到 `.vaws-local/vllm-api-compat/params.yaml`

---

## 日志与状态

### 日志目录

```
<log-path>/                  (默认 ./server-api-log)
├── accuracy/<section>/      # baseline.json + <param_key>.json
├── bench/<section>/         # <param_key>.log
├── results/<section>/       # <param_key>.json (单参数结果)
│   └── summary.json         # 所有参数的聚合结果（upsert 模式）
└── serve/<section>/         # <param_key>_stdout.log (vllm 进程输出)
```

`summary.json` 按 `(section, param, test_value)` 三元组去重 upsert，支持增量运行。

### 状态文件

`.vaws-local/vllm-api-compat/daily/state.json`：

```json
{"last_pr_number": 12345, "last_run": "2026-06-09T10:00:00Z"}
```

### 进度协议

进度事件输出到 **stderr**：

```
__VAWS_VLLM_API_COMPAT_PROGRESS__={"phase":"test","message":"GlobalOptions / --disable-log-stats=true","param":"--disable-log-stats","port":39521}
```

最终 JSON 结果输出到 **stdout**，便于管道消费和 Agent 解析。

---

## 使用示例

```bash
# 环境准备
export ASCEND_RT_VISIBLE_DEVICES=0,1,2,3
export PYTHONPATH="/path/to/vllm:$PYTHONPATH"

# 跑全量测试
python3 .agents/skills/vllm-api-compat/scripts/cli.py \
  --host localhost --nodes all --timeout 400

# 只测某个 section
python3 .agents/skills/vllm-api-compat/scripts/cli.py \
  --host localhost --nodes single --section GlobalOptions --timeout 400

# 只测某个参数的某个值
python3 .agents/skills/vllm-api-compat/scripts/cli.py \
  --host localhost --nodes single --section GlobalOptions \
  --param=--disable-log-stats --test-value true --timeout 400

# 测 JSON 子字段
python3 .agents/skills/vllm-api-compat/scripts/cli.py \
  --host localhost --nodes single --section VllmConfig \
  --param=--structured-outputs-config.disable_any_whitespace --timeout 400

# 带压测
python3 .agents/skills/vllm-api-compat/scripts/cli.py \
  --host localhost --nodes single --section GlobalOptions \
  --param=--disable-log-stats --test-value true \
  --bench --bench-num-prompts 10 --bench-concurrency 4

# 重跑上次失败的用例
python3 .agents/skills/vllm-api-compat/scripts/cli.py \
  --host localhost --rerun-failed ./server-api-log/results/summary.json

# 每日例行（dry run）
GITHUB_TOKEN=ghp_... python3 .agents/skills/vllm-api-compat/scripts/daily_check.py \
  --model Qwen/Qwen3-0.6B --dry-run
```

---

## 边界与限制

| 约束 | 说明 |
|------|------|
| 仅限本地执行 | 所有测试在当前机器上启动进程，不 SSH 到远程 Ascend 节点 |
| 需要真实 Ascend NPU | 无法在 x86 CPU 环境模拟，`ASCEND_RT_VISIBLE_DEVICES` 必须正确设置 |
| 串行执行 | 参数逐个测试，每个需完整启停 `vllm serve`，全量测试耗时较长 |
| 仅覆盖 bool 参数 | `params_simple.yaml` 目前以 bool flag 为主，非 bool 参数需手工标注或 SKIP |
| 不做精确性能基准 | bench 模式仅做基本可用性压测，精确 benchmark 用 `vllm-ascend-benchmark` skill |
| 不管理机器和代码 | 机器管理用 `machine-management`，代码同步用 `remote-code-parity` |
| daily_check 需要 GITHUB_TOKEN | 且通过 GitHub REST API 拉取 PR，受 rate limit 约束 |
