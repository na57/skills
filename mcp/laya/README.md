# laya MCP

把云南大学 new-api 网关的 **laya (System One) 决策接口**封装为 MCP server，供 Trae / Claude 等 MCP 客户端直接调用。对任意文本提出选择题组，返回带概率分布的判定结果。

## 工具列表

| 工具 | 用途 |
|------|------|
| `laya_ask` | 通用：对一段 state 文本提交自定义选择题组，返回每题最优选项与完整概率分布 |
| `laya_judge_asset` | 判定单个资产是否属于算力设备（GPU 卡、图形工作站、带独显的服务器/台式机） |
| `laya_judge_assets` | 批量判定（单次上限 200 条，内部并发 1-24） |

## System One 接口调用格式

```
POST https://new-api-itc.ynu.edu.cn/v1/systemone
Headers:
  Authorization: Bearer <NEWAPI_KEY>
  Content-Type: application/json

Body:
{
  "model": "laya",
  "state": "Dell PowerEdge R740 | brand: Dell | model: Tesla V100",
  "questions": {
    "has_gpu": {
      "type": "choice",
      "instructions": "该设备是否包含独立显卡？",
      "criteria": {
        "includes_gpu": "提到了显卡或 GPU 型号",
        "no_gpu_info": "没有提到显卡"
      }
    }
  }
}

响应:
{
  "answers": {
    "has_gpu": {
      "choice": "includes_gpu",
      "probabilities": {"includes_gpu": 0.83, "no_gpu_info": 0.17},
      "answer_confidence": "high"
    }
  }
}
```

要点：一次请求可携带多道选择题；返回每题完整概率分布；实测 24 并发稳定。

## 安装与配置

依赖 [uv](https://docs.astral.sh/uv/)（Python MCP SDK 必须钉版 `mcp<2`，2.x 的 FastMCP 已改名 MCPServer）。

**必须**通过环境变量 `NEWAPI_KEY` 提供 new-api 令牌（`sk-` 开头），代码中不内置任何密钥。

在 MCP 客户端配置文件（如 Trae 的 `mcp.json`）中注册：

```json
{
  "laya": {
    "command": "/path/to/uv",
    "args": ["run", "--with", "mcp<2", "/path/to/skills/mcp/laya/server.py"],
    "env": { "NEWAPI_KEY": "sk-你的new-api令牌" }
  }
}
```

> 注意：默认端点为校内地址，需校园网 / VPN 环境访问；其他用户需自行持有 new-api 平台的令牌。

## 算力判定口径

`laya_judge_asset` / `laya_judge_assets` 采用双通道判定（与算力资产清查一致）：

1. **关键词命中**：名称/品牌/型号命中 GPU 关键词（NVIDIA、RTX、V100、A100、H100、显卡、图形工作站 等），直接判为算力；
2. **模型判定**：laya 判定「包含独立显卡」的概率 `p_gpu >= threshold`（默认 0.45）。

细节：
- 型号（model 字段）仅当其本身含 GPU 关键词时才并入判定文本，避免无关型号干扰；
- state 构造格式：`名称 | brand: 品牌 | model: 型号`；
- 批量接口单次最多 200 条，`concurrency` 默认 8、上限 24。

## 快速验证

```bash
cd mcp/laya
NEWAPI_KEY=sk-你的令牌 uv run --with "mcp<2" python -c "
import server
print(server.judge_one('Dell R740 | model: Tesla V100', '', '', 0.45))
"
```

输出中 `is_compute: true`、`p_gpu` 接近 0.8 即配置成功。
