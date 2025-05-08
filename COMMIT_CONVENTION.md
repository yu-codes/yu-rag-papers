# 📝 Git Commit 規則 - Conventional Commits

本專案採用 [Conventional Commits](https://www.conventionalcommits.org/) 格式，請依下列規範進行 commit message 撰寫，以利版本管理與自動產生 Changelog。

---

## 🔧 常見 type 類型說明

| 類型    | 說明                             |
|---------|----------------------------------|
| feat    | 新功能（features）               |
| fix     | 修復 bug（bugs）                 |
| docs    | 文件修改（README, 註解等）       |
| style   | 格式調整（不影響程式邏輯）       |
| refactor| 重構程式碼邏輯                   |
| test    | 新增或調整測試                   |
| chore   | 雜項（如建構設定、CI、Docker）   |
| perf    | 效能優化                         |
| ci      | CI/CD 相關設定（GitHub Actions） |

---

## 💡 額外建議

- `message` 建議控制在 **72 字以內**
- 英文建議使用祈使句，如：add、fix、update、remove
- 中文團隊也可採中英混用，例如：

---

## ✅ 格式範例

<type>(optional-scope): message

例如：
feat(api): add /ask endpoint for RAG pipeline
fix(memory): resolve PostgreSQL history bug
docs(readme): update architecture and usage section