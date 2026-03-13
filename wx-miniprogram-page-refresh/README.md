# 微信小程序页面刷新机制

## 简介

本 Skill 提供微信小程序中页面间数据同步刷新的标准解决方案。通过使用本地存储标记控制页面刷新，避免 `onShow` 频繁刷新，实现性能与用户体验的最佳平衡。

## 核心思想

```
数据变更页 ──设置标记──> wx.setStorageSync('needRefreshXXX', true)
                              │
                              │ 返回上一页
                              ▼
目标页面 <──检查标记─── onShow: wx.getStorageSync('needRefreshXXX')
```

## 快速开始

### 1. 数据变更页设置标记

```javascript
// 操作成功后设置刷新标记
wx.setStorageSync('needRefreshOrderList', true);
wx.navigateBack();
```

### 2. 目标页面检查标记

```javascript
onShow: function() {
  const needRefresh = wx.getStorageSync('needRefreshOrderList');
  if (needRefresh) {
    wx.removeStorageSync('needRefreshOrderList');
    this.loadData(); // 执行刷新
  }
}
```

## 完整文档

详见 [SKILL.md](./SKILL.md)，包含：

- 核心机制详解
- 完整代码示例
- 最佳实践
- 与其他方案对比

## 适用场景

- ✅ 列表页数据变更后需要刷新
- ✅ 详情页数据编辑后需要同步
- ✅ 跨页面数据状态同步
- ✅ 避免 onShow 频繁刷新

## 优势

| 特性 | 说明 |
|------|------|
| 简单 | 无需额外依赖，使用小程序原生 API |
| 高效 | 只在必要时刷新，避免性能浪费 |
| 可靠 | 不受页面栈影响，跨页面有效 |
| 易维护 | 标准化机制，代码清晰 |

## License

MIT
