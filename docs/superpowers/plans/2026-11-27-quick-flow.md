# Quick Flow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans. Steps use checkbox syntax for tracking.

**Goal:** 單頁輸入、確認、取得成果，並以真實 MixRoute 驗收。
**Architecture:** 將既有執行表單及成品區移到首頁，加入必要記憶摘要；自動建立 Session，沿用 API、帳本與去重。
**Tech Stack:** 現有原生 HTML/CSS/JavaScript、FastAPI。
**Spec:** docs/superpowers/specs/2026-11-27-quick-flow-design.md

## Global Constraints

繁體中文；金鑰只留本機；共用原帳本；保留完成任務；付費執行必須由明確按鈕觸發。

## Review Focus

- 改需求後不能使用舊確認。
- 改預算後需要重新檢索。
- Session 失敗不能送出生成。
- 連按只能提交一次。
- 無法辨識或必要記憶不足不能生成。

### Task 1: 單頁接續與實測

**Files:** frontend/index.html, frontend/app.js, frontend/style.css, tests/browser_quick_flow.mjs
**Interfaces:** 沿用 /api/retrieve、/api/session、/api/execute，使用既有狀態與 SHA 成品。
- [x] 新瀏覽器測試先驗證單頁摘要不存在（RED，零付費呼叫）。
- [x] 整理三步驟首頁並加入自動 Session、狀態與失效處理。
- [x] 真實 SMART/auto 生成一份成品；核對空白 Session、SHA、下載、單次呼叫與手機寬度。
- [x] 既有 pytest 及一次獨立審查；修正重大問題。
- [x] 更新原工作區與 GitHub 來源包，保留原始實測證據及資源紀錄。
