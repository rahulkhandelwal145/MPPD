// Keys are the exact full party names stored in the DB (from /api/v1/mps/parties).
// Images are local copies in /public/party-symbols/ — source: Wikimedia Commons.
export const PARTY_SYMBOL_URLS = {
  "Bharatiya Janata Party":                           "/party-symbols/BJP.svg",
  "Indian National Congress":                         "/party-symbols/INC.svg",
  "Samajwadi Party":                                  "/party-symbols/SP.png",
  "All India Trinamool Congress":                     "/party-symbols/AITC.svg",
  "Dravida Munnetra Kazhagam":                        "/party-symbols/DMK.svg",
  "Telugu Desam Party":                               "/party-symbols/SP.png",   // same bicycle symbol
  "Janata Dal (United)":                              "/party-symbols/JDU.svg",
  "Aam Aadmi Party":                                  "/party-symbols/AAP.svg",
  "Communist Party of India (Marxist)":               "/party-symbols/CPIM.svg",
  "Yuvajana Sramika Rythu Congress Party":            "/party-symbols/YSRCP.svg",
  "Shiv Sena":                                        "/party-symbols/SHS.svg",
  "Shiv Sena (Uddhav Balasaheb Thackeray)":           "/party-symbols/SS_UBT.png",
  "Rashtriya Janata Dal":                             "/party-symbols/RJD.png",
  "Shiromani Akali Dal":                              "/party-symbols/SAD.svg",
  "Biju Janata Dal":                                  "/party-symbols/BJD.svg",
  "Bahujan Samaj Party":                              "/party-symbols/BSP.svg",
  "Jharkhand Mukti Morcha":                           "/party-symbols/SHS.svg",  // bow & arrow
};

// Standalone party symbol image — shown on the profile page header.
// `size` is a Tailwind class pair e.g. "h-14 w-14".
export default function PartySymbol({ party, size = "h-12 w-12" }) {
  const url = party && PARTY_SYMBOL_URLS[party];
  if (!url) return null;

  return (
    <div className={`${size} flex-shrink-0 overflow-hidden rounded-xl border border-slate-200 bg-white p-1.5 shadow-soft`}>
      <img
        src={url}
        alt={`${party} election symbol`}
        className="h-full w-full object-contain"
        onError={(e) => { e.currentTarget.parentElement.style.display = "none"; }}
      />
    </div>
  );
}
