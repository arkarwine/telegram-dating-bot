MESSAGES = {
    "en": {
        "welcome": "Welcome. Choose a language, complete a profile, or browse previews.",
        "help": (
            "/profile - create or edit your profile\n"
            "/browse - browse profiles\n"
            "/matches - view matches\n"
            "/settings - change language\n"
            "/help - show help"
        ),
        "language_saved": "Language saved.",
        "profile_help": (
            "Send profile details like this:\n"
            "Name: Aye\nAge: 24\nGender: female\nInterested: male\nBio: Coffee and books\n\n"
            "Then send one photo and use Telegram's location button."
        ),
        "profile_incomplete": "Your profile needs a photo, bio, age, gender, interested-in, and Myanmar location before matching.",
        "profile_complete": "Your profile is complete. You can now like profiles and match.",
        "photo_saved": "Photo saved.",
        "location_processing": "Checking your location...",
        "location_saved": "Location saved: {place}.",
        "location_rejected": "This bot is only for Myanmar. Please send a Myanmar location.",
        "no_candidates": "No more profiles right now. Try again later.",
        "anonymous_notice": "Anonymous preview mode: complete your profile before liking or matching.",
        "like_requires_profile": "Complete your profile before liking someone.",
        "passed": "Passed.",
        "liked": "Liked.",
        "match": "It's a match with {name}!",
        "contact": "Contact: @{username}",
        "contact_missing": "This match has no public Telegram username yet.",
        "blocked": "Blocked. You will not see this profile again.",
        "reported": "Reported. Thank you for helping keep the bot safe.",
        "not_admin": "Admin access required.",
        "admin_help": "/reports - latest reports\n/ban <telegram_id> - ban user\n/unban <telegram_id> - unban user",
        "no_reports": "No reports found.",
        "banned": "User banned.",
        "unbanned": "User unbanned.",
    },
    "my": {
        "welcome": "ကြိုဆိုပါတယ်။ ဘာသာစကားရွေးပြီး ပရိုဖိုင်ဖြည့်နိုင်သလို preview လည်းကြည့်နိုင်ပါတယ်။",
        "help": (
            "/profile - ပရိုဖိုင်ပြင်ရန်\n"
            "/browse - ပရိုဖိုင်များကြည့်ရန်\n"
            "/matches - match များကြည့်ရန်\n"
            "/settings - ဘာသာစကားပြောင်းရန်\n"
            "/help - အကူအညီ"
        ),
        "language_saved": "ဘာသာစကား သိမ်းပြီးပါပြီ။",
        "profile_help": (
            "ပရိုဖိုင်ကို ဒီပုံစံနဲ့ပို့ပါ:\n"
            "Name: Aye\nAge: 24\nGender: female\nInterested: male\nBio: Coffee and books\n\n"
            "ပြီးရင် ဓာတ်ပုံတစ်ပုံနဲ့ Telegram location ပို့ပါ။"
        ),
        "profile_incomplete": "Match လုပ်ရန် ဓာတ်ပုံ၊ bio၊ အသက်၊ gender၊ interested-in နဲ့ မြန်မာနိုင်ငံ location လိုအပ်ပါတယ်။",
        "profile_complete": "ပရိုဖိုင်ပြည့်စုံပါပြီ။ Like နဲ့ match လုပ်နိုင်ပါပြီ။",
        "photo_saved": "ဓာတ်ပုံ သိမ်းပြီးပါပြီ။",
        "location_processing": "Location စစ်ဆေးနေပါတယ်...",
        "location_saved": "Location သိမ်းပြီးပါပြီ: {place}။",
        "location_rejected": "ဒီ bot က မြန်မာနိုင်ငံအတွက်သာ ဖြစ်ပါတယ်။ မြန်မာနိုင်ငံ location ပို့ပါ။",
        "no_candidates": "လောလောဆယ် ပရိုဖိုင်အသစ်မရှိသေးပါ။ နောက်မှ ထပ်စမ်းပါ။",
        "anonymous_notice": "Anonymous preview mode ဖြစ်ပါတယ်။ Like/match လုပ်ရန် ပရိုဖိုင်ဖြည့်ပါ။",
        "like_requires_profile": "Like လုပ်ရန် ပရိုဖိုင်အရင်ဖြည့်ပါ။",
        "passed": "Pass လုပ်ပြီးပါပြီ။",
        "liked": "Like လုပ်ပြီးပါပြီ။",
        "match": "{name} နဲ့ match ဖြစ်ပါတယ်!",
        "contact": "Contact: @{username}",
        "contact_missing": "ဒီ match မှာ public Telegram username မရှိသေးပါ။",
        "blocked": "Block လုပ်ပြီးပါပြီ။ ဒီပရိုဖိုင်ကို ထပ်မပြတော့ပါ။",
        "reported": "Report လုပ်ပြီးပါပြီ။ ကျေးဇူးတင်ပါတယ်။",
        "not_admin": "Admin access လိုအပ်ပါတယ်။",
        "admin_help": "/reports - report များ\n/ban <telegram_id> - ban\n/unban <telegram_id> - unban",
        "no_reports": "Report မရှိသေးပါ။",
        "banned": "User ကို ban လုပ်ပြီးပါပြီ။",
        "unbanned": "User ကို unban လုပ်ပြီးပါပြီ။",
    },
}


def t(language: str | None, key: str, **kwargs: object) -> str:
    lang = language if language in MESSAGES else "en"
    template = MESSAGES[lang].get(key, MESSAGES["en"][key])
    return template.format(**kwargs)

