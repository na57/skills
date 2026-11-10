#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
laya-mcp：把云南大学 new-api 网关的 laya (System One) 决策接口封装为 MCP 工具。

System One 接口调用方式（2026-11 算力资产清查时验证可用）：
  POST https://new-api-itc.ynu.edu.cn/v1/systemone
  Headers: Authorization: Bearer <NEWAPI_KEY> / Content-Type: application/json
  Body:    {"model": "laya", "state": "<待判定文本>",
            "questions": {"<题名>": {"type": "choice", "instructions": "<题干>",
                                     "criteria": {"<选项>": "<选项含义>", ...}}}}
  响应:    {"answers": {"<题名>": {"choice": "<最优选项>",
                                   "probabilities": {"<选项>": 0.x, ...},
                                   "answer_confidence": "..."}}}
要点：一次请求可带多道选择题；返回每题完整概率分布；实测 24 并发稳定。

工具：
  - laya_ask          通用：对任意 state 提自定义选择题组
  - laya_judge_asset  高层：判定单个资产是否算力设备（GPU卡/图形工作站/带显卡的服务器或台式机）
  - laya_judge_assets 批量版（单次上限 200 条，内部并发）

运行：uv run --with "mcp<2" <本目录>/server.py
鉴权：环境变量 NEWAPI_KEY（new-api 令牌，sk- 开头），必须设置
"""
import json
import os
import re
import time
import urllib.request
import urllib.error
import concurrent.futures
from typing import Any

from mcp.server.fastmcp import FastMCP

URL = 'https://new-api-itc.ynu.edu.cn/v1/systemone'
MODEL = 'laya'
KEY = os.environ.get('NEWAPI_KEY', '')
TIMEOUT = 60
BATCH_LIMIT = 200

# 算力资产判定：两道固定选择题（与算力资产清查口径一致）
ASSET_QUESTIONS = {
    'category': {
        'type': 'choice',
        'instructions': 'What kind of asset is this?',
        'criteria': {
            'graphics_card': 'a GPU graphics card itself',
            'computer': 'a desktop, laptop, workstation or server computer',
            'peripheral': 'a printer, monitor, scanner, projector, camera or similar device',
            'other': 'furniture, appliance, network device, tool or anything else',
        },
    },
    'has_gpu': {
        'type': 'choice',
        'instructions': 'Does the equipment include a discrete GPU graphics card?',
        'criteria': {
            'includes_gpu': 'the text mentions a graphics card or a GPU model like RTX, GTX, Tesla, V100, A100, Quadro, Radeon',
            'no_gpu_info': 'no graphics card or GPU model is mentioned',
        },
    },
}

# 名称中含 GPU 关键词时才把型号并入判定文本（避免无关型号干扰）
GPU_TOKEN = re.compile(
    r'(RTX|GTX|TESLA|A\d{3,4}|V100|P40|P100|P4\b|M40|K80|QUADRO|NVIDIA|'
    r'GEFORCE|RADEON|3090|3080|3070|3060|4090|4080|4070|5090|5080|L40|H100|H20|910B|'
    r'显卡|GPU)', re.I)

# 关键词命中即算力（品牌/型号完整 token，防子串误报）
KW = re.compile(
    r'(?<![A-Za-z0-9])(?:NVIDIA|GEFORCE|QUADRO|TESLA|RADEON|910B|V100|P100|P40'
    r'|A100|A800|A40|L40|L20|H100|H800|H20|GPU|HPC)(?![A-Za-z0-9])'
    r'|(?<![A-Za-z0-9])(?:RTX|GTX)(?:[\s\-]?\d{3,5})?'
    r'|显卡|图形工作站|图形加速|深度学习|高性能计算',
    re.I)

mcp = FastMCP('laya', instructions='云南大学 laya (System One) 决策模型：对文本提出选择题组并返回概率分布')


def call_systemone(state: str, questions: dict, model: str = MODEL,
                   tries: int = 3) -> dict:
    """调用 System One 接口，失败重试（指数退避），返回原始 answers。"""
    body = json.dumps({'model': model, 'state': state, 'questions': questions}).encode()
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(URL, data=body, headers={
                'Authorization': f'Bearer {KEY}',
                'Content-Type': 'application/json',
                'User-Agent': 'laya-mcp/1.0',
            })
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                return json.loads(r.read())
        except Exception as e:
            last = e
            time.sleep(1.5 * (i + 1))
    raise RuntimeError(f'laya 请求失败: {last}')


def build_state(name: str, brand: str = '', model_no: str = '') -> str:
    state = name.strip()
    if brand.strip():
        state += f' | brand: {brand.strip()}'
    if model_no.strip() and GPU_TOKEN.search(model_no):
        state += f' | model: {model_no.strip()}'
    return state


@mcp.tool()
def laya_ask(state: str, questions: dict[str, Any], model: str = MODEL) -> dict:
    """向 laya (System One) 提交一段状态文本和自定义选择题组。

    Args:
        state: 待判定的文本（如设备名称+品牌+型号、一段描述等）。
        questions: 选择题组，形如
            {"is_risky": {"type": "choice", "instructions": "题干",
                          "criteria": {"yes": "选项含义", "no": "选项含义"}}}
            type 目前为 "choice"；criteria 的 key 是选项名。
        model: 模型名，默认 laya。

    Returns:
        {"answers": {"<题名>": {"choice": ..., "probabilities": {...},
                                "answer_confidence": ...}}}
    """
    if not state or not questions:
        return {'success': False, 'error': 'state 和 questions 均不能为空'}
    try:
        d = call_systemone(state, questions, model)
        return {'success': True, 'state': state, 'answers': d.get('answers', d)}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def judge_one(name: str, brand: str, model_no: str, threshold: float) -> dict:
    state = build_state(name, brand, model_no)
    kw = bool(KW.search(state))
    d = call_systemone(state, ASSET_QUESTIONS)
    ans = d['answers']
    gpu = ans['has_gpu']
    cat = ans['category']
    p_gpu = gpu['probabilities']['includes_gpu']
    probs = cat['probabilities']
    cat_top = cat['choice']
    is_compute = kw or p_gpu >= threshold
    return {
        'state': state,
        'is_compute': is_compute,
        'keyword_hit': kw,
        'p_gpu': round(p_gpu, 4),
        'category': cat_top,
        'category_probabilities': {k: round(v, 4) for k, v in probs.items()},
        'confidence': cat.get('answer_confidence'),
    }


@mcp.tool()
def laya_judge_asset(name: str, brand: str = '', model: str = '',
                     threshold: float = 0.45) -> dict:
    """判定单个资产是否属于算力设备（GPU卡、图形工作站、带独显的服务器/台式机）。

    口径与算力资产清查一致：名称/品牌/型号命中 GPU 关键词，或 laya 判定
    "含独立显卡" 的概率 >= threshold（默认 0.45）即为算力。

    Args:
        name: 资产名称（中文即可）。
        brand: 品牌名（可选）。
        model: 型号规格（可选，仅当其中含 GPU 关键词时才并入判定文本）。
        threshold: has_gpu 概率阈值，默认 0.45。

    Returns:
        {success, state, is_compute, keyword_hit, p_gpu, category,
         category_probabilities, confidence}
    """
    if not name or not name.strip():
        return {'success': False, 'error': 'name 不能为空'}
    try:
        r = judge_one(name, brand, model, threshold)
        return {'success': True, **r}
    except Exception as e:
        return {'success': False, 'error': str(e)}


@mcp.tool()
def laya_judge_assets(items: list[dict], threshold: float = 0.45,
                      concurrency: int = 8) -> dict:
    """批量判定资产是否算力设备（单次上限 200 条，内部并发调用 laya）。

    Args:
        items: [{"id": 可选标识, "name": 资产名, "brand": 品牌(可选),
                 "model": 型号(可选)}]
        threshold: has_gpu 概率阈值，默认 0.45。
        concurrency: 并发数，默认 8，建议不超过 24。

    Returns:
        {success, total, computed, failed, results: [{id, ...判定字段, error?}]}
    """
    if not items:
        return {'success': False, 'error': 'items 不能为空'}
    if len(items) > BATCH_LIMIT:
        return {'success': False, 'error': f'单次最多 {BATCH_LIMIT} 条，请分批调用'}
    concurrency = max(1, min(concurrency, 24))

    results: list[dict] = [None] * len(items)

    def work(i: int, it: dict):
        name = (it.get('name') or '').strip()
        base = {'id': it.get('id', i), 'name': name}
        if not name:
            return base | {'success': False, 'error': 'name 为空'}
        try:
            r = judge_one(name, it.get('brand') or '', it.get('model') or '', threshold)
            return base | {'success': True, **r}
        except Exception as e:
            return base | {'success': False, 'error': str(e)}

    with concurrent.futures.ThreadPoolExecutor(concurrency) as ex:
        futs = {ex.submit(work, i, it): i for i, it in enumerate(items)}
        for f in concurrent.futures.as_completed(futs):
            results[futs[f]] = f.result()

    ok = sum(1 for r in results if r and r.get('success'))
    return {'success': True, 'total': len(items), 'computed': ok,
            'failed': len(items) - ok, 'results': results}


if __name__ == '__main__':
    mcp.run()
