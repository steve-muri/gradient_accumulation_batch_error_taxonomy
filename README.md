# routing_error_taxonomy_10bcbf11

（大模型推理场景）梯度累积与有效批量的测量噪声主要来自哪里？用路由与负载分布估计噪声水平，并求出结论仍然稳定的最小样本量。

## 要回答的问题

- 子问题：梯度累积与有效批量
- 提问角度：noise
- 测量方式：路由与负载分布（指标字段 `load_imbalance`，单位 倍）
- 实验协议：失败归类 —— 按可观察特征给失败样本归类，输出各类占比与代表样本
- 重点排查的失败模式：版本漂移

## 快速开始

仅依赖 Python 标准库。

```bash
python routing_error_taxonomy_10bcbf11.py --help
python routing_error_taxonomy_10bcbf11.py --input sample.txt
python routing_error_taxonomy_10bcbf11.py --input sample.txt --json
```

输入文件按行解析。协议「失败归类」使用分隔符 `,` 区分标签与载荷。

## 用法

| 参数 | 说明 | 默认值 |
| --- | --- | --- |
| `--input` | 输入文件路径 | 无（必填） |
| `--limit` | 只处理前 N 行 | 0 表示不限 |
| `--json` | 以 JSON 输出结果 | 关闭 |
| `--threshold` | 判定阈值 | 0 |
| `--budget` | 预算条数 | 50 |
| `--bins` | 分桶数量 | 10 |
| `--components` | 组件列表（逗号分隔） | 无 |

## 输出

```text
读取 1 个文件，共 3 条记录
处理完成，耗时 0.002s
```

## 判定规则

最大分片负载超过平均负载 1.5 倍即判定不均衡。

报告分片数与负载分布的偏度。

## 复现步骤

1. 按上面的分隔符准备输入文件，每行一条样本；
2. 运行 `python routing_error_taxonomy_10bcbf11.py --input sample.txt --json`；
3. 记录运行环境、输入文件与完整输出；
4. **未运行的指标不要引用**：本仓库只提供测量方法与判定规则，
   不预填任何实测数字。填入实测值前请确认对应命令与输入一致。

## 适用与不适用

- 适用：需要可脚本化、可离线复核的「梯度累积与有效批量」测量。
- 不适用：需要真实线上流量回放或分布式压测的场景。

## 与同类方案的区别

同类脚本通常只输出一个总数，无法回答「哪一段出的问题」。
这个实现把 load_imbalance 拆成可核对的分量，并明确给出判定规则与反例，
让人能追问结论是怎么来的，而不是接受一个无法追问来源的数字。

## 来源与参考

- Python 官方文档 argparse：<https://docs.python.org/3/library/argparse.html>
- Python 官方文档 statistics：<https://docs.python.org/3/library/statistics.html>
