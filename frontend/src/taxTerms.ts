export interface TaxTermDefinition {
  id: string;
  term: { en: string; hi: string };
  plain_explanation: { en: string; hi: string };
  why_asked: { en: string; hi: string };
  what_needed: { en: string; hi: string };
  context: { en: string; hi: string };
  applicability: { en: string; hi: string };
  source: string;
}

export const TAX_TERMS_DICTIONARY: Record<string, TaxTermDefinition> = {
  computation_of_total_income: {
    id: "computation_of_total_income",
    term: {
      en: "Computation of Total Income",
      hi: "कुल आय की गणना (Computation of Total Income)",
    },
    plain_explanation: {
      en: "The calculation used to arrive at the income on which your tax is determined.",
      hi: "वह गणना जिससे आपकी कुल कर-योग्य आय और देय कर निर्धारित होता है।",
    },
    why_asked: {
      en: "The notice is asking you to provide the detailed calculation supporting the income figures reported in your filed return.",
      hi: "नोटिस में आपके दाखिल रिटर्न में बताई गई आय का समर्थन करने वाली विस्तृत गणना प्रदान करने को कहा गया है।",
    },
    what_needed: {
      en: "Your income computation statement, Form 16, or tax schedule summary for the Assessment Year.",
      hi: "निर्धारण वर्ष के लिए आपकी आय संगणना विवरणी, फॉर्म 16 या टैक्स शेड्यूल सारांश।",
    },
    context: {
      en: "Standard schedule in Section 142(1) scrutiny notices to reconcile reported income with books.",
      hi: "धारा 142(1) स्क्रूटनी नोटिस में रिपोर्ट की गई आय को खातों से मिलाने के लिए आवश्यक मानक अनुसूची।",
    },
    applicability: {
      en: "Section 142(1) read with Chapter IV computation provisions of the Income-tax Act.",
      hi: "आयकर अधिनियम के अध्याय IV संगणना प्रावधानों के साथ पठित धारा 142(1)।",
    },
    source: "Income-tax Act, 1961 · Section 142(1)",
  },

  balance_sheet: {
    id: "balance_sheet",
    term: {
      en: "Balance Sheet",
      hi: "बैलेंस शीट (Balance Sheet)",
    },
    plain_explanation: {
      en: "Shows your financial position, including what you own (assets) and what you owe (liabilities) as on March 31.",
      hi: "आपकी वित्तीय स्थिति दिखाता है, जिसमें 31 मार्च तक आपकी संपत्ति और देनदारियां शामिल हैं।",
    },
    why_asked: {
      en: "The Department checks whether your reported turnover, capital, loans, and business assets reconcile with your return.",
      hi: "विभाग यह जांचता है कि आपका घोषित टर्नओवर, पूंजी, ऋण और संपत्तियां रिटर्न से मेल खाती हैं या नहीं।",
    },
    what_needed: {
      en: "Audited or signed balance sheet, asset schedules, loan confirmations, and capital account statements.",
      hi: "हस्ताक्षरित बैलेंस शीट, संपत्ति अनुसूचियां, ऋण पुष्टि पत्र और पूंजी खाता विवरण।",
    },
    context: {
      en: "Verifies the business financial position and capital accretion at the end of the previous year.",
      hi: "पिछले वर्ष के अंत में व्यावसायिक वित्तीय स्थिति और पूंजी वृद्धि का सत्यापन करता है।",
    },
    applicability: {
      en: "Section 142(1)(ii) for production of accounts and financial statements.",
      hi: "लेखा और वित्तीय विवरण प्रस्तुत करने के लिए धारा 142(1)(ii)।",
    },
    source: "Income-tax Act, 1961 · Section 142(1)(ii)",
  },

  profit_loss: {
    id: "profit_loss",
    term: {
      en: "Profit and Loss Account (P&L)",
      hi: "लाभ-हानि खाता (Profit & Loss Account)",
    },
    plain_explanation: {
      en: "Shows the income earned and expenses incurred during the relevant period to arrive at net profit.",
      hi: "संबंधित अवधि के दौरान अर्जित आय और किए गए खर्चों का विवरण जिससे शुद्ध लाभ निकलता है।",
    },
    why_asked: {
      en: "The officer verifies that business turnover and claimed expenses are supported by authentic vouchers and ledger accounts.",
      hi: "अधिकारी यह सत्यापित करता है कि व्यावसायिक टर्नओवर और दावा किए गए खर्च वास्तविक वाउचर और खातों से समर्थित हैं।",
    },
    what_needed: {
      en: "Trading and Profit & Loss account, major expense ledger summaries, and depreciation statements.",
      hi: "ट्रेडिंग और लाभ-हानि खाता, मुख्य खर्चों के लेजर सारांश और मूल्यह्रास विवरण।",
    },
    context: {
      en: "Substantiates business income under Section 28 of the Income-tax Act.",
      hi: "आयकर अधिनियम की धारा 28 के तहत व्यावसायिक आय का सत्यापन करता है।",
    },
    applicability: {
      en: "Assessment of profits and gains of business or profession under Section 143(3).",
      hi: "धारा 143(3) के तहत व्यापार या पेशे के लाभ और लाभ का निर्धारण।",
    },
    source: "Income-tax Act, 1961 · Section 28 & 142(1)",
  },

  bank_statements: {
    id: "bank_statements",
    term: {
      en: "Complete Bank Statements",
      hi: "संपूर्ण बैंक विवरण (Complete Bank Statements)",
    },
    plain_explanation: {
      en: "Official records from your bank showing all money coming in (credits) and going out (debits) during the year.",
      hi: "बैंक के आधिकारिक रिकॉर्ड जो वर्ष के दौरान खाते में आए (क्रेडिट) और गए (डेबिट) सभी पैसों को दिखाते हैं।",
    },
    why_asked: {
      en: "The Assessing Officer matches actual banking turnover against reported receipts and identifies any unexplained entries.",
      hi: "आकलन अधिकारी वास्तविक बैंकिंग टर्नओवर को रिपोर्ट की गई प्राप्तियों से मिलाता है और अस्पष्ट प्रविष्टियों की पहचान करता है।",
    },
    what_needed: {
      en: "Full 12-month bank statements for all business and personal accounts used for financial transactions.",
      hi: "वित्तीय लेन-देन के लिए उपयोग किए गए सभी व्यावसायिक और व्यक्तिगत खातों के पूरे 12 महीने के बैंक विवरण।",
    },
    context: {
      en: "Primary corroborative evidence used by the Department to verify cash flow and turnover.",
      hi: "कैश फ्लो और टर्नओवर की पुष्टि के लिए विभाग द्वारा उपयोग किया जाने वाला प्राथमिक दस्तावेजी प्रमाण।",
    },
    applicability: {
      en: "Section 142(1)(ii) read with information matching from reporting entities under Section 285BA.",
      hi: "धारा 285BA के तहत रिपोर्टिंग संस्थाओं के डेटा से मिलान हेतु धारा 142(1)(ii)।",
    },
    source: "Income-tax Act, 1961 · Section 142(1)(ii)",
  },

  cash_deposits: {
    id: "cash_deposits",
    term: {
      en: "Explanation of Sources of Cash Deposits",
      hi: "नकद जमा के स्रोतों का स्पष्टीकरण (Sources of Cash Deposits)",
    },
    plain_explanation: {
      en: "Clear explanation and source documents showing where physical cash deposited into your bank accounts came from.",
      hi: "स्पष्टीकरण और रिकॉर्ड कि आपके बैंक खातों में जमा किया गया नकद कहाँ से आया।",
    },
    why_asked: {
      en: "Unexplained cash deposits are subject to statutory additions under Section 68 or 69A with special high tax rates.",
      hi: "अस्पष्ट नकद जमा पर धारा 68 या 69A के तहत विशेष उच्च कर दरों के साथ कर वृद्धि हो सकती है।",
    },
    what_needed: {
      en: "Cash book extract, bank withdrawal slips for redeposits, cash sales invoices, or gifts/loan confirmations.",
      hi: "कैश बुक का अंश, पुनर्जमा के लिए बैंक निकासी पर्चियां, नकद बिक्री इनवॉइस, या ऋण/उपहार पुष्टि पत्र।",
    },
    context: {
      en: "Taxpayer must establish identity, creditworthiness of source, and genuineness of transaction.",
      hi: "करदाता को स्रोत की पहचान, साख और लेन-देन की वास्तविकता स्थापित करनी होती है।",
    },
    applicability: {
      en: "Section 68 (Cash Credits) and Section 142(1)(iii) for written explanations.",
      hi: "लिखित स्पष्टीकरण के लिए धारा 68 (नकद ऋण) और धारा 142(1)(iii)।",
    },
    source: "Income-tax Act, 1961 · Section 68 & 142(1)(iii)",
  },

  significant_transactions: {
    id: "significant_transactions",
    term: {
      en: "Significant Credits and Debits",
      hi: "महत्वपूर्ण क्रेडिट एवं डेबिट (Significant Credits & Debits)",
    },
    plain_explanation: {
      en: "Explanations and supporting proof for unusually large receipts or payments in your accounts.",
      hi: "आपके खातों में असामान्य रूप से बड़े लेन-देन, प्राप्तियों या भुगतानों का स्पष्टीकरण और प्रमाण।",
    },
    why_asked: {
      en: "To verify whether large receipts represent taxable income, capital, loans, or exempt transactions.",
      hi: "यह सत्यापित करने के लिए कि क्या बड़ी प्राप्तियां कर-योग्य आय, पूंजी, ऋण या कर-मुक्त लेन-देन हैं।",
    },
    what_needed: {
      en: "Contracts, invoices, third-party confirmations, Form 26AS/AIS reconciliation, and ledger extracts.",
      hi: "अनुबंध, इनवॉइस, तृतीय-पक्ष पुष्टि, फॉर्म 26AS/AIS समाधान और लेजर अंश।",
    },
    context: {
      en: "Reconciles High-Value Financial Transactions (SFT) and AIS data with the filed return.",
      hi: "दाखिल रिटर्न के साथ उच्च-मूल्य वित्तीय लेनदेन (SFT) और AIS डेटा का समाधान करता है।",
    },
    applicability: {
      en: "Section 142(1)(iii) inquiry into banking transactions and Annual Information Statement.",
      hi: "बैंकिंग लेनदेन और वार्षिक सूचना विवरण (AIS) की धारा 142(1)(iii) के तहत जांच।",
    },
    source: "Income-tax Act, 1961 · Section 142(1)(iii)",
  },

  deductions_exemptions: {
    id: "deductions_exemptions",
    term: {
      en: "Deductions and Exemptions Claimed",
      hi: "दावा की गई छूट और कटौतियां (Deductions & Exemptions)",
    },
    plain_explanation: {
      en: "Official receipts, investments, and eligibility proof for tax deductions claimed in your return.",
      hi: "रिटर्न में दावा किए गए टैक्स डिडक्शन और छूट के आधिकारिक प्रमाण, निवेश और रसीदें।",
    },
    why_asked: {
      en: "The Department confirms that tax relief claimed under Chapter VI-A (80C, 80D) or Section 10 was legally eligible and paid.",
      hi: "विभाग यह पुष्टि करता है कि अध्याय VI-A (80C, 80D) या धारा 10 के तहत दावा की गई कर राहत वास्तव में पात्र और भुगतान की गई थी।",
    },
    what_needed: {
      en: "Life/health insurance premium receipts, provident fund proof, donation receipts, and home loan interest certificates.",
      hi: "बीमा प्रीमियम रसीदें, भविष्य निधि प्रमाण, दान रसीदें और गृह ऋण ब्याज प्रमाण पत्र।",
    },
    context: {
      en: "Disallowance of unsupported claims directly increases taxable income under assessment.",
      hi: "असमर्थित दावों की अस्वीकृति से निर्धारण के तहत कर योग्य आय सीधे बढ़ जाती है।",
    },
    applicability: {
      en: "Chapter VI-A (Sections 80C to 80U) and Section 10 of the Income-tax Act.",
      hi: "आयकर अधिनियम का अध्याय VI-A (धाराएं 80C से 80U) और धारा 10।",
    },
    source: "Income-tax Act, 1961 · Chapter VI-A",
  },

  other_notice_request: {
    id: "other_notice_request",
    term: {
      en: "Other Notice-Specific Information",
      hi: "अन्य नोटिस-विशिष्ट जानकारी (Other Inquiries)",
    },
    plain_explanation: {
      en: "Any other specific clarification, voucher, or contract specifically numbered in the Department's inquiry.",
      hi: "विभाग की जांच में विशेष रूप से क्रमांकित कोई अन्य स्पष्टीकरण, वाउचर या अनुबंध।",
    },
    why_asked: {
      en: "The Assessing Officer has statutory power under Section 142(1)(ii) and (iii) to require any relevant books or written explanations.",
      hi: "आकलन अधिकारी के पास कोई भी प्रासंगिक बहीखाते या लिखित जानकारी मांगने की वैधानिक शक्ति है।",
    },
    what_needed: {
      en: "Written submission, agreements, registrations, or chartered accountant certificates requested in the schedule.",
      hi: "अनुसूची में मांगे गए लिखित बयान, समझौते, पंजीकरण या सीए प्रमाण पत्र।",
    },
    context: {
      en: "General inquiry powers for complete and accurate assessment.",
      hi: "पूर्ण और सटीक निर्धारण के लिए सामान्य जांच शक्तियां।",
    },
    applicability: {
      en: "Section 142(1) inquiry powers for completion of assessment under Section 143(3).",
      hi: "धारा 143(3) के तहत मूल्यांकन पूरा करने के लिए धारा 142(1) जांच शक्तियां।",
    },
    source: "Income-tax Act, 1961 · Section 142(1)",
  },
};

export function lookupTaxTerm(sectionOrId: string): TaxTermDefinition {
  const norm = sectionOrId.toLowerCase().replace(/[\s\-_]/g, "");

  if (norm.includes("computation") || norm.includes("totalincome")) {
    return TAX_TERMS_DICTIONARY.computation_of_total_income;
  }
  if (norm.includes("balance") || norm.includes("sheet")) {
    return TAX_TERMS_DICTIONARY.balance_sheet;
  }
  if (norm.includes("profit") || norm.includes("loss") || norm.includes("pl")) {
    return TAX_TERMS_DICTIONARY.profit_loss;
  }
  if (norm.includes("bank") || norm.includes("statement")) {
    return TAX_TERMS_DICTIONARY.bank_statements;
  }
  if (norm.includes("cash") || norm.includes("deposit")) {
    return TAX_TERMS_DICTIONARY.cash_deposits;
  }
  if (norm.includes("significant") || norm.includes("credit") || norm.includes("debit") || norm.includes("transaction")) {
    return TAX_TERMS_DICTIONARY.significant_transactions;
  }
  if (norm.includes("deduction") || norm.includes("exemption") || norm.includes("chaptervia")) {
    return TAX_TERMS_DICTIONARY.deductions_exemptions;
  }

  return TAX_TERMS_DICTIONARY.other_notice_request;
}
