# nvzhuang

Python + Vue 的桌面应用，使用 `pywebview` 承载前端界面。

当前包含两类能力：
- Tabcut 商品排名数据抓取
- 基于 `flow2api` 的荷塘图片生成

## 功能

### 数据抓取
- 从 Tabcut 抓取商品排名数据
- 地区、类目、默认数量由后端统一提供
- 抓取结果保存到 `data/` 目录
- 每次抓取会生成独立目录，包含：
  - `items/`：商品 JSON
  - `images/`：商品图片目录
  - `summary.json`：抓取汇总

### 荷塘图片生成
- 仅使用荷塘配置的图片模型
- 通过 `flow2api` 的 OpenAI 兼容图片接口调用
- 生成结果保存到 `data/generated_images/`
- 接口返回值为生成文件的本地路径

## 页面说明

- `首页`：占位首页
- `数据抓取`：执行 Tabcut 数据抓取
- `调试`：调试工具页，当前包含多个 tab
  - `荷塘生图`：测试荷塘图片生成
  - `接口说明`：查看当前调试接口说明
  - `结果记录`：查看本次运行内的生成记录
- `设置`：
  - 抓取配置
  - 荷塘配置
  - 日志

## 荷塘配置

在“设置”页面的“荷塘配置”中填写：

- `Base URL`
- `Model`
- `API Key`

示例模型：

```text
gemini-3.0-pro-image-landscape
```

默认请求地址为：

```text
<Base URL>/v1/images/generations
```

## 目录结构

```text
.
├── backend/
│   ├── main.py                   # pywebview 入口与前后端桥接
│   ├── crawler.py                # Tabcut 抓取逻辑
│   ├── crawl_metadata.py         # 抓取类目、地区等元数据
│   ├── generators.py             # 图片/视频生成器父类
│   ├── hotang_image_generator.py # 荷塘图片生成器
│   ├── logger.py                 # 日志
│   ├── settings_store.py         # 本地设置存储
│   └── vue/                      # 编译后的前端资源
├── frontend/
│   ├── src/views/
│   │   ├── Home.vue
│   │   ├── Crawler.vue
│   │   ├── Debug.vue
│   │   └── Settings.vue
│   └── ...
├── data/                         # 抓取结果、日志、生成图片
├── requirements.txt
└── run.sh
```

## 运行

需要安装：

- [uv](https://github.com/astral-sh/uv)
- Node.js

启动：

```bash
chmod +x run.sh
./run.sh
```

脚本会自动：

1. 创建 Python 虚拟环境 `/.venv`
2. 安装 Python 依赖
3. 安装前端依赖
4. 编译前端到 `frontend/dist`
5. 复制前端产物到 `backend/vue`
6. 启动桌面应用

## 数据输出

### 抓取结果目录

抓取结果会输出到类似下面的目录：

```text
data/2026-04-23-231500-女装与女士内衣-US/
```

目录内通常包含：

```text
items/
images/
summary.json
```

### 荷塘生成结果目录

```text
data/generated_images/
```

## 备注

- 前端展示的抓取类目和地区不再硬编码，统一从后端获取
- 荷塘图片生成当前只实现了图片生成链路，没有接入视频生成
- 荷塘生图已移动到“调试”页面的 tab 中
- 如果你的 `flow2api` 部署对请求字段有额外要求，需要再按实际接口格式调整
