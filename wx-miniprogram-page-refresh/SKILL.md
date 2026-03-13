---
name: "wx-miniprogram-page-refresh"
description: "提供微信小程序页面间数据刷新机制的最佳实践。使用本地存储标记控制页面刷新，避免onShow频繁刷新。Invoke when user needs to implement page refresh mechanism in WeChat Mini Program, especially when data changes in one page need to trigger refresh in another page."
---

# 微信小程序页面刷新机制 Skill

## 概述

本 Skill 提供微信小程序中页面间数据同步刷新的标准解决方案。通过使用 `wx.setStorageSync` 设置刷新标记，在目标页面的 `onShow` 生命周期中检查标记并执行刷新，实现：

1. **及时刷新** - 数据变更后立即通知相关页面刷新
2. **避免频繁刷新** - 只在必要时刷新，提升性能
3. **代码简洁** - 标准化的刷新机制，易于维护

## 核心机制

### 1. 设置刷新标记（数据变更页）

当页面数据发生变更后，设置刷新标记：

```javascript
// 在数据操作成功的回调中设置标记
wx.setStorageSync('needRefreshXXX', true);
```

**命名规范**：
遵循 `needRefresh` + 页面/数据功能 的驼峰命名法：

```javascript
// 列表页刷新
wx.setStorageSync('needRefreshOrderList', true);
wx.setStorageSync('needRefreshUserList', true);
wx.setStorageSync('needRefreshProductList', true);

// 详情页刷新
wx.setStorageSync('needRefreshOrderDetail', true);
wx.setStorageSync('needRefreshUserProfile', true);

// 特定数据刷新
wx.setStorageSync('needRefreshComments', true);
wx.setStorageSync('needRefreshStatistics', true);
```

### 2. 检查并执行刷新（目标页）

在目标页面的 `onShow` 生命周期中检查标记：

```javascript
Page({
  data: {
    page: 1,
    hasMore: true,
    list: [],
  },

  onShow: function() {
    // 检查是否需要刷新
    const needRefresh = wx.getStorageSync('needRefreshXXX');
    if (needRefresh) {
      // 清除标记，避免重复刷新
      wx.removeStorageSync('needRefreshXXX');
      // 重置分页状态
      this.setData({
        page: 1,
        hasMore: true,
      });
      // 执行刷新
      this.loadData();
    }
  },

  loadData: function() {
    // 加载数据的逻辑
  },
});
```

## 完整示例

### 场景：修改信息后刷新首页列表

#### 修改页（edit.js）

```javascript
Page({
  submitForm() {
    wx.cloud.callFunction({
      name: 'updateData',
      data: { /* ... */ },
      success: (res) => {
        if (res.result && res.result.success) {
          wx.showToast({ title: '保存成功', icon: 'success' });
          
          // 设置刷新标记
          wx.setStorageSync('needRefreshOrderList', true);
          
          setTimeout(() => {
            wx.navigateBack();
          }, 1500);
        }
      },
    });
  },
});
```

#### 首页（index.js）

```javascript
Page({
  data: {
    list: [],
    page: 1,
    pageSize: 10,
    hasMore: true,
  },

  onShow: function() {
    // 检查是否需要刷新列表
    const needRefresh = wx.getStorageSync('needRefreshOrderList');
    if (needRefresh) {
      wx.removeStorageSync('needRefreshOrderList');
      this.loadList(true); // true 表示重新加载
    }
  },

  loadList: function(reload = false) {
    if (reload) {
      this.setData({
        page: 1,
        list: [],
        hasMore: true,
      });
    }
    // ... 加载数据的逻辑
  },
});
```

### 场景：创建项目后刷新详情页列表

#### 创建页（add.js）

```javascript
Page({
  data: {
    from: '', // 来源页面标识
    targetId: '',
  },

  doSubmit: function() {
    wx.cloud.callFunction({
      name: 'create',
      data: { /* ... */ },
      success: (res) => {
        if (res.result && res.result.success) {
          wx.showToast({ title: '添加成功', icon: 'success' });
          
          // 设置通用刷新标记
          wx.setStorageSync('needRefreshList', true);
          
          // 如果是从特定页面进入，额外设置对应刷新标记
          if (this.data.from === 'detail' && this.data.targetId) {
            wx.setStorageSync('needRefreshDetail', true);
          }
          
          setTimeout(() => {
            wx.navigateBack();
          }, 1500);
        }
      },
    });
  },
});
```

#### 详情页（detail.js）

```javascript
Page({
  data: {
    id: '',
    items: [],
    page: 1,
    pageSize: 20,
    hasMore: true,
  },

  onShow: function() {
    // 检查是否需要刷新列表
    const needRefresh = wx.getStorageSync('needRefreshDetail');
    if (needRefresh) {
      wx.removeStorageSync('needRefreshDetail');
      this.setData({
        page: 1,
        hasMore: true,
      });
      this.loadItems();
    }
  },

  loadItems: function() {
    // 加载列表的逻辑
  },
});
```

## 最佳实践

### 1. 标记命名规范

- 使用 `needRefresh` 作为前缀
- 使用驼峰命名法
- 名称要清晰表达刷新的目标页面或数据

```javascript
// 好的命名
wx.setStorageSync('needRefreshOrderList', true);
wx.setStorageSync('needRefreshUserProfile', true);
wx.setStorageSync('needRefreshProductList', true);

// 避免的命名
wx.setStorageSync('refresh', true);        // 太模糊
wx.setStorageSync('need_refresh_list', true); // 不是驼峰命名
```

### 2. 及时清除标记

在 `onShow` 中检查到标记后，**必须立即清除**，避免重复刷新：

```javascript
onShow: function() {
  const needRefresh = wx.getStorageSync('needRefreshXXX');
  if (needRefresh) {
    wx.removeStorageSync('needRefreshXXX'); // 立即清除
    this.loadData();
  }
}
```

### 3. 多页面刷新

如果一个操作需要刷新多个页面，设置多个标记：

```javascript
// 删除操作后，需要刷新列表和详情页
wx.setStorageSync('needRefreshList', true);
wx.setStorageSync('needRefreshDetail', true);
```

### 4. 条件刷新

根据来源页面决定是否设置特定标记：

```javascript
// 根据来源设置不同的刷新标记
if (this.data.from === 'pageA') {
  wx.setStorageSync('needRefreshPageA', true);
} else if (this.data.from === 'pageB') {
  wx.setStorageSync('needRefreshPageB', true);
}
```

### 5. 配合分页使用

刷新时重置分页状态：

```javascript
onShow: function() {
  const needRefresh = wx.getStorageSync('needRefreshXXX');
  if (needRefresh) {
    wx.removeStorageSync('needRefreshXXX');
    // 重置分页状态
    this.setData({
      page: 1,
      hasMore: true,
      list: [], // 可选：清空列表避免闪烁
    });
    this.loadData();
  }
}
```

## 注意事项

1. **只在必要时使用** - 对于实时性要求不高的数据，可以使用下拉刷新而不是自动刷新
2. **避免循环刷新** - A 页面刷新 B 页面，B 页面不要再刷新 A 页面
3. **考虑性能** - 如果列表数据量大，考虑使用局部刷新而不是全量刷新
4. **异常处理** - 网络错误时不要设置刷新标记，避免用户看到旧数据

## 对比其他方案

| 方案 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| **本地存储标记**（推荐） | 简单、可靠、跨页面 | 需要手动管理标记 | 大多数页面间刷新场景 |
| EventBus / 全局状态 | 实时、灵活 | 需要额外库、复杂 | 多页面实时同步 |
| 页面回调 | 实时、精确 | 只能返回上一页 | 仅返回上一页的场景 |
| 每次 onShow 刷新 | 简单 | 性能差、用户体验差 | 数据变化频繁的场景 |

## 总结

本地存储标记机制是微信小程序页面间数据刷新的最佳实践，它：

- ✅ 实现简单，无需额外依赖
- ✅ 性能友好，避免不必要的刷新
- ✅ 可靠稳定，不受页面栈影响
- ✅ 易于维护，代码清晰可读

在开发微信小程序时，遇到页面间数据同步需求，优先使用此机制。
