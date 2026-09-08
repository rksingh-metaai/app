# IndicFinance — Product Requirements Document

## Original Problem Statement
Build an Android application in the fintech domain with app localization in major Indic languages.

## User Choices
- App: All-in-one personal finance dashboard
- Languages: Hindi, Tamil, Telugu, Bengali, Marathi + English
- Auth: Email + password (JWT)
- AI: AI money assistant ("Arth")
- Design: Modern & trustworthy (Forest/Botanical Green palette)

## Architecture
- Frontend: Expo Router (React Native), @tanstack/react-query, react-native-keyboard-controller, react-native-svg, phosphor-react-native, reanimated. Light + dark theme tokens in `src/theme.ts`.
- Backend: FastAPI + Motor (MongoDB). JWT auth (bcrypt + pyjwt). AI via emergentintegrations (gpt-5.4, EMERGENT_LLM_KEY).
- i18n: custom dictionary system (`src/i18n`) with 6 languages, persisted in storage; also synced to backend user profile.

## User Personas
- Indian users who prefer managing personal finances in their native language.

## Core Requirements (static)
- Multilingual UI across 6 languages with native scripts.
- Secure email/password auth.
- Dashboard: total balance, income/expense, spending-by-category chart, recent transactions.
- Transactions CRUD; budgets; savings goals.
- AI assistant replying in the user's chosen language using their real financial data.

## Implemented (2026-06)
- Onboarding language picker (native scripts, no flags).
- JWT register/login; new users auto-seeded with 3 accounts, 12 transactions, 4 budgets, 3 goals.
- Dashboard with gradient balance hero, donut spending chart, quick actions, recent transactions, pull-to-refresh.
- Transactions tab: search, filter chips (All/Income/Expense), delete, FAB → add-transaction modal (type toggle, amount, category grid, account chips, note).
- Budgets tab: monthly budgets with progress bars, savings goals with add-money; add-budget / add-goal modals.
- AI Money Assistant chat (suggestion chips, history persistence, multilingual replies).
- Settings: profile, in-app language switcher (live), currency, logout.
- Full backend test suite: 14/14 pytest passing. Frontend flows verified.

## Backlog / Remaining
- P1: Multiple currency support beyond INR; account management screen (add/edit accounts).
- P1: Edit existing transactions; transaction date picker.
- P2: Recurring transactions & bill reminders; export/statement.
- P2: Biometric app lock; charts for income trends over months.

## Next Tasks
- Gather user feedback on language coverage and any additional Indic languages.
