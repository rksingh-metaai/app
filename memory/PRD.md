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
- JWT register/login; new users auto-seeded with 3 accounts, 12 transactions, 4 budgets, 3 goals, 4 bills.
- Dashboard with gradient balance hero, donut spending chart, quick actions (Add Expense/Income, Accounts, Bills), spending-trends card, upcoming-bills preview, recent transactions, pull-to-refresh.
- Transactions tab: search, filter chips (All/Income/Expense), delete, FAB → add-transaction modal.
- Budgets tab: monthly budgets with progress bars, savings goals with add-money; add-budget / add-goal modals.
- AI Money Assistant chat (multilingual replies, history persistence).
- Settings: profile, in-app language switcher (live), currency, logout.
- Accounts screen: add / rename / edit / delete accounts (bank, cash, card, wallet, investment).
- Bill Reminders: recurring monthly bills with due-day, days-until badges, mark-paid (logs expense + deducts balance), add/edit/delete.
- Spending Trends: month-over-month income vs expense chart (last 6 months) + averages.
- Fixed Android launch crash (AppearanceModule.setColorScheme null) in src/theme.ts.
- Full backend test suite: 22/22 pytest passing. All frontend flows verified.

## Backlog / Remaining
- P1: Multiple currency support beyond INR.
- P1: Edit existing transactions; transaction date picker.
- P2: Weekly/yearly bill frequencies; bill payment history view.
- P2: Biometric app lock.

## Next Tasks
- Gather user feedback on language coverage and any additional Indic languages.
