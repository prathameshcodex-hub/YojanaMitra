import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "backend" / "data" / "schemes.json"

# New entries are candidates for research, not verified eligibility decisions.
CANDIDATES = [
    ("pmay-g", "Pradhan Mantri Awaas Yojana - Gramin", "Central", "https://pmayg.nic.in/"),
    ("pmjay", "Ayushman Bharat PM-JAY", "Central", "https://pmjay.gov.in/"),
    ("ujjwala", "Pradhan Mantri Ujjwala Yojana", "Central", "https://www.pmuy.gov.in/"),
    ("surya-ghar", "PM Surya Ghar Muft Bijli Yojana", "Central", "https://pmsuryaghar.gov.in/"),
    ("pm-kusum", "PM-KUSUM", "Central", "https://pmkusum.mnre.gov.in/"),
    ("pmfby", "Pradhan Mantri Fasal Bima Yojana", "Central", "https://pmfby.gov.in/"),
    ("apy", "Atal Pension Yojana", "Central", "https://www.npscra.nsdl.co.in/"),
    ("pmjjby", "Pradhan Mantri Jeevan Jyoti Bima Yojana", "Central", "https://jansuraksha.gov.in/"),
    ("pmsby", "Pradhan Mantri Suraksha Bima Yojana", "Central", "https://jansuraksha.gov.in/"),
    ("sukanya", "Sukanya Samriddhi Account Scheme", "Central", "https://www.indiapost.gov.in/"),
    ("ignoaps", "Indira Gandhi National Old Age Pension Scheme", "Central", "https://nsap.nic.in/"),
    ("ignwps", "Indira Gandhi National Widow Pension Scheme", "Central", "https://nsap.nic.in/"),
    ("igndps", "Indira Gandhi National Disability Pension Scheme", "Central", "https://nsap.nic.in/"),
    ("nfbs", "National Family Benefit Scheme", "Central", "https://nsap.nic.in/"),
    ("pmmvy", "Pradhan Mantri Matru Vandana Yojana", "Central", "https://pmmvy.wcd.gov.in/"),
    ("poshan-2", "Saksham Anganwadi and POSHAN 2.0", "Central", "https://wcd.gov.in/"),
    ("pm-poshan", "PM POSHAN Scheme", "Central", "https://pmposhan.education.gov.in/"),
    ("samagra-shiksha", "Samagra Shiksha", "Central", "https://samagra.education.gov.in/"),
    ("nmmss", "National Means-cum-Merit Scholarship Scheme", "Central", "https://scholarships.gov.in/"),
    ("csss-scholarship", "Central Sector Scheme of Scholarships for College Students", "Central", "https://scholarships.gov.in/"),
    ("pm-ajay", "Pradhan Mantri Anusuchit Jaati Abhyuday Yojana", "Central", "https://socialjustice.gov.in/"),
    ("pm-daksh", "PM-DAKSH", "Central", "https://pmdaksh.dosje.gov.in/"),
    ("pm-svanidhi", "PM Street Vendor's AtmaNirbhar Nidhi", "Central", "https://pmsvanidhi.mohua.gov.in/"),
    ("day-nulm", "Deendayal Antyodaya Yojana - National Urban Livelihoods Mission", "Central", "https://mohua.gov.in/"),
    ("day-nrlm", "Deendayal Antyodaya Yojana - National Rural Livelihoods Mission", "Central", "https://aajeevika.gov.in/"),
    ("mgnrega", "Mahatma Gandhi National Rural Employment Guarantee Act", "Central", "https://nrega.nic.in/"),
    ("pmgsy", "Pradhan Mantri Gram Sadak Yojana", "Central", "https://pmgsy.nic.in/"),
    ("jjm", "Jal Jeevan Mission", "Central", "https://jaljeevanmission.gov.in/"),
    ("sbm-g", "Swachh Bharat Mission - Gramin", "Central", "https://swachhbharatmission.ddws.gov.in/"),
    ("pmfme", "PM Formalisation of Micro Food Processing Enterprises", "Central", "https://pmfme.mofpi.gov.in/"),
    ("pmegp", "Prime Minister's Employment Generation Programme", "Central", "https://www.kviconline.gov.in/pmegpeportal/"),
    ("mudra", "Pradhan Mantri MUDRA Yojana", "Central", "https://www.mudra.org.in/"),
    ("stand-up-india", "Stand-Up India", "Central", "https://www.standupmitra.in/"),
    ("startup-india", "Startup India", "Central", "https://www.startupindia.gov.in/"),
    ("cgtmse", "Credit Guarantee Scheme for Micro and Small Enterprises", "Central", "https://www.cgtmse.in/"),
    ("pmkvy", "Pradhan Mantri Kaushal Vikas Yojana", "Central", "https://www.pmkvyofficial.org/"),
    ("ddu-gky", "Deen Dayal Upadhyaya Grameen Kaushalya Yojana", "Central", "https://ddugky.gov.in/"),
    ("e-shram", "e-Shram", "Central", "https://eshram.gov.in/"),
    ("pm-sym", "Pradhan Mantri Shram Yogi Maandhan", "Central", "https://maandhan.in/"),
    ("jan-dhan", "Pradhan Mantri Jan Dhan Yojana", "Central", "https://pmjdy.gov.in/"),
    ("nfsa", "National Food Security Act entitlements", "Central", "https://nfsa.gov.in/"),
    ("onorc", "One Nation One Ration Card", "Central", "https://nfsa.gov.in/"),
    ("mission-vatsalya", "Mission Vatsalya", "Central", "https://wcd.gov.in/"),
    ("mission-shakti", "Mission Shakti", "Central", "https://wcd.gov.in/"),
    ("one-stop-centre", "One Stop Centre Scheme", "Central", "https://wcd.gov.in/"),
    ("pm-abhim", "PM Ayushman Bharat Health Infrastructure Mission", "Central", "https://pmabhim.mohfw.gov.in/"),
    ("nhm", "National Health Mission", "Central", "https://nhm.gov.in/"),
    ("nikshay-poshan", "Nikshay Poshan Yojana", "Central", "https://nikshay.in/"),
    ("rashtriya-vayoshri", "Rashtriya Vayoshri Yojana", "Central", "https://alimco.in/"),
    ("adip", "Assistance to Persons with Disabilities for Aids and Appliances", "Central", "https://disabilityaffairs.gov.in/"),
    ("national-livestock", "National Livestock Mission", "Central", "https://dahd.gov.in/"),
    ("pm-matsya", "Pradhan Mantri Matsya Sampada Yojana", "Central", "https://dof.gov.in/"),
    ("soil-health", "Soil Health Card Scheme", "Central", "https://soilhealth.dac.gov.in/"),
    ("pmksy", "Pradhan Mantri Krishi Sinchayee Yojana", "Central", "https://pmksy.gov.in/"),
    ("agri-infra", "Agriculture Infrastructure Fund", "Central", "https://agriinfra.dac.gov.in/"),
    ("pm-kisan-dhan", "Pradhan Mantri Kisan Maandhan Yojana", "Central", "https://maandhan.in/"),
    ("namo-shetkari", "Namo Shetkari Mahasanman Nidhi Yojana", "Maharashtra", "https://maharashtra.gov.in/"),
    ("mjpjay", "Mahatma Jyotirao Phule Jan Arogya Yojana", "Maharashtra", "https://www.jeevandayee.gov.in/"),
    ("lek-ladki", "Lek Ladki Yojana", "Maharashtra", "https://womenchild.maharashtra.gov.in/"),
    ("sanjay-gandhi", "Sanjay Gandhi Niradhar Anudan Yojana", "Maharashtra", "https://sjsa.maharashtra.gov.in/"),
    ("shravanbal", "Shravanbal Seva Rajya Nivruttivetan Yojana", "Maharashtra", "https://sjsa.maharashtra.gov.in/"),
    ("mahadbt-postmatric", "MahaDBT Post-Matric Scholarships", "Maharashtra", "https://mahadbt.maharashtra.gov.in/"),
    ("rajarshi-shahu", "Rajarshi Chhatrapati Shahu Maharaj Shikshan Shulkh Shishyavrutti", "Maharashtra", "https://mahadbt.maharashtra.gov.in/"),
    ("panjabrao-hostel", "Dr. Panjabrao Deshmukh Vasatigruh Nirvah Bhatta", "Maharashtra", "https://mahadbt.maharashtra.gov.in/"),
    ("savitribai-scholarship", "Savitribai Phule Scholarship", "Maharashtra", "https://mahadbt.maharashtra.gov.in/"),
    ("swadhar", "Bharatratna Dr. Babasaheb Ambedkar Swadhar Yojana", "Maharashtra", "https://mahadbt.maharashtra.gov.in/"),
    ("bal-sangopan", "Bal Sangopan Yojana", "Maharashtra", "https://womenchild.maharashtra.gov.in/"),
    ("cmegp", "Chief Minister Employment Generation Programme", "Maharashtra", "https://maha-cmegp.gov.in/"),
    ("bandhkam-kamgar", "Maharashtra Building and Other Construction Workers Welfare Board benefits", "Maharashtra", "https://mahabocw.in/"),
    ("tribal-scholarship", "Maharashtra Tribal Development scholarships", "Maharashtra", "https://tribal.maharashtra.gov.in/"),
    ("mahajyoti", "MAHAJYOTI training and scholarship programmes", "Maharashtra", "https://mahajyoti.org.in/"),
    ("bartie", "BARTI training and educational support programmes", "Maharashtra", "https://barti.in/"),
    ("sarthi", "SARTHI educational and training programmes", "Maharashtra", "https://sarthi.maharashtra.gov.in/"),
    ("amrut-maha", "AMRUT Maharashtra programmes", "Maharashtra", "https://amrut.org.in/"),
    ("mahadbt-farmer", "MahaDBT Farmer agricultural subsidies", "Maharashtra", "https://mahadbt.maharashtra.gov.in/Farmer/"),
    ("gopinath-munde", "Gopinath Munde Shetkari Apghat Suraksha Sanugrah Anudan Yojana", "Maharashtra", "https://krishi.maharashtra.gov.in/"),
    ("farm-pond", "Magel Tyala Shettale scheme", "Maharashtra", "https://mahadbt.maharashtra.gov.in/Farmer/"),
    ("rashtriya-krishi", "Rashtriya Krishi Vikas Yojana implementation in Maharashtra", "Maharashtra", "https://krishi.maharashtra.gov.in/"),
    ("maha-rural-livelihood", "Maharashtra State Rural Livelihood Mission programmes", "Maharashtra", "https://umed.in/"),
    ("maha-women-savings", "Maharashtra women self-help group support programmes", "Maharashtra", "https://umed.in/"),
    ("maha-disability", "Maharashtra disability welfare programmes", "Maharashtra", "https://divyangkalyan.maharashtra.gov.in/"),
    ("maha-senior-citizen", "Maharashtra senior citizen welfare programmes", "Maharashtra", "https://sjsa.maharashtra.gov.in/"),
    ("maha-minority", "Maharashtra minority welfare scholarships", "Maharashtra", "https://mdd.maharashtra.gov.in/"),
    ("maha-forest-rights", "Maharashtra Forest Rights Act support programmes", "Maharashtra", "https://tribal.maharashtra.gov.in/"),
    ("maha-fisheries", "Maharashtra fisheries support programmes", "Maharashtra", "https://fisheries.maharashtra.gov.in/"),
    ("maha-animal-husbandry", "Maharashtra animal husbandry support programmes", "Maharashtra", "https://ahd.maharashtra.gov.in/"),
    ("maha-sericulture", "Maharashtra sericulture development programmes", "Maharashtra", "https://mahasilk.maharashtra.gov.in/"),
    ("maha-handloom", "Maharashtra handloom and handicraft support programmes", "Maharashtra", "https://mahahandloom.maharashtra.gov.in/"),
    ("maha-skill", "Maharashtra skill development programmes", "Maharashtra", "https://kaushalya.mahaswayam.gov.in/"),
    ("maha-startup", "Maharashtra startup and innovation support programmes", "Maharashtra", "https://msins.in/"),
    ("maha-msme", "Maharashtra MSME support programmes", "Maharashtra", "https://di.maharashtra.gov.in/"),
    ("maha-housing", "Maharashtra housing assistance programmes", "Maharashtra", "https://housing.maharashtra.gov.in/"),
    ("maha-water", "Maharashtra water conservation programmes", "Maharashtra", "https://waterconserve.maharashtra.gov.in/"),
    ("maha-energy", "Maharashtra renewable energy and solar support programmes", "Maharashtra", "https://www.mahaurja.com/"),
    ("maha-health", "Maharashtra public health assistance programmes", "Maharashtra", "https:// आरोग्य.maharashtra.gov.in/"),
    ("maha-education", "Maharashtra school education assistance programmes", "Maharashtra", "https://education.maharashtra.gov.in/"),
    ("maha-agri-extension", "Maharashtra agricultural extension and farmer support programmes", "Maharashtra", "https://krishi.maharashtra.gov.in/"),
]

def main():
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"Database not found: {DATA_FILE}")

    with DATA_FILE.open("r", encoding="utf-8") as f:
        schemes = json.load(f)

    if not isinstance(schemes, list):
        raise ValueError("schemes.json must contain a JSON list.")

    existing_ids = {str(s.get("id", "")).strip() for s in schemes}
    added = 0

    for scheme_id, name, level, url in CANDIDATES:
        if len(schemes) >= 100:
            break
        if scheme_id in existing_ids:
            continue

        schemes.append({
            "id": scheme_id,
            "name": name,
            "description": (
                "Candidate scheme record. Verify current operational status, "
                "official eligibility rules, benefits, and application process."
            ),
            "benefits": [
                "Refer to the official portal for current benefits and conditions."
            ],
            "level": level,
            "state": "Maharashtra" if level == "Maharashtra" else "All India",
            "eligibility": {
                "verification_required": True
            },
            "required_documents": [],
            "application_url": url,
            "verification_status": "needs_official_verification",
            "important_conditions": [
                "Not yet verified for current activity or eligibility.",
                "Do not treat this record as a confirmed eligibility match.",
                "Check the official portal before applying."
            ]
        })
        existing_ids.add(scheme_id)
        added += 1

    # Validate before replacing the original file.
    output = json.dumps(schemes, ensure_ascii=False, indent=2)
    json.loads(output)

    backup = DATA_FILE.with_suffix(".json.before_add.bak")
    backup.write_text(DATA_FILE.read_text(encoding="utf-8"), encoding="utf-8")
    DATA_FILE.write_text(output + "\n", encoding="utf-8")

    print(f"Added candidate records: {added}")
    print(f"Total scheme records: {len(schemes)}")
    print(f"Backup created: {backup}")
    print("New records require official verification before use.")

if __name__ == "__main__":
    main()
