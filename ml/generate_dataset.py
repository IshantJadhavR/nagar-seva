# -*- coding: utf-8 -*-
"""
Synthetic civic-complaint dataset generator (English + Hindi), Maharashtra municipal setting.

Design goals
- 8 categories x 2 languages, balanced.
- Train and test use DIFFERENT issue phrases and DIFFERENT openings/closings
  (phrase-disjoint split), so the test score is less inflated than a random split.
- Includes mixed-issue complaints (secondary_category), typos, missing punctuation,
  location/duration/safety fields for testing the severity engine.

Run:  python generate_dataset.py
"""
import random
import re
import pandas as pd

random.seed(42)

N_TRAIN_PER_CELL = 300   # 8 categories x 2 languages x 300 = 4800
N_TEST_PER_CELL = 75     # 8 x 2 x 75 = 1200   -> total 6000

DEPT = {
    "Roads": "Public Works Department",
    "Garbage": "Solid Waste Management",
    "Water Supply": "Water Supply Department",
    "Drainage": "Drainage and Sewerage",
    "Streetlight": "Electrical Department",
    "Public Health": "Health Department",
    "Encroachment": "Building Permission and Encroachment",
    "Other": "Admin Review",
}

# ---------------------------------------------------------------- issues
# (english, hindi, is_critical)
ISSUES = {
    "Roads": [
        ("There is a big pothole on the road", "सड़क पर बड़ा गड्ढा हो गया है", 0),
        ("The road is badly damaged and full of potholes", "सड़क बहुत खराब हो गई है और जगह-जगह गड्ढे हैं", 0),
        ("Road surface has broken and gravel is spread everywhere", "सड़क टूट गई है और हर तरफ बजरी फैली है", 0),
        ("The footpath tiles are broken", "फुटपाथ की टाइलें टूटी हुई हैं", 0),
        ("The speed breaker is too high and damaged", "स्पीड ब्रेकर बहुत ऊँचा और टूटा हुआ है", 0),
        ("The road has caved in after the rain", "बारिश के बाद सड़क धँस गई है", 0),
        ("The tar road has completely worn out", "डामर की सड़क पूरी तरह उखड़ गई है", 0),
        ("There is an open manhole without a cover on the road", "सड़क पर खुला मैनहोल है, ढक्कन नहीं है", 1),
        ("Road repair work was left half done", "सड़क की मरम्मत का काम अधूरा छोड़ दिया गया है", 0),
        ("A deep crater has formed in the middle of the road", "बीच सड़क में गहरा गड्ढा बन गया है", 0),
        ("Cracks have appeared all across the road", "सड़क में जगह-जगह दरारें पड़ गई हैं", 0),
        ("The road near the bridge is uneven and broken", "पुल के पास की सड़क ऊबड़-खाबड़ और टूटी हुई है", 0),
    ],
    "Garbage": [
        ("Garbage has not been collected", "कचरा नहीं उठाया गया है", 0),
        ("The dustbin is overflowing and waste is spilling onto the street", "कूड़ेदान भरकर बाहर बह रहा है और कचरा सड़क पर फैल रहा है", 0),
        ("People are dumping waste openly in the empty plot", "लोग खाली प्लॉट में खुलेआम कचरा फेंक रहे हैं", 0),
        ("Waste is being burned here and the smoke is spreading", "यहाँ कचरा जलाया जा रहा है और धुआँ फैल रहा है", 0),
        ("The garbage truck does not come regularly", "कचरा गाड़ी नियमित रूप से नहीं आती", 0),
        ("A heap of rubbish has piled up at the corner", "कोने पर कूड़े का ढेर लग गया है", 0),
        ("Construction debris has been dumped on the roadside", "सड़क किनारे निर्माण का मलबा फेंक दिया गया है", 0),
        ("Stray animals scatter the waste and it smells terrible", "आवारा जानवर कचरा बिखेर देते हैं और बहुत बदबू आती है", 0),
        ("There is no dustbin in this area", "इस इलाके में कोई कूड़ेदान नहीं है", 0),
        ("Wet and dry waste is mixed and lying in the open", "गीला और सूखा कचरा मिलाकर खुले में पड़ा है", 0),
        ("Plastic waste has piled up in the street", "प्लास्टिक का कचरा गली में जमा हो गया है", 0),
        ("The community dumping point is completely full", "कचरा संग्रह स्थल पूरी तरह भर गया है", 0),
    ],
    "Water Supply": [
        ("There is no water supply in our area", "हमारे इलाके में पानी की सप्लाई नहीं आ रही है", 0),
        ("Water pressure is very low in the taps", "नलों में पानी का दबाव बहुत कम है", 0),
        ("The tap water is dirty and has a bad smell", "नल का पानी गंदा है और उसमें बदबू आ रही है", 0),
        ("The main water pipeline is leaking", "मुख्य पानी की पाइपलाइन लीक हो रही है", 0),
        ("The water tanker has not arrived as scheduled", "पानी का टैंकर समय पर नहीं आया", 0),
        ("The water supply timing was changed without notice", "बिना सूचना दिए पानी आने का समय बदल दिया गया", 0),
        ("A pipeline has burst and clean water is being wasted", "पाइपलाइन फट गई है और साफ पानी बर्बाद हो रहा है", 0),
        ("Muddy water is coming out of the tap", "नल से मटमैला पानी आ रहा है", 0),
        ("The public tap nearby is broken", "पास का सार्वजनिक नल टूटा हुआ है", 0),
        ("The water meter is not working properly", "पानी का मीटर ठीक से काम नहीं कर रहा", 0),
        ("We get water for only ten minutes a day", "दिन में सिर्फ दस मिनट पानी आता है", 0),
        ("Sewage water is mixing with the drinking water supply", "पीने के पानी की सप्लाई में सीवर का पानी मिल रहा है", 1),
    ],
    "Drainage": [
        ("The drain is blocked and water is not flowing", "नाली जाम हो गई है और पानी नहीं निकल रहा", 0),
        ("Sewage is overflowing onto the road", "सीवर का पानी सड़क पर बह रहा है", 0),
        ("There is waterlogging in the lane after every rain", "हर बारिश के बाद गली में पानी भर जाता है", 0),
        ("The open gutter is broken and uncovered", "खुली नाली टूटी हुई है और ढकी नहीं है", 0),
        ("Drains were not cleaned before the monsoon", "मानसून से पहले नालों की सफाई नहीं हुई है", 0),
        ("Dirty drain water is entering our houses", "नाली का गंदा पानी घरों में घुस रहा है", 0),
        ("The manhole is overflowing with sewage", "मैनहोल से सीवेज उफन रहा है", 0),
        ("The nala behind our society is choked with garbage", "सोसाइटी के पीछे का नाला कचरे से भरकर जाम हो गया है", 0),
        ("A drain cover is missing near the entrance", "प्रवेश द्वार के पास नाली का ढक्कन गायब है", 0),
        ("The sewer line is choked and smells terrible", "सीवर लाइन चोक हो गई है और बहुत बदबू आ रही है", 0),
        ("Rainwater is not draining from the street", "बारिश का पानी सड़क से निकल नहीं रहा है", 0),
        ("Heavy flooding has occurred in the lane and water is entering shops", "गली में भारी जलभराव हो गया है और दुकानों में पानी घुस रहा है", 1),
    ],
    "Streetlight": [
        ("The streetlight is not working", "स्ट्रीट लाइट काम नहीं कर रही है", 0),
        ("Street lights in the entire lane are off at night", "पूरी गली की स्ट्रीट लाइटें रात में बंद रहती हैं", 0),
        ("The light keeps flickering the whole night", "बत्ती पूरी रात टिमटिमाती रहती है", 0),
        ("The streetlight pole is leaning and may fall", "स्ट्रीट लाइट का खंभा झुक गया है और गिर सकता है", 0),
        ("The light stays on during the day and wastes electricity", "दिन में भी लाइट जलती रहती है और बिजली बर्बाद हो रही है", 0),
        ("There is no light on this road and it is very dark", "इस सड़क पर बिल्कुल रोशनी नहीं है और बहुत अंधेरा रहता है", 0),
        ("The bulb of the street lamp is broken", "स्ट्रीट लैंप का बल्ब टूट गया है", 0),
        ("The lamp post has rusted and its cover is missing", "लैंप पोस्ट में जंग लग गई है और उसका कवर गायब है", 0),
        ("New streetlights are required in this area", "इस इलाके में नई स्ट्रीट लाइटें लगाने की ज़रूरत है", 0),
        ("Live electric wires are hanging from the streetlight pole", "स्ट्रीट लाइट के खंभे से बिजली के नंगे तार लटक रहे हैं", 1),
        ("The light near the park is out", "पार्क के पास की लाइट बंद है", 0),
        ("The streetlight switch box is open and the wires are visible", "स्ट्रीट लाइट का स्विच बॉक्स खुला है और तार दिख रहे हैं", 1),
    ],
    "Public Health": [
        ("Mosquitoes are breeding in stagnant water nearby", "आसपास जमा पानी में मच्छर पनप रहे हैं", 0),
        ("A dead animal is lying on the road and rotting", "सड़क पर मरा हुआ जानवर पड़ा है और सड़ रहा है", 0),
        ("Stray dogs are attacking people in our area", "हमारे इलाके में आवारा कुत्ते लोगों पर हमला कर रहे हैं", 0),
        ("The food stalls here are very unhygienic and sell stale food", "यहाँ के खाने के ठेले बहुत गंदे हैं और बासी खाना बेचते हैं", 0),
        ("There is a dengue outbreak in our locality", "हमारे मोहल्ले में डेंगू फैल गया है", 0),
        ("Stagnant water in the empty plot is full of mosquito larvae", "खाली प्लॉट के जमा पानी में मच्छरों के लार्वा भरे हैं", 0),
        ("Fogging has not been done in our area for months", "महीनों से हमारे इलाके में फॉगिंग नहीं हुई है", 0),
        ("Rats have increased in the market because of the dirt", "गंदगी की वजह से बाज़ार में चूहे बढ़ गए हैं", 0),
        ("The public toilet is extremely dirty and unhygienic", "सार्वजनिक शौचालय बहुत गंदा और अस्वच्छ है", 0),
        ("Pigs are roaming in the colony and spreading filth", "कॉलोनी में सूअर घूम रहे हैं और गंदगी फैला रहे हैं", 0),
        ("Packs of stray dogs bite passersby at night", "आवारा कुत्तों के झुंड रात में राहगीरों को काटते हैं", 0),
        ("Fever is spreading in the whole neighbourhood because of mosquitoes", "मच्छरों की वजह से पूरे मोहल्ले में बुखार फैल रहा है", 0),
    ],
    "Encroachment": [
        ("Hawkers have occupied the entire footpath", "फेरीवालों ने पूरे फुटपाथ पर कब्ज़ा कर लिया है", 0),
        ("Illegal construction is going on next to our building", "हमारी बिल्डिंग के बगल में अवैध निर्माण चल रहा है", 0),
        ("A shop owner has extended his shop onto the road", "एक दुकानदार ने अपनी दुकान सड़क तक बढ़ा ली है", 0),
        ("An unauthorized shed has been built on public land", "सरकारी ज़मीन पर अवैध शेड बना दिया गया है", 0),
        ("A garage has been built illegally on the public pavement", "सार्वजनिक फुटपाथ पर अवैध गैराज बना दिया गया है", 0),
        ("Illegal hawkers block the entrance of the market", "अवैध फेरीवाले बाज़ार का प्रवेश द्वार रोक देते हैं", 0),
        ("A temporary structure has been put up on the roadside without permission", "सड़क किनारे बिना अनुमति के अस्थायी ढाँचा खड़ा कर दिया गया है", 0),
        ("The compound wall has been extended onto the public road", "कंपाउंड की दीवार सार्वजनिक सड़क तक बढ़ा दी गई है", 0),
        ("Builders are constructing an extra floor without permission", "बिल्डर बिना अनुमति के अतिरिक्त मंज़िल बना रहे हैं", 0),
        ("Handcarts have taken over the main road and block traffic", "ठेलों ने मुख्य सड़क पर कब्ज़ा कर लिया है और ट्रैफिक रुक जाता है", 0),
        ("Someone has taken over the open ground meant for the garden", "बगीचे के लिए छोड़ी गई खुली जगह पर किसी ने कब्ज़ा कर लिया है", 0),
        ("An illegal advertisement stand has been fixed on the footpath", "फुटपाथ पर अवैध विज्ञापन का स्टैंड लगा दिया गया है", 0),
    ],
    "Other": [
        ("There is loud music from the wedding hall late at night", "शादी हॉल में देर रात तक तेज़ संगीत बजता है", 0),
        ("The traffic signal is not following its timing", "ट्रैफिक सिग्नल समय के अनुसार नहीं चल रहा", 0),
        ("I want to give feedback about the new municipal website", "मैं नगर निगम की नई वेबसाइट के बारे में सुझाव देना चाहता हूँ", 0),
        ("I need information about my property tax receipt", "मुझे अपनी संपत्ति कर की रसीद के बारे में जानकारी चाहिए", 0),
        ("There is some problem in this area, please look into it", "इस इलाके में कुछ समस्या है, कृपया देखिए", 0),
        ("Please help, something is wrong near my house", "कृपया मदद कीजिए, मेरे घर के पास कुछ गड़बड़ है", 0),
        ("The bus service on this route is very irregular", "इस रूट पर बस सेवा बहुत अनियमित है", 0),
        ("I want to know how to apply for a birth certificate", "जन्म प्रमाण पत्र बनवाने की प्रक्रिया जाननी है", 0),
        ("Neighbours fight loudly every night", "पड़ोसी हर रात ज़ोर-ज़ोर से झगड़ते हैं", 0),
        ("Thank you for the quick action on my last complaint", "पिछली शिकायत पर जल्दी काम करने के लिए धन्यवाद", 0),
        ("Auto drivers are charging extra fare", "ऑटो वाले ज़्यादा किराया माँग रहे हैं", 0),
        ("My ration card has not been updated", "मेरा राशन कार्ड अपडेट नहीं हुआ है", 0),
    ],
}

# (primary, secondary, english, hindi)
MIXED = [
    ("Water Supply", "Roads", "A water pipeline has burst and the water is damaging the road", "पानी की पाइपलाइन फट गई है और पानी से सड़क खराब हो रही है"),
    ("Drainage", "Roads", "Sewage is overflowing from the drain and flooding the road", "नाली से सीवेज उफनकर सड़क पर भर गया है"),
    ("Garbage", "Drainage", "Garbage dumped in the nala has blocked the drain", "नाले में कचरा फेंकने से नाली जाम हो गई है"),
    ("Public Health", "Garbage", "Piles of garbage are attracting rats and mosquitoes", "कचरे के ढेर की वजह से चूहे और मच्छर बढ़ रहे हैं"),
    ("Public Health", "Drainage", "Stagnant drain water is breeding mosquitoes in our lane", "नाली का रुका हुआ पानी हमारी गली में मच्छर पैदा कर रहा है"),
    ("Roads", "Encroachment", "Hawkers stand on the road and the road is also broken", "फेरीवाले सड़क पर खड़े रहते हैं और सड़क भी टूटी हुई है"),
    ("Streetlight", "Roads", "The streetlight is off and the road has deep potholes, so it is dangerous at night", "स्ट्रीट लाइट बंद है और सड़क पर गहरे गड्ढे हैं, इसलिए रात में खतरा है"),
    ("Water Supply", "Drainage", "Dirty drain water is mixing with the tap water", "नाली का गंदा पानी नल के पानी में मिल रहा है"),
    ("Garbage", "Public Health", "Garbage has not been picked up and it is causing a foul smell and disease", "कचरा नहीं उठाया गया है और इससे बदबू और बीमारी फैल रही है"),
    ("Encroachment", "Roads", "A shop has occupied the road and traffic is blocked", "दुकान ने सड़क पर कब्ज़ा कर लिया है और ट्रैफिक रुका है"),
    ("Drainage", "Public Health", "The blocked drain is full of mosquito larvae and is making people ill", "जाम नाली में मच्छरों के लार्वा भरे हैं और लोग बीमार पड़ रहे हैं"),
    ("Roads", "Drainage", "The road is damaged because water keeps standing here from the clogged drain", "जाम नाली का पानी रुकने से सड़क खराब हो गई है"),
]
MIXED_BY_PRIMARY = {}
for i, m in enumerate(MIXED):
    MIXED_BY_PRIMARY.setdefault(m[0], []).append((i, m))

# --------------------------------------------------------------- context
LOCS = [  # en, hi, location_type
    ("near the school", "स्कूल के पास", "school_area"),
    ("outside the hospital", "अस्पताल के बाहर", "hospital_area"),
    ("on the main road", "मुख्य सड़क पर", "main_road"),
    ("in the market area", "बाज़ार इलाके में", "market"),
    ("in our lane", "हमारी गली में", "residential"),
    ("near our society gate", "हमारी सोसाइटी के गेट के पास", "society"),
    ("near the bus stand", "बस स्टैंड के पास", "public_place"),
]
LOC_WEIGHTS = [1, 1, 1.2, 1, 1.5, 1, 1]
P_NO_LOC = 0.30

DURS = [  # en, hi, days
    ("for the past two days", "पिछले दो दिनों से", 2),
    ("since last week", "पिछले हफ्ते से", 7),
    ("for more than a month", "एक महीने से ज़्यादा समय से", 30),
    ("for over three months", "तीन महीने से ज़्यादा समय से", 90),
]
P_NO_DUR = 0.35

DANGER = {  # category -> list of (en, hi)
    "Roads": [("Two-wheelers are slipping here daily.", "यहाँ रोज़ दोपहिया वाहन फिसल रहे हैं।"),
              ("It may cause a serious accident.", "इससे गंभीर दुर्घटना हो सकती है।"),
              ("Children and elderly people find it dangerous to walk.", "बच्चों और बुज़ुर्गों के लिए यहाँ चलना खतरनाक है।")],
    "Garbage": [("The foul smell is making it hard to breathe.", "बदबू की वजह से साँस लेना मुश्किल हो गया है।"),
                ("It may spread diseases among children.", "इससे बच्चों में बीमारियाँ फैल सकती हैं।")],
    "Water Supply": [("Many families are suffering without water.", "कई परिवार पानी के बिना परेशान हैं।"),
                     ("People may fall sick if they drink this water.", "यह पानी पीने से लोग बीमार पड़ सकते हैं।")],
    "Drainage": [("Children may fall in and get hurt.", "बच्चे गिरकर घायल हो सकते हैं।"),
                 ("The dirty water may cause diseases.", "गंदे पानी से बीमारियाँ फैल सकती हैं।")],
    "Streetlight": [("Women and children feel unsafe walking here at night.", "रात में यहाँ महिलाओं और बच्चों को चलने में असुरक्षित महसूस होता है।"),
                    ("There is a risk of accidents in the dark.", "अंधेरे में दुर्घटना का खतरा है।")],
    "Public Health": [("Children and elderly people are falling sick.", "बच्चे और बुज़ुर्ग बीमार पड़ रहे हैं।"),
                      ("There is a serious risk of disease.", "बीमारी फैलने का गंभीर खतरा है।")],
    "Encroachment": [("Pedestrians have to walk on the road, which is risky.", "पैदल चलने वालों को सड़क पर चलना पड़ता है, जो खतरनाक है।"),
                     ("Ambulances cannot pass through.", "एम्बुलेंस यहाँ से गुज़र नहीं पाती।")],
    "Other": [],
}
P_DANGER = 0.30
P_MIXED = 0.10

# frames (train vs test are disjoint)
OPEN = {
    "en": {"train": ["", "", "Hello, ", "Sir, ", "Please note: ", "Complaint: ", "Dear officer, ", "Respected sir/madam, "],
           "test": ["", "Attention: ", "I am writing to report that ", "Kindly look into this. ", "Request: "]},
    "hi": {"train": ["", "", "नमस्कार, ", "सर, ", "शिकायत: ", "कृपया ध्यान दें, ", "आदरणीय अधिकारी, ", "महोदय, "],
           "test": ["", "निवेदन है कि ", "ध्यान दीजिए: ", "सूचना: ", "मैं यह बताना चाहता हूँ कि "]},
}
CLOSE = {
    "en": {"train": ["", "", " Please take action.", " Kindly resolve this soon.", " This needs urgent attention.", " Please look into it.", " Request you to fix it at the earliest."],
           "test": ["", " Awaiting your response.", " Thank you.", " Hoping for quick action.", " Please do the needful."]},
    "hi": {"train": ["", "", " कृपया कार्रवाई करें।", " कृपया इसे जल्दी ठीक करवाएँ।", " इस पर तुरंत ध्यान देने की ज़रूरत है।", " कृपया इसे देखिए।", " जल्द से जल्द समाधान करने की कृपा करें।"],
           "test": ["", " आपके जवाब का इंतज़ार है।", " धन्यवाद।", " जल्दी कार्रवाई की उम्मीद है।", " कृपया आवश्यक कार्यवाही करें।"]},
}

BASE_RISK = {"Roads": 1, "Drainage": 1, "Streetlight": 1, "Public Health": 1,
             "Water Supply": 1, "Garbage": 0, "Encroachment": 0, "Other": 0}


def split_of(i, n):
    """index i of n items -> 'test' for every third item, else 'train'"""
    return "test" if i % 3 == 2 else "train"


def noise(text, lang):
    r = random.random()
    if lang == "en":
        if r < 0.12:
            words = text.split()
            cand = [k for k, w in enumerate(words) if len(re.sub(r"\W", "", w)) > 5]
            if cand:
                k = random.choice(cand)
                w = words[k]
                pos = random.randint(1, len(w) - 3)
                kind = random.choice(["swap", "drop", "double"])
                if kind == "swap":
                    w = w[:pos] + w[pos + 1] + w[pos] + w[pos + 2:]
                elif kind == "drop":
                    w = w[:pos] + w[pos + 1:]
                else:
                    w = w[:pos] + w[pos] + w[pos:]
                words[k] = w
                text = " ".join(words)
        if random.random() < 0.12:
            text = text.lower()
        if random.random() < 0.10:
            text = text.rstrip(". ")
    else:
        if r < 0.10:
            text = text.replace("़", "")        # dropped nukta, very common in real typing
        if random.random() < 0.10:
            text = text.rstrip("। ")
    return text


def make_row(cat, lang, part):
    L = 0 if lang == "en" else 1
    # choose issue or mixed sentence
    secondary, critical = "", 0
    use_mixed = cat in MIXED_BY_PRIMARY and random.random() < P_MIXED
    pool = []
    if use_mixed:
        pool = [m for i, m in MIXED_BY_PRIMARY[cat] if split_of(i, len(MIXED)) == part]
    if pool:
        m = random.choice(pool)
        issue = m[2 + L]
        secondary = m[1]
    else:
        pool = [it for i, it in enumerate(ISSUES[cat]) if split_of(i, len(ISSUES[cat])) == part]
        it = random.choice(pool)
        issue, critical = it[L], it[2]

    loc = dur = None
    danger = None
    if cat != "Other":
        if random.random() > P_NO_LOC:
            loc = random.choices(LOCS, weights=LOC_WEIGHTS)[0]
        if random.random() > P_NO_DUR:
            dur = random.choice(DURS)
        if DANGER[cat] and random.random() < P_DANGER:
            danger = random.choice(DANGER[cat])

    if lang == "en":
        body = issue
        if loc:
            body += " " + loc[0]
        if dur:
            body += " " + dur[0]
        body += "."
        if danger:
            body += " " + danger[0]
    else:
        pre = " ".join(x for x in [loc[1] if loc else "", dur[1] if dur else ""] if x)
        body = (pre + " " + issue if pre else issue) + "।"
        if danger:
            body += " " + danger[1]

    op = random.choice(OPEN[lang][part])
    cl = random.choice(CLOSE[lang][part])
    if lang == "en" and op.strip().endswith(",") and body[:1].isupper() and not body.startswith("I "):
        body = body[0].lower() + body[1:]
    if lang == "en" and op.endswith("that ") and body[:1].isupper():
        body = body[0].lower() + body[1:]
    if lang == "hi" and op.endswith("कि "):
        pass
    text = noise((op + body + cl).strip(), lang)

    # reference priority (ONLY for testing the rule engine; see README note)
    days = dur[2] if dur else 0
    loc_type = loc[2] if loc else "other"
    if critical:
        priority = "critical"
    else:
        score = BASE_RISK[cat]
        score += 2 if danger else 0
        score += 2 if loc_type in ("school_area", "hospital_area") else (1 if loc_type == "main_road" else 0)
        score += 1 if days >= 30 else 0
        if cat == "Other":
            priority = "low"
        elif score >= 4:
            priority = "high"
        elif score >= 2:
            priority = "medium"
        else:
            priority = "low"

    return {
        "text": text,
        "language": "English" if lang == "en" else "Hindi",
        "category": cat,
        "department": DEPT[cat],
        "secondary_category": secondary,
        "priority": priority,
        "location_type": loc_type,
        "duration_days": days,
        "has_safety_risk": int(bool(danger) or bool(critical)),
        "split": part,
        "source": "synthetic_template",
    }


def build():
    rows, seen = [], set()
    for part, n in (("train", N_TRAIN_PER_CELL), ("test", N_TEST_PER_CELL)):
        for cat in DEPT:
            for lang in ("en", "hi"):
                made, tries = 0, 0
                while made < n and tries < n * 60:
                    tries += 1
                    r = make_row(cat, lang, part)
                    if r["text"] in seen:
                        continue
                    seen.add(r["text"])
                    rows.append(r)
                    made += 1
                if made < n:
                    print(f"WARNING: only {made}/{n} unique rows for {part}/{cat}/{lang}")
    df = pd.DataFrame(rows).sample(frac=1, random_state=42).reset_index(drop=True)
    df.insert(0, "complaint_id", range(1, len(df) + 1))
    return df


if __name__ == "__main__":
    df = build()
    df.to_csv("complaints_full.csv", index=False, encoding="utf-8-sig")
    df[df.split == "train"].to_csv("complaints_train.csv", index=False, encoding="utf-8-sig")
    df[df.split == "test"].to_csv("complaints_test.csv", index=False, encoding="utf-8-sig")
    print(df.shape)
    print(df.groupby(["split", "language"]).size())
    print(df.category.value_counts())
    print(df.priority.value_counts(normalize=True).round(3))
