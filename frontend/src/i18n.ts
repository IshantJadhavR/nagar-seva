import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import en from "./locales/en.json";
import hi from "./locales/hi.json";

let lng = "en";
try { lng = localStorage.getItem("ct_lang") ?? "en"; } catch { /* ignore */ }

i18n.use(initReactI18next).init({
  resources: { en: { translation: en }, hi: { translation: hi } },
  lng,
  fallbackLng: "en",
  interpolation: { escapeValue: false },
});

export function setLanguage(l: "en" | "hi") {
  i18n.changeLanguage(l);
  try { localStorage.setItem("ct_lang", l); } catch { /* ignore */ }
  document.documentElement.lang = l;
}
export default i18n;
