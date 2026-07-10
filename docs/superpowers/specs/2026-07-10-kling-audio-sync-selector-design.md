# 可灵音画同步控件兼容设计

## 目标

修复可灵图生视频自动化在设置“音画同步”时因旧版 SVG 选择器不存在而超时的问题，确保失败发生在参数设置阶段之前不会阻塞生成流程。

## 范围

只调整 `backend/kling_video_generator.py` 中音画同步开关的检测与关闭逻辑，并为图标状态解析补充单元测试。不修改模型、清晰度、时长、上传、提交或任务轮询逻辑。

## 当前页面事实

当前页面使用如下控件结构：

```html
<div class="setting-switch">
  <svg icon-name="IconCheckboxCheckedSecondary">...</svg>
  音画同步
</div>
```

旧代码依赖 `.svg-icon use[xlink:href]`，该元素在当前页面不存在，因此 `get_attribute` 等待 30 秒后超时。

## 设计

1. 新增一个纯函数，将 `icon-name` 和旧版 `xlink:href` 解析为三态结果：开启、关闭或未知。
2. 优先读取当前页面的 `svg[icon-name]`：`IconCheckboxChecked*` 表示开启，`IconCheckboxUnchecked*` 表示关闭。
3. 为兼容旧页面，若当前属性不可用，则保留对 `xlink:href` 中 `unchecked` 的判断。
4. 找不到“音画同步”控件或无法判定状态时，写入 warning 日志并继续生成；只有确认开关处于开启状态时才点击。

## 错误处理

控件缺失和状态未知属于非致命兼容问题，不能中断生成。其他参数控件仍沿用现有错误处理，以便页面改版时明确暴露问题。

## 测试

单元测试覆盖：

- `IconCheckboxCheckedSecondary` 被识别为开启；
- `IconCheckboxUnchecked` 被识别为关闭；
- 旧版 `#icon-unchecked` 被识别为关闭；
- 无可识别属性时返回未知。

页面层面验证：使用已登录 Cookies 打开可灵视频页，执行参数设置不再在音画同步控件处超时；实际生成仍需由用户帐号完成一次人工验收。
