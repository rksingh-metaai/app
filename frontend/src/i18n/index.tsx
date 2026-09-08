import React, { createContext, useContext, useEffect, useState, useCallback } from "react";

import { storage } from "@/src/utils/storage";
import { LangCode, translations, TransKey } from "./translations";

const LANG_KEY = "app_language";

type I18nContextType = {
  lang: LangCode;
  ready: boolean;
  hasChosen: boolean;
  setLang: (l: LangCode) => Promise<void>;
  t: (key: TransKey) => string;
};

const I18nContext = createContext<I18nContextType | null>(null);

export function I18nProvider({ children }: { children: React.ReactNode }) {
  const [lang, setLangState] = useState<LangCode>("en");
  const [hasChosen, setHasChosen] = useState(false);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    (async () => {
      const stored = await storage.getItem<string>(LANG_KEY, "");
      if (stored && stored in translations) {
        setLangState(stored as LangCode);
        setHasChosen(true);
      }
      setReady(true);
    })();
  }, []);

  const setLang = useCallback(async (l: LangCode) => {
    setLangState(l);
    setHasChosen(true);
    await storage.setItem(LANG_KEY, l);
  }, []);

  const t = useCallback(
    (key: TransKey): string => {
      return translations[lang]?.[key] ?? translations.en[key] ?? key;
    },
    [lang],
  );

  return (
    <I18nContext.Provider value={{ lang, ready, hasChosen, setLang, t }}>
      {children}
    </I18nContext.Provider>
  );
}

export function useI18n() {
  const ctx = useContext(I18nContext);
  if (!ctx) throw new Error("useI18n must be used within I18nProvider");
  return ctx;
}
