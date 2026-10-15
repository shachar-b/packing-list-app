"""First-boot seed data: Hebrew family members and vacation templates."""

from __future__ import annotations

import logging

from app.db import Database
from app.schemas import ExportDocument
from app.services.cloning import clone_trip
from app.services.transfer import import_document

log = logging.getLogger(__name__)

SEED_META_KEY = "seeded_at"

ALL = "כל המשפחה"
PARENTS = "הורים"
DAD = "אבא"
MOM = "אמא"
KIDS = "ילדים"


def _i(name: str, qty: int = 1, note: str | None = None, *who: str) -> dict:
    return {"name": name, "quantity": qty, "note": note, "assignees": list(who)}


SEED_DATA: dict = {
    "members": [
        {"name": ALL, "color": "#6366f1", "emoji": "👨‍👩‍👧‍👦"},
        {"name": PARENTS, "color": "#0ea5e9", "emoji": "🧑‍🤝‍🧑"},
        {"name": DAD, "color": "#10b981", "emoji": "👨"},
        {"name": MOM, "color": "#ec4899", "emoji": "👩"},
        {"name": KIDS, "color": "#f59e0b", "emoji": "🧒"},
    ],
    "trips": [
        {
            "name": "תבנית: חופשה משפחתית בחו״ל",
            "emoji": "✈️",
            "is_template": True,
            "categories": [
                {
                    "name": "מסמכים וכסף",
                    "icon": "📄",
                    "items": [
                        _i("דרכונים", 4, "לוודא תוקף של 6 חודשים לפחות", PARENTS),
                        _i("כרטיסי טיסה / כרטיסי עלייה למטוס", 1, None, PARENTS),
                        _i("פוליסת ביטוח נסיעות", 1, None, PARENTS),
                        _i("רישיון נהיגה + רישיון בינלאומי", 1, None, DAD),
                        _i("כרטיסי אשראי", 2, "להודיע לחברת האשראי על הנסיעה", PARENTS),
                        _i("מזומן במטבע מקומי", 1, None, MOM),
                        _i("אישורי הזמנה — מלון ורכב", 1, "גם מודפס וגם בטלפון", MOM),
                        _i("צילומי דרכונים בענן", 1, None, DAD),
                    ],
                },
                {
                    "name": "ביגוד והנעלה",
                    "icon": "👕",
                    "items": [
                        _i("חולצות קצרות", 7, None, ALL),
                        _i("מכנסיים", 4, None, ALL),
                        _i("תחתונים", 8, None, ALL),
                        _i("גרביים", 8, None, ALL),
                        _i("פיג׳מות", 2, None, ALL),
                        _i("בגדי ים", 2, None, ALL),
                        _i("סווטשירט / ז׳קט קל", 1, "לטיסה ולערבים", ALL),
                        _i("נעלי הליכה נוחות", 1, None, ALL),
                        _i("כפכפים", 1, None, ALL),
                        _i("כובעים ומשקפי שמש", 1, None, ALL),
                    ],
                },
                {
                    "name": "טואלטיקה ופארם",
                    "icon": "🧴",
                    "items": [
                        _i("מברשות שיניים ומשחת שיניים", 1, None, ALL),
                        _i("שמפו ומרכך בגודל טיסה", 1, "עד 100 מ״ל בתיק היד", MOM),
                        _i("דאודורנט", 2, None, PARENTS),
                        _i("קרם הגנה", 2, None, ALL),
                        _i("ערכת עזרה ראשונה", 1, "פלסטרים, אקמול, נורופן לילדים, מדחום", MOM),
                        _i("תרופות קבועות", 1, "בתיק היד!", PARENTS),
                        _i("משחה נגד עקיצות", 1, None, KIDS),
                        _i("מגבונים לחים", 2, None, KIDS),
                        _i("מכונת גילוח", 1, None, DAD),
                    ],
                },
                {
                    "name": "אלקטרוניקה",
                    "icon": "🔌",
                    "items": [
                        _i("טלפונים ומטענים", 1, None, ALL),
                        _i("מטען נייד (פאוור בנק)", 2, "רק בתיק היד — אסור במזוודה", PARENTS),
                        _i("מתאם חשמל לחו״ל", 2, None, DAD),
                        _i("אוזניות", 4, None, ALL),
                        _i("טאבלט עם סרטים שהורדו מראש", 1, None, KIDS),
                        _i("מחזיק טלפון לרכב", 1, None, DAD),
                    ],
                },
                {
                    "name": "ילדים וציוד לטיולי יום",
                    "icon": "🎒",
                    "items": [
                        _i("עגלה / מנשא", 1, None, PARENTS),
                        _i("בקבוקי מים", 4, None, ALL),
                        _i("חטיפים לדרך", 1, None, MOM),
                        _i("משחקים וספרים לטיסה", 1, None, KIDS),
                        _i("תיק גב קטן לטיולים", 2, None, KIDS),
                        _i("בובה / שמיכי אהובה", 1, "לא לשכוח במלון!", KIDS),
                        _i("שקיות לכביסה מלוכלכת", 3, None, MOM),
                    ],
                },
            ],
        },
        {
            "name": "תבנית: סופ״ש קמפינג",
            "emoji": "⛺",
            "is_template": True,
            "categories": [
                {
                    "name": "לינה",
                    "icon": "🏕️",
                    "items": [
                        _i("אוהל + יתדות", 1, None, DAD),
                        _i("שקי שינה", 4, None, ALL),
                        _i("מזרנים מתנפחים + משאבה", 2, None, DAD),
                        _i("כריות", 4, None, ALL),
                        _i("פנסי ראש", 4, "לבדוק סוללות", ALL),
                    ],
                },
                {
                    "name": "מטבח שטח",
                    "icon": "🍳",
                    "items": [
                        _i("גזייה + מיכל גז", 1, None, DAD),
                        _i("סיר, מחבת וקומקום", 1, None, MOM),
                        _i("צלחות, כוסות וסכו״ם רב-פעמיים", 1, None, MOM),
                        _i("צידנית + קרחונים", 1, None, PARENTS),
                        _i("מים", 12, "ליטרים", ALL),
                        _i("שקיות זבל", 5, None, PARENTS),
                    ],
                },
                {
                    "name": "ביגוד והנעלה",
                    "icon": "👕",
                    "items": [
                        _i("בגדים חמים ללילה", 1, None, ALL),
                        _i("נעלי שטח", 1, None, ALL),
                        _i("כובעים", 1, None, ALL),
                    ],
                },
                {
                    "name": "טואלטיקה ופארם",
                    "icon": "🧴",
                    "items": [
                        _i("קרם הגנה", 1, None, ALL),
                        _i("דוחה יתושים", 1, None, ALL),
                        _i("נייר טואלט", 2, None, PARENTS),
                        _i("ערכת עזרה ראשונה", 1, None, MOM),
                    ],
                },
                {
                    "name": "ילדים ופנאי",
                    "icon": "🎒",
                    "items": [
                        _i("משחקי קופסה / קלפים", 1, None, KIDS),
                        _i("כדור", 1, None, KIDS),
                        _i("מרשמלו לקומזיץ", 1, None, KIDS),
                    ],
                },
            ],
        },
        {
            "name": "תבנית: סופ״ש בצימר בצפון 🏡🌿",
            "emoji": "🏡",
            "is_template": True,
            "categories": [
                {
                    "name": "בריכה ומים",
                    "icon": "🏊‍♂️",
                    "items": [
                        _i("נודל וגלשני קצף", 1, "מתנפחים וגלשנים לבריכה", KIDS),
                        _i("מתנפחים גדולים", 1, "אבובים / מזרני ים גדולים", KIDS),
                        _i("משאבה / מפוח למתנפחים", 1, "לניפוח מהיר של המתנפחים הגדולים", PARENTS),
                        _i("דברי בריכה", 1, "משקפות שחייה, מצופים ומשחקי בריכה לילדים", KIDS),
                        _i("מגבות בריכה מהבית", 5, "המגבות האהובות שלנו לבריכה ולדשא (אחת לכל אחד)", ALL),
                        _i("בגדי ים", 5, "בגד ים לכל אחד מבני המשפחה", ALL),
                        _i("כפכפים", 5, "זוג כפכפים לכל אחד לבריכה", ALL),
                        _i("נעלי מים", 5, "לטבילה בנחלים ובמעיינות באזור", ALL),
                    ],
                },
                {
                    "name": "ביגוד והנעלה",
                    "icon": "👕",
                    "items": [
                        _i("בגדים ליומיום", 15, "3 סטים מלאים לכל אחד (חמישי, שישי, שבת)", ALL),
                        _i("תחתונים", 15, "3 לכל אחד", ALL),
                        _i("פיג׳מות", 5, "סט פיג'מה לכל אחד", ALL),
                        _i("כובעים", 5, "כובע שמש רחב שוליים לכל אחד", ALL),
                    ],
                },
                {
                    "name": "פארם, רחצה והיגיינה",
                    "icon": "🧴",
                    "items": [
                        _i("אופטלגין / משככי כאבים למבוגרים", 1, "משככי כאבים וכדורים", PARENTS),
                        _i("תרופות להורדת חום לילדים", 1, "נובימול / נורופן + מזרק מדידה", PARENTS),
                        _i("ערכת עזרה ראשונה", 1, "פלסטרים, פולידין, פדים לחבישה ותחבושת אלסטית", PARENTS),
                        _i("קרם הגנה", 2, "מקדם הגנה SPF גבוה לילדים ולמבוגרים", ALL),
                        _i("תכשיר נגד יתושים", 1, "אל-תוש / ספריי דוחה יתושים לצפון", PARENTS),
                        _i("קרמים ואיפור לאמא", 1, None, MOM),
                        _i("דאודורנטים", 2, "דאודורנט להורים", PARENTS),
                        _i("סבון גוף", 1, None, ALL),
                        _i("שמפו ומרכך", 1, None, ALL),
                        _i("משחות ומברשות שיניים", 5, "מברשת לכל אחד + משחת שיניים ילדים ומבוגרים", ALL),
                        _i("מגבונים רגילים", 2, "חבילות סגורות לנסיעה ולצימר", PARENTS),
                        _i("מגבונים נשטפים", 2, None, ALL),
                    ],
                },
                {
                    "name": "אלקטרוניקה וגאדג'טים",
                    "icon": "🔌",
                    "items": [
                        _i("מטען 3 ב-1", 1, "לטעינת טלפון, שעון חכם ואוזניות בעמדה אחת", DAD),
                        _i("מחשב נייד", 1, "כולל מטען למחשב", DAD),
                        _i("מטען עם כבל ארוך לאמא", 1, "כבל טעינה ארוך למיטה", MOM),
                        _i("תחנת טעינה לטלפונים", 1, "עמדת טעינה מרכזית: 3 כבלי Lightning + 2 כבלי Type-C", PARENTS),
                    ],
                },
                {
                    "name": "אוכל, שתייה ומטבח",
                    "icon": "🍳",
                    "items": [
                        _i("יין", 2, "בקבוקי יין אדום/לבן לערב במרפסת", PARENTS),
                        _i("פותחן יין", 1, "שלא ניתקע בלי פותחן!", PARENTS),
                        _i("נינג׳ה גריל", 1, "כולל כבל חשמל ורשתות צלייה", PARENTS),
                        _i("מקציף חלב נספרסו", 1, "לקפה מפנק של בוקר", PARENTS),
                        _i("קטשופ", 1, None, ALL),
                        _i("מיוטשופ", 1, None, ALL),
                        _i("חטיפים לנסיעה", 1, "נשנושים לדרך באוטו לילדים", KIDS),
                        _i("פנקייקים", 1, "פנקייקים מוכנים בקופסה לנשנוש בדרך באוטו! 🥞", ALL),
                    ],
                },
                {
                    "name": "פנאי, משחקים וספורט",
                    "icon": "🎲",
                    "items": [
                        _i("טאקי", 1, "קלפי טאקי למשחק משפחתי", ALL),
                        _i("משחקי קופסא", 2, "משחקים שמתאימים לערב בצימר", ALL),
                        _i("דברי יצירה", 1, "טושים, דפי ציור ומדבקות לילדים לשעות החמות", KIDS),
                        _i("כדורגל", 1, "לדשא בצימר", ALL),
                        _i("פריזבי", 1, "למשחק במדשאה", ALL),
                        _i("תיקי מים", 2, "שלוקרים 2-3 ליטר לטיולים רגליים", PARENTS),
                    ],
                },
            ],
        },
    ],
}


def seed_if_needed(db: Database) -> bool:
    """Populate an empty database once, or add newly released default templates on upgrade."""
    seeded = False
    with db.transaction():
        # First-boot seeding
        if db.get_meta(SEED_META_KEY) is None:
            has_data = db.fetchone("SELECT (SELECT COUNT(*) FROM trips) + (SELECT COUNT(*) FROM family_members)")[0]
            if not has_data:
                doc = ExportDocument.model_validate(SEED_DATA)
                trip_ids, _ = import_document(db, doc)
                clone_trip(db, trip_ids[0], name="חופשת הקיץ שלנו", emoji="☀️")
                seeded = True
                log.info("Seeded database with default templates")
            db.set_meta(SEED_META_KEY, "1")
            db.set_meta("seed_cabin_template_v1", "1")
        elif db.get_meta("seed_cabin_template_v1") is None:
            # Upgrade seeding: add the cabin template if missing (runs once per version)
            existing = {r[0].casefold() for r in db.fetchall("SELECT name FROM trips WHERE is_template = 1")}
            cabin_template = next(t for t in SEED_DATA["trips"] if "צימר בצפון" in t["name"])
            if cabin_template["name"].casefold() not in existing:
                doc = ExportDocument.model_validate({
                    "members": SEED_DATA["members"],
                    "trips": [cabin_template],
                })
                import_document(db, doc)
                seeded = True
                log.info("Added default cabin weekend template to database")
            db.set_meta("seed_cabin_template_v1", "1")

    return seeded
