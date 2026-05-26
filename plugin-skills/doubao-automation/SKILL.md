---
name: doubao-automation
description: Automate 豆包 (Doubao) AI Chat web interactions. Use when controlling the Doubao web chat interface — including sending messages, clicking the image generation button, typing in the input box, navigating to AI creation pages, or any multi-step Doubao web chat workflows.
---

# Doubao Automation

## Page Structure

豆包聊天页： `https://www.doubao.com/chat`

```
[导航栏]
  豆包 logo | 新对话 | AI 创作链接(/chat/create-image) | 更多菜单

[主区域]
  欢迎页（推荐话题） | 聊天消息区域

[底部输入区]
  textarea[placeholder="发消息..."]  ← 输入框
  快速按钮组: [快速 新] [PPT 生成] [更多▾]
  更多下拉菜单: 图像生成 | 帮我写作 | 翻译 | 编程 | 深入研究 | AI 播客 | 记录会议 | 音乐生成 | 解题答疑 | 数据分析
  发送按钮: 输入框右侧 36x36 圆形按钮 (x:718, y:431, class含"bg-dbx-fill-trans-20")
```

## Key AOM References (last snapshot)

| 元素 | ref | 说明 |
|------|-----|------|
| 输入框 textarea | `e155` | `textbox "发消息..."` |
| 更多按钮(输入区) | `e202` | button "更多" |
| 图像生成按钮 | `e160` | button "图像生成" (在更多下拉内) |
| 帮我写作 | `e164` | button "帮我写作" |
| 翻译 | `e168` | button "翻译" |
| 编程 | `e172` | button "编程" |
| 深入研究 | `e176` | button "深入研究" |
| AI 播客 | `e180` | button "AI 播客" |
| PPT生成 | `e129` | button "PPT 生成" |
| 快速 新 | `e118` | button "快速 新" |
| AI 创作链接 | `e24` | link → `/chat/create-image` |
| 新对话按钮 | `e16` | generic "新对话" |
| 登录按钮 | `e83` | button "登录" |

## 关键规则

### targetId 必须用 exact 值

每次 `browser` 调用时，`targetId` 必须用以下之一，**不能用 label**：

- **UUID**: 打开标签页时工具返回的完整 ID（如 `78889798AE8673EDEBA66B0A4E052E9D`）
- **tabId handle**: 如 `t1`（标签页位置索引）
- **label**: 仅在 `action="tabs"` / `action="open"` 时用于匹配，返回后后续调用必须换 UUID

```
❌ targetId: "doubao"   ← label，不能用
✅ targetId: "78889798AE8673EDEBA66B0A4E052E9D"
✅ targetId: "t1"
```

### ref 会过期，必须重新 snapshot

每次点击、输入、弹窗变化后，都要重新 `snapshot` 再继续操作。

```
❌ 点击 e160（已过时）→ 先 snapshot 获取新 ref
✅ 关键操作前 snapshot → 用新 ref → 执行
```

### className 可能是 SVGAnimatedString

evaluate 中访问 `el.className` 前必须做类型检查：

```javascript
const toClass = (el) => typeof el.className === 'string' ? el.className : '';
```

---

## Stable Selector Patterns

豆包使用动态类名，优先用以下稳定选择器：

```javascript
// 输入框
'textarea[placeholder="发消息..."]'
'textarea[dir="ltr"]'

// 发送按钮 (输入框右侧36x36圆形)
document.querySelector('textarea[placeholder="发消息..."]')
  ?.closest('div[class*="flex"]')
  ?.querySelector('button[size="36"], [class*="size-36"]')

// 图像生成按钮 (需先展开更多菜单)
'button[aria-haspopup="menu"]' // 更多按钮
// 或直接用 text
'button:has-text("图像生成")'

// AI 创作 (跳转生图页)
'a[href="/chat/create-image"]'

// 更多下拉菜单内所有项
'dialog button' // 在 dialog[role="dialog"] 内的按钮

// 输入区域技能按钮
'button[data-skill-id="skill_bar_button_5000"]' // PPT 生成
```

## Workflows

### 发消息（打字 → 发送）

1. snapshot 获取当前 ref
2. 点击输入框聚焦: `ref=<current>` → `kind: click`
3. 清空: `press(Control+a, Delete)`
4. 输入文字: `fill` 或 `type`
5. 发送按钮用 evaluate 脚本点击（36x36圆形，坐标 x:736, y:449）

```javascript
// 发送按钮 evaluate 脚本（className 可能有非string类型，需容错）
const sendBtn = Array.from(document.querySelectorAll('button')).find(b => {
  const r = b.getBoundingClientRect();
  return r.width === 36 && r.height === 36 &&
         typeof b.className === 'string' &&
         b.className.includes('dbx-fill-trans-20');
});
sendBtn?.click();
```

> ⚠️ 发送按钮**没有 aria-label**，只能通过位置/样式特征定位。

### 展开"更多"菜单 → 点击"图像生成"

1. **snapshot**（获取最新 ref）
2. 点击更多按钮: `kind: click, ref=<current-e202>`
3. **snapshot**（等菜单出现）
4. 点击图像生成: `kind: click, ref=<new-e160>`

```javascript
// 完整生图流程 evaluate 脚本
const moreBtn = Array.from(document.querySelectorAll('button')).find(b => 
  typeof b.innerText === 'string' && b.innerText.includes('更多')
);
if (moreBtn) { moreBtn.click(); await new Promise(r => setTimeout(r, 600)); }
const imgGenBtn = Array.from(document.querySelectorAll('button')).find(b => 
  typeof b.innerText === 'string' && b.innerText.includes('图像生成')
);
imgGenBtn?.click();
```

### 进入 AI 创作页（专用生图页）

直接导航: `https://www.doubao.com/chat/create-image`

### 新对话

点击导航栏"新对话"文字区域: `textbox "发消息..."` 附近的 button 或 `link[href="/chat"]`

## 注意事项

- **类名动态**: Tailwind JIT + 哈希类名，每次构建会变。不要用完整类名。
- **ref 会过期**: 每次 navigation 或 弹窗变化后重新 `snapshot`，不要跨操作复用旧 ref。
- **输入框聚焦**: 某些操作后需重新点击输入框才能继续输入
- **登录状态**: 未登录时部分功能不可用，会显示登录弹窗
- **AI 创作 vs 图像生成**: 前者是独立生图页 `/chat/create-image`；后者是输入框下拉菜单项
- **className 容错**: 访问 `el.className` 前必须检查 `typeof === 'string'`
- **发送按钮定位**: 只能通过位置(36x36, 坐标约736,449)或样式特征(`dbx-fill-trans-20`)找，没有 aria-label

## Quick Reference (copy-paste)

```json
{
  "inputBox": "textarea[placeholder=\"发消息...\"]",
  "sendButton": "evaluate for 36x36 circle at (736,449) with class containing 'dbx-fill-trans-20'",
  "imageGenMenuItem": "dialog button:has-text(\"图像生成\")",
  "imageGenPage": "https://www.doubao.com/chat/create-image",
  "moreMenu": "button:has-text(\"更多\")",
  "pptGen": "button[data-skill-id=\"skill_bar_button_5000\"]"
}
```
