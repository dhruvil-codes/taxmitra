import { createContext, useContext, useState, ReactNode } from "react";
import { store, Locale } from "./lib";

type Dict = Record<string, string>;

const en: Dict = {
  "app.name": "Tax Mitra",
  "app.tagline": "Your tax notice, made understandable.",
  "banner": "Independent prototype · All data is fictional and synthetic · Not an official Income Tax Department service",
  "lang.label": "Language",

  "landing.hero": "Got a confusing income tax notice?",
  "landing.sub": "Tax Mitra turns it into plain language, a document checklist, and a ready-to-send response — in your language, with every claim cited to official sources.",
  "landing.cta": "See how it works",
  "landing.four.title": "Tax Mitra answers your four questions",
  "landing.q1": "What happened?",
  "landing.q1.sub": "A plain-language explanation of your notice, side-by-side with the official wording.",
  "landing.q2": "Why did I get it?",
  "landing.q2.sub": "The possible reasons behind the mismatch — in words that make sense.",
  "landing.q3": "What do I need?",
  "landing.q3.sub": "A personalized checklist of documents, and why each one matters.",
  "landing.q4": "What do I do next?",
  "landing.q4.sub": "An editable response draft, a final review, and the exact official step to take.",
  "landing.gpt.title": "Why not just ask ChatGPT?",
  "landing.gpt.col1": "Your notice",
  "landing.gpt.col2": "ChatGPT",
  "landing.gpt.col3": "Tax Mitra",
  "landing.gpt.1": "Confusing, technical, stressful",
  "landing.gpt.1b": "Explains it from memory — then you're on your own",
  "landing.gpt.1c": "Explains it from official sources, cited — then walks you to the finish",
  "landing.gpt.2": "Deadline computed from rules",
  "landing.gpt.2b": "May miscalculate or vary each run",
  "landing.gpt.2c": "Deterministic rules engine, identical every time",
  "landing.gpt.3": "Next step",
  "landing.gpt.3b": "You must know what to ask",
  "landing.gpt.3c": "Guided questions — no prompting needed, in your language",
  "landing.trust": "Independent prototype · All data fictional · We never submit anything for you · The official portal stays the source of truth · We say \"we can't guide you\" when that's the truth",

  "login.title": "Demo login",
  "login.sub": "This is a hackathon prototype with synthetic data. Pick the demo citizen to explore.",
  "login.cta": "Continue as {name}",
  "login.note": "No real credentials exist. Nothing here connects to any government system.",

  "dash.title": "Your notices",
  "dash.amount": "Amount involved",
  "dash.respondBy": "Respond by",
  "dash.daysLeft": "{n} days left",
  "dash.dueToday": "Due today",
  "dash.overdue": "Response window closed",
  "dash.actionRequired": "Action required",
  "dash.dueSoon": "Due soon",
  "dash.start": "Start — I'll guide you",
  "dash.unsupported": "See why we can't guide this one",
  "dash.demoCitizen": "Demo citizen: {name}",

  "step.understand": "Understand",
  "step.answer": "Answer",
  "step.prepare": "Prepare",
  "step.act": "Act",

  "notice.official": "Official wording",
  "notice.officialShow": "Show the official wording",
  "notice.officialHide": "Hide the official wording",
  "notice.plain": "In simple language",
  "notice.notMean": "What this does NOT necessarily mean",
  "notice.reasons": "Why might this have happened?",
  "notice.basedOn": "Based on",
  "notice.viewSource": "View at source ↗",
  "notice.verification.pending": "Summary — pending verification against source",
  "notice.verification.verified": "Verified against source",
  "notice.continue": "Answer 3 simple questions",
  "notice.savedGuidance": "✓ Using verified saved guidance",
  "notice.close": "Close",

  "j.qTitle": "A few simple questions",
  "j.qHelp": "Your answers decide your personalized path. There are no wrong answers — \"I'm not sure\" is always allowed.",
  "j.next": "Continue",
  "j.back": "Back",
  "j.checklistTitle": "Your checklist",
  "j.checklistSub": "Based on your answers, you may need:",
  "j.why": "Why do I need this?",
  "j.draftTitle": "Your response draft",
  "j.draftSub": "This draft was prepared from your answers. Edit anything before accepting it.",
  "j.draftPlaceholder": "Your response letter...",
  "j.acceptDraft": "Accept draft",
  "j.reviewTitle": "Final review",
  "j.reviewIssue": "Issue",
  "j.reviewAmount": "Amount",
  "j.reviewPosition": "Your position",
  "j.reviewDocs": "Supporting documents",
  "j.reviewDeadline": "Response deadline",
  "j.reviewNote": "Review your information carefully before continuing.",
  "j.finalTitle": "Your next official step",
  "j.finalWhat": "What to do",
  "j.finalWhen": "By when",
  "j.finalNeed": "What you'll need",
  "j.finalWhere": "Where",
  "j.finalBoundary": "Tax Mitra does not submit anything on your behalf.",
  "j.finalInstruction": "Review your draft and supporting documents carefully, then submit the response yourself through the official Income Tax e-Filing portal.",
  "j.finalCopy": "Copy draft to clipboard",
  "j.finalCopied": "Copied ✓",
  "j.continuePortal": "Continue on the official Income Tax e-Filing portal ↗",
  "j.restart": "Start over",

  "unsupported.title": "We can't safely guide you through this yet",
  "unsupported.links": "Official channels",
  "unsupported.suggestionTitle": "Our honest suggestion",
  "back.home": "Back",
};

const hi: Dict = {
  "app.name": "टैक्स मित्र",
  "app.tagline": "आपका टैक्स नोटिस, अब आसान भाषा में।",
  "banner": "स्वतंत्र प्रोटोटाइप · सारा डेटा काल्पनिक है · यह आयकर विभाग की आधिकारिक सेवा नहीं है",
  "lang.label": "भाषा",

  "landing.hero": "आपको कोई उलझन भरा टैक्स नोटिस आया है?",
  "landing.sub": "Tax Mitra उसे आसान भाषा, दस्तावेज़ सूची और भेजने-योग्य उत्तर में बदल देता है — आपकी भाषा में, हर बात आधिकारिक स्रोतों से संदर्भित।",
  "landing.cta": "देखें यह कैसे काम करता है",
  "landing.four.title": "Tax Mitra आपके चार सवालों के जवाब देता है",
  "landing.q1": "क्या हुआ?",
  "landing.q1.sub": "आधिकारिक शब्दों के साथ-साथ, आसान भाषा में नोटिस की व्याख्या।",
  "landing.q2": "मुझे यह क्यों मिला?",
  "landing.q2.sub": "बेमेल के संभावित कारण — समझ आने वाले शब्दों में।",
  "landing.q3": "मुझे क्या चाहिए?",
  "landing.q3.sub": "आपके लिए तैयार दस्तावेज़ों की सूची, और हर एक क्यों ज़रूरी है।",
  "landing.q4": "अब मैं क्या करूँ?",
  "landing.q4.sub": "संपादन योग्य उत्तर मसौदा, अंतिम समीक्षा, और सटीक आधिकारिक कदम।",
  "landing.gpt.title": "सीधे ChatGPT से क्यों न पूछें?",
  "landing.gpt.col1": "आपका नोटिस",
  "landing.gpt.col2": "ChatGPT",
  "landing.gpt.col3": "Tax Mitra",
  "landing.gpt.1": "उलझन भरा, तकनीकी, परेशान करने वाला",
  "landing.gpt.1b": "याददाश्त से समझाता है — फिर आप अकेले",
  "landing.gpt.1c": "आधिकारिक स्रोतों से, संदर्भित समझाता है — और अंत तक साथ चलता है",
  "landing.gpt.2": "समय-सीमा की गणना",
  "landing.gpt.2b": "गलत या हर बार अलग हो सकती है",
  "landing.gpt.2c": "नियम-आधारित इंजन, हर बार एक जैसी",
  "landing.gpt.3": "अगला कदम",
  "landing.gpt.3b": "आपको पता होना चाहिए क्या पूछना है",
  "landing.gpt.3c": "निर्देशित सवाल — प्रॉम्प्ट की ज़रूरत नहीं, आपकी भाषा में",
  "landing.trust": "स्वतंत्र प्रोटोटाइप · सारा डेटा काल्पनिक · हम आपकी ओर से कुछ भी जमा नहीं करते · आधिकारिक पोर्टल ही सत्य का स्रोत है · जहाँ मार्गदर्शन संभव नहीं, हम वही कहते हैं",

  "login.title": "डेमो लॉगिन",
  "login.sub": "यह हैकाथॉन प्रोटोटाइप है, डेटा काल्पनिक है। देखने के लिए डेमो नागरिक चुनिए।",
  "login.cta": "{name} के रूप में जारी रखें",
  "login.note": "कोई असली क्रेडेंशियल नहीं है। यह किसी सरकारी सिस्टम से जुड़ा नहीं है।",

  "dash.title": "आपके नोटिस",
  "dash.amount": "शामिल राशि",
  "dash.respondBy": "तक जवाब दें",
  "dash.daysLeft": "{n} दिन बचे",
  "dash.dueToday": "आज अंतिम दिन",
  "dash.overdue": "समय-सीमा समाप्त",
  "dash.actionRequired": "कार्रवाई आवश्यक",
  "dash.dueSoon": "जल्दी करें",
  "dash.start": "शुरू करें — हम मार्गदर्शन करेंगे",
  "dash.unsupported": "देखें हम यह क्यों नहीं कर सकते",
  "dash.demoCitizen": "डेमो नागरिक: {name}",

  "step.understand": "समझें",
  "step.answer": "उत्तर दें",
  "step.prepare": "तैयारी",
  "step.act": "कार्रवाई",

  "notice.official": "आधिकारिक शब्द",
  "notice.officialShow": "आधिकारिक शब्द देखें",
  "notice.officialHide": "आधिकारिक शब्द छिपाएँ",
  "notice.plain": "सरल भाषा में",
  "notice.notMean": "इसका यह मतलब ज़रूरी नहीं है",
  "notice.reasons": "यह क्यों हुआ होगा?",
  "notice.basedOn": "आधार",
  "notice.viewSource": "स्रोत देखें ↗",
  "notice.verification.pending": "सारांश — स्रोत से सत्यापन शेष",
  "notice.verification.verified": "स्रोत से सत्यापित",
  "notice.continue": "3 आसान सवालों के जवाब दें",
  "notice.savedGuidance": "✓ सत्यापित सहेजी गई मार्गदर्शिका उपयोग में",
  "notice.close": "बंद करें",

  "j.qTitle": "कुछ आसान सवाल",
  "j.qHelp": "आपके जवाब ��पका व्यक्तिगत मार्ग तय करते हैं। कोई गलत जवाब नहीं — \"मुझे पक्का नहीं है\" हमेशा चलेगा।",
  "j.next": "आगे बढ़ें",
  "j.back": "पीछे",
  "j.checklistTitle": "आपकी सूची",
  "j.checklistSub": "आपके जवाबों के आधार पर, आपको चाहिए हो सकता है:",
  "j.why": "मुझे यह क्यों चाहिए?",
  "j.draftTitle": "आपका उत्तर मसौदा",
  "j.draftSub": "यह मसौदा आपके जवाबों से बना है। स्वीकारने से पहले कुछ भी बदल सकते हैं।",
  "j.draftPlaceholder": "आपका उत्तर पत्र...",
  "j.acceptDraft": "मसौदा स्वीकारें",
  "j.reviewTitle": "अंतिम समीक्षा",
  "j.reviewIssue": "मुद्दा",
  "j.reviewAmount": "राशि",
  "j.reviewPosition": "आपका रुख",
  "j.reviewDocs": "सहायक दस्तावेज़",
  "j.reviewDeadline": "जवाब की अंतिम तिथि",
  "j.reviewNote": "आगे बढ़ने से पहले अपनी जानकारी ध्यान से देखें।",
  "j.finalTitle": "आपका अगला आधिकारिक कदम",
  "j.finalWhat": "क्या करना है",
  "j.finalWhen": "कब तक",
  "j.finalNeed": "क्या चाहिए होगा",
  "j.finalWhere": "कहाँ",
  "j.finalBoundary": "Tax Mitra आपकी ओर से कुछ भी जमा नहीं करता है।",
  "j.finalInstruction": "अपने मसौदे और सहायक दस्तावेज़ों की सावधानी से समीक्षा करें, फिर आधिकारिक आयकर e-Filing पोर्टल पर स्वयं उत्तर जमा करें।",
  "j.finalCopy": "मसौदा कॉपी करें",
  "j.finalCopied": "कॉपी हो गया ✓",
  "j.continuePortal": "आधिकारिक आयकर e-Filing पोर्टल पर जाएँ ↗",
  "j.restart": "फिर से शुरू करें",

  "unsupported.title": "हम अभी इसमें आपका सुरक्षित मार्गदर्शन नहीं कर सकते",
  "unsupported.links": "आधिकारिक चैनल",
  "unsupported.suggestionTitle": "हमारा ईमानदार सुझाव",
  "back.home": "वापस",
};

const dicts: Record<Locale, Dict> = { en, hi };

interface I18nValue {
  locale: Locale;
  setLocale: (l: Locale) => void;
  t: (key: string, vars?: Record<string, string>) => string;
}

const I18nContext = createContext<I18nValue | null>(null);

export function I18nProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>(store.locale());
  const setLocale = (l: Locale) => {
    store.setLocale(l);
    setLocaleState(l);
    document.documentElement.lang = l;
  };
  const t = (key: string, vars?: Record<string, string>) => {
    let value = dicts[locale][key] ?? dicts.en[key] ?? key;
    if (vars) {
      for (const [k, v] of Object.entries(vars)) {
        value = value.replace(`{${k}}`, v);
      }
    }
    return value;
  };
  return <I18nContext.Provider value={{ locale, setLocale, t }}>{children}</I18nContext.Provider>;
}

export function useI18n(): I18nValue {
  const ctx = useContext(I18nContext);
  if (!ctx) throw new Error("useI18n outside provider");
  return ctx;
}
