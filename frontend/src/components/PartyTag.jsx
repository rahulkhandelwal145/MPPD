import { PARTY_SYMBOL_URLS } from "./PartySymbol";

// Short display labels for the pill badge — full names are too wide for cards.
const PARTY_ABBR = {
  "Bharatiya Janata Party":                           "BJP",
  "Indian National Congress":                         "INC",
  "Samajwadi Party":                                  "SP",
  "All India Trinamool Congress":                     "AITC",
  "Dravida Munnetra Kazhagam":                        "DMK",
  "Telugu Desam Party":                               "TDP",
  "Janata Dal (United)":                              "JDU",
  "Janata Dal (Secular)":                             "JDS",
  "Aam Aadmi Party":                                  "AAP",
  "Communist Party of India (Marxist)":               "CPI(M)",
  "Communist Party of India":                         "CPI",
  "Communist Party of India (Marxist-Leninist) (Liberation)": "CPI(ML)",
  "Yuvajana Sramika Rythu Congress Party":            "YSRCP",
  "Shiv Sena":                                        "SS",
  "Shiv Sena (Uddhav Balasaheb Thackeray)":           "SS(UBT)",
  "Nationalist Congress Party":                       "NCP",
  "Nationalist Congress Party Sharadchandra Pawar":   "NCP(SP)",
  "Rashtriya Janata Dal":                             "RJD",
  "Rashtriya Lok Dal":                                "RLD",
  "Rashtriya Loktantrik Party":                       "RLTP",
  "Shiromani Akali Dal":                              "SAD",
  "Biju Janata Dal":                                  "BJD",
  "Bahujan Samaj Party":                              "BSP",
  "Jharkhand Mukti Morcha":                           "JMM",
  "Lok Janshakti Party (Ram Vilas)":                  "LJP(RV)",
  "Jana Sena Party":                                  "JSP",
  "Jammu and Kashmir National Conference":            "JKNC",
  "Indian Union Muslim League":                       "IUML",
  "Marumalarchi Dravida Munnetra Kazhagam":           "MDMK",
  "Viduthalai Chiruthaigal Katchi":                   "VCK",
  "Aazad Samaj Party (Kanshi Ram)":                   "ASPKR",
  "AJSU Party":                                       "AJSU",
  "All India Majlis-E-Ittehadul Muslimeen":           "AIMIM",
  "Apna Dal (Soneylal)":                              "AD(S)",
  "Asom Gana Parishad":                               "AGP",
  "Bharat Adivasi Party":                             "BAP",
  "Hindustani Awam Morcha (Secular)":                 "HAM(S)",
  "Kerala Congress":                                  "KC",
  "Revolutionary Socialist Party":                    "RSP",
  "Sikkim Krantikari Morcha":                         "SKM",
  "United Peoples Party, Liberal":                    "UPPL",
  "Voice of the People Party":                        "VPP",
  "Zoram People's Movement":                          "ZPM",
  "Independent":                                      "IND",
};

// Keys are the exact full party names stored in the DB.
const PARTY_COLORS = {
  "Bharatiya Janata Party":                           "bg-amber-50 text-amber-700 ring-amber-200",
  "Indian National Congress":                         "bg-sky-50 text-sky-700 ring-sky-200",
  "Samajwadi Party":                                  "bg-red-50 text-red-700 ring-red-200",
  "All India Trinamool Congress":                     "bg-teal-50 text-teal-700 ring-teal-200",
  "Dravida Munnetra Kazhagam":                        "bg-orange-50 text-orange-700 ring-orange-200",
  "Telugu Desam Party":                               "bg-yellow-50 text-yellow-700 ring-yellow-200",
  "Janata Dal (United)":                              "bg-green-50 text-green-700 ring-green-200",
  "Janata Dal (Secular)":                             "bg-green-50 text-green-700 ring-green-200",
  "Shiv Sena":                                        "bg-orange-50 text-orange-700 ring-orange-200",
  "Shiv Sena (Uddhav Balasaheb Thackeray)":           "bg-amber-50 text-amber-700 ring-amber-200",
  "Nationalist Congress Party":                       "bg-slate-50 text-slate-700 ring-slate-200",
  "Nationalist Congress Party Sharadchandra Pawar":   "bg-indigo-50 text-indigo-700 ring-indigo-200",
  "Rashtriya Janata Dal":                             "bg-emerald-50 text-emerald-700 ring-emerald-200",
  "Aam Aadmi Party":                                  "bg-blue-50 text-blue-700 ring-blue-200",
  "Communist Party of India (Marxist)":               "bg-red-100 text-red-800 ring-red-300",
  "Communist Party of India":                         "bg-red-50 text-red-700 ring-red-200",
  "Communist Party of India (Marxist-Leninist) (Liberation)": "bg-red-50 text-red-700 ring-red-200",
  "Yuvajana Sramika Rythu Congress Party":            "bg-blue-50 text-blue-700 ring-blue-200",
  "Biju Janata Dal":                                  "bg-slate-50 text-slate-700 ring-slate-200",
  "Bahujan Samaj Party":                              "bg-blue-50 text-blue-700 ring-blue-200",
  "Shiromani Akali Dal":                              "bg-yellow-50 text-yellow-700 ring-yellow-200",
  "Jharkhand Mukti Morcha":                           "bg-green-50 text-green-700 ring-green-200",
  "Lok Janshakti Party (Ram Vilas)":                  "bg-slate-50 text-slate-700 ring-slate-200",
  "Jana Sena Party":                                  "bg-amber-50 text-amber-700 ring-amber-200",
  "Rashtriya Lok Dal":                                "bg-green-50 text-green-700 ring-green-200",
  "Jammu and Kashmir National Conference":            "bg-slate-50 text-slate-700 ring-slate-200",
  "Indian Union Muslim League":                       "bg-green-50 text-green-700 ring-green-200",
  "Marumalarchi Dravida Munnetra Kazhagam":           "bg-orange-50 text-orange-700 ring-orange-200",
  "Independent":                                      "bg-slate-50 text-slate-600 ring-slate-200",
};

const FALLBACK = "bg-slate-50 text-slate-600 ring-slate-200";

export default function PartyTag({ party }) {
  const colorCls = (party && PARTY_COLORS[party]) || FALLBACK;
  const symbolUrl = party && PARTY_SYMBOL_URLS[party];
  const label = (party && PARTY_ABBR[party]) || party || "Unknown";

  return (
    <span
      title={party}
      className={`inline-flex flex-shrink-0 items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ${colorCls}`}
    >
      {symbolUrl && (
        <img
          src={symbolUrl}
          alt=""
          aria-hidden="true"
          className="h-4 w-4 flex-shrink-0 object-contain"
          onError={(e) => { e.currentTarget.style.display = "none"; }}
        />
      )}
      {label}
    </span>
  );
}
