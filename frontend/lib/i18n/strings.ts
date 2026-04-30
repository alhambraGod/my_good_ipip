export type Lang = "en" | "hi";

export const STRINGS = {
  en: {
    nav: {
      archetypes: "Archetypes",
      takeTest: "Take the test",
      startFree: "Start free →",
    },
    landing: {
      eyebrow: "Indian-built personality + career mapping",
      headline1: "Find your",
      headline2: "Indian Career DNA",
      pitch:
        "45 questions. 5 minutes. Built on Holland RIASEC + Big Five (OCEAN). Tuned for Bangalore IT, Marwari hustle, Sharma ji's beta, EMI math, all of it.",
      ctaPrimary: "Start Free Test →",
      ctaSecondary: "Browse 24 archetypes",
      socialProof:
        "Free results · No login needed · ₹49 only if you want the full report",
      whatYouGet: "What you'll get",
      featureArchetype: "Your archetype",
      featureCareer: "Career match",
      featureShare: "WhatsApp-ready share",
      gallery: "Some archetypes you might be",
      seeAll: "See all 24 →",
      science: "Real psychometrics, not vibes",
      faq: "Honest answers to honest questions",
      ctaTail: "Ready to find your archetype?",
      privacy:
        "Privacy: your answers stay on our server. We don't sell data, don't run ads, don't share with third parties. Email support to delete your data anytime.",
    },
    test: {
      tipKeyboard: "Tip: press 1–{n} on your keyboard",
      tipKeyboardLikert: "Tip: press 1–5 to answer · Use Back to revise",
      back: "← Back",
      restart: "Restart",
      continue: "Continue (Enter)",
      decoding: "Decoding your archetype…",
      submitFailed: "Failed to submit. Please try again.",
      networkErr: "Network error. Please retry.",
      cantStart: "Couldn't start the test. Try again.",
      resumeFailed: "Couldn't resume; starting over.",
    },
    payment: {
      title: "Unlock full CareerDNA",
      sub: "Holland + OCEAN deep report · one-time payment",
      detail: "Detailed report pack",
      promoOn: "Early-bird promo applied — locked in until checkout.",
      promoOff: "Standard price (promo quota used).",
      loading: "Loading current price…",
      whatYouGet: "What you get",
      payRazorpay: "Pay {amount} via Razorpay",
      payGeneric: "Pay via Razorpay",
      opening: "Opening checkout…",
      backToResults: "← Back to results",
      noUrl: "No payment URL returned. Try again.",
      generic: "Payment failed. Please try again.",
      promoLeft: "{remaining} / {cap} left",
      promoFooter: "Once used up, the price returns to ₹{full}.",
      trust: ["Secure checkout", "Instant unlock", "UPI / Cards"],
      bullets: [
        "Full archetype deep dive (India-relevant copy)",
        "OCEAN scores + percentiles",
        "5+ career matches with salary & city notes",
        "Strengths & growth tips",
        "Share-ready lines & rarity context",
      ],
    },
    common: {
      home: "Home",
      langEn: "EN",
      langHi: "हि",
      switchLang: "Switch language",
    },
  },
  hi: {
    nav: {
      archetypes: "Archetypes",
      takeTest: "Test do",
      startFree: "Free shuru karo →",
    },
    landing: {
      eyebrow: "Indian-built personality + career mapping",
      headline1: "Apna pataa lagao —",
      headline2: "Indian Career DNA",
      pitch:
        "45 sawal. 5 minute. Holland RIASEC + Big Five (OCEAN) pe based. Bangalore IT, Marwari hustle, Sharma ji ka beta, EMI math — sab samjhata hai.",
      ctaPrimary: "Free test shuru karo →",
      ctaSecondary: "24 archetypes dekho",
      socialProof:
        "Free result · login zaroori nahi · sirf ₹49 agar full report chahiye",
      whatYouGet: "Aap ko kya milega",
      featureArchetype: "Aapka archetype",
      featureCareer: "Career match",
      featureShare: "WhatsApp pe seedha share",
      gallery: "Kuch archetypes jo aap ho sakte ho",
      seeAll: "Saare 24 dekho →",
      science: "Sahi psychometrics, vibes nahi",
      faq: "Seedhe sawal ke seedhe jawab",
      ctaTail: "Apna archetype dhundhne ke liye taiyaar?",
      privacy:
        "Privacy: aapke jawab humare server pe rehte hain. Hum data bechte nahi, ads nahi chalate, third-party ke saath share nahi karte. Kabhi bhi email karke delete karaa sakte ho.",
    },
    test: {
      tipKeyboard: "Tip: keyboard pe 1–{n} dabao",
      tipKeyboardLikert: "Tip: 1–5 dabao · Back se badlo",
      back: "← Peeche",
      restart: "Phir se",
      continue: "Aage (Enter)",
      decoding: "Aapka archetype decode ho raha hai…",
      submitFailed: "Submit nahi hua. Phir try karo.",
      networkErr: "Network problem. Phir try karo.",
      cantStart: "Test shuru nahi hua. Phir try karo.",
      resumeFailed: "Resume fail; shuru se shuru karte hain.",
    },
    payment: {
      title: "Full CareerDNA unlock karo",
      sub: "Holland + OCEAN deep report · ek baar payment",
      detail: "Detailed report pack",
      promoOn: "Early-bird promo lag gayi — checkout tak locked.",
      promoOff: "Standard price (promo khatam).",
      loading: "Abhi ka price aa raha hai…",
      whatYouGet: "Aap ko kya milega",
      payRazorpay: "Razorpay se {amount} do",
      payGeneric: "Razorpay se pay karo",
      opening: "Checkout khol rahe hain…",
      backToResults: "← Result pe wapas",
      noUrl: "Payment URL nahi mila. Phir try karo.",
      generic: "Payment fail. Phir try karo.",
      promoLeft: "{remaining} / {cap} bache",
      promoFooter: "Khatam hote hi price ₹{full} ho jaayega.",
      trust: ["Surakshit checkout", "Turant unlock", "UPI / Cards"],
      bullets: [
        "Full archetype deep dive (Indian context)",
        "OCEAN scores + percentile",
        "5+ career matches, salary aur city ke saath",
        "Strengths aur growth tips",
        "Share lines aur rarity",
      ],
    },
    common: {
      home: "Ghar",
      langEn: "EN",
      langHi: "हि",
      switchLang: "Bhasha badlo",
    },
  },
} as const;

export type StringsTree = (typeof STRINGS)[Lang];

export function fmt(template: string, vars: Record<string, string | number>): string {
  return template.replace(/\{(\w+)\}/g, (_, k) => String(vars[k] ?? ""));
}
