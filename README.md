# רשימת אריזה משפחתית לחופשות 🧳
### Self-Hosted Family Vacation Packing App (Hebrew / RTL)

אפליקציית ווב מתקדמת לניהול רשימות אריזה לחופשות משפחתיות בריבוי משתמשים ובזמן אמת (Real-Time WebSockets), המיועדת להרצה עצמית (Self-Hosted) על גבי שרת Proxmox בתוך קונטיינר LXC קל משקל (Debian), ללא תקורה של Docker ובצריכת זיכרון מינימלית (פחות מ-60MB RAM פעיל).

---

## 🌟 מאפיינים עיקריים (Key Features)

- **ממשק עברי מלא (RTL First):** מותאם מן היסוד לשפה העברית (`dir="rtl"`), כולל כיווניות של פסי התקדמות, כפתורים, מודאלים וטיפוגרפיה מודרנית (Rubik / Heebo).
- **סנכרון בזמן אמת (WebSockets):** סימון פריט שנארז, הוספת פריט או עדכון כמות בטלפון של אחד מבני המשפחה מתעדכן מיד בכל המכשירים האחרים ללא צורך ברענון העמוד!
- **עדכונים גרנולריים ומניעת דריסות (Granular Updates):** שינויים נשמרים ברמת הפריט והשדה (PATCH סלקטיבי) ולא כקובץ JSON בודד הנדרס בשלמותו. שני אנשים יכולים לערוך במקביל פריטים שונים ללא התנגשויות.
- **תבניות בסיס ושכפול חופשות:** יצירת חופשות חדשות מתוך תבניות מוכנות (למשל "חופשה בחו״ל", "סופ״ש קמפינג") בלחיצת כפתור—הקטגוריות והפריטים מועתקים וכל הסימונים מתאפסים.
- **נתוני התחלה בעברית (Seed Data):** בהפעלה הראשונה נוצרות תבניות עשירות למשפחה ישראלית (מסמכים וכסף, ביגוד, פארם וטואלטיקה, אלקטרוניקה, ציוד לילדים).
- **שיוך לבני משפחה:** הגדרת תגיות אישיות לחברי המשפחה (אבא, אמא, ילדים, סבא, סבתא) עם צבע ואימוג׳י ייחודי, וסינון מהיר לפי מי שאחראי לארוז.
- **פס התקדמות אינטראקטיבי ודביק (Sticky Progress Bar):** מחוון אחוזים ראשי בראש העמוד המציג משוב דינמי ("בואו נתחיל לארוז", "האריזה בעיצומה", "הכל ארוז! 🎉"), לצד מיני-מחוון התקדמות בכל קטגוריה.
- **פעולות מהירות ב-WhatsApp:** העתקת סיכום מעוצב ומסודר של הרשימה (או רק הפריטים שטרם נארזו) בלחיצת כפתור להדבקה מיידית או שליחה ישירה לוואטסאפ המשפחתי.
- **גיבוי ושחזור מלא (JSON Import/Export):** ייצוא חופשה בודדת או גיבוי מלא של כל החופשות והמשתמשים לקובץ JSON, ושחזור אדיטיבי (בטוח, ללא מחיקת נתונים קיימים).
- **נגישות ומובייל:** מותאם למסכי מגע עם יעדי לחיצה נוחים (מינימום 44px), סגירה קלה של מודאלים בלחיצה על `Escape` או על הרקע (תוך שמירה על מחסנית חלונות).

---

## 🏗️ ארכיטקטורה וטכנולוגיות

```
packing-list-app/
├── app/                      # Backend (FastAPI + SQLite)
│   ├── __main__.py           # נקודת כניסה: python -m app
│   ├── main.py               # אפליקציית FastAPI, lifespan והגשת קבצים סטטיים
│   ├── config.py             # הגדרות סביבה (PACKING_*) ללא תלויות מיותרות
│   ├── db.py                 # ניהול מסד נתונים SQLite (WAL, Foreign Keys, מיגרציות)
│   ├── schemas.py            # מודלי Pydantic v2 קפדניים (extra="forbid")
│   ├── realtime.py           # מנהל חיבורי WebSockets ושידור אירועים
│   ├── repositories/         # שכבת גישה לנתונים (שאילתות SQL בלבד)
│   ├── services/             # לוגיקה עסקית (שכפול, ייבוא/ייצוא, seed data)
│   ├── api/                  # נתיבי REST ו-WebSocket
│   └── migrations/           # קובצי מיגרציה ב-SQL (0001_initial.sql)
├── frontend/                 # ממשק משתמש קל-משקל (Vanilla ES Modules, ללא צורך ב-Build)
│   ├── index.html            # דף הבית בעברית (RTL)
│   ├── manifest.webmanifest  # PWA Manifest להתקנה על מסך הבית בנייד
│   ├── icon.svg              # אייקון מזוודת חופשה
│   ├── css/                  # עיצוב מודולרי (tokens, base, layout, components)
│   └── js/                   # לוגיקת לקוח מודולרית (api, realtime, store, share, ui)
├── tests/                    # חבילת בדיקות אוטומטיות (pytest, 100+ בדיקות, >90% כיסוי)
└── deploy/                   # כלי פריסה לקונטיינר LXC
    ├── packing-list.service  # קובץ שירות systemd מוקשח
    ├── setup.sh              # סקריפט התקנה אידמפוטנטי ל-Debian
    └── env.example           # דוגמה להגדרות סביבה
```

### מסד הנתונים (SQLite Relational Model)
- **`trips`**: חופשות ותבניות (`id`, `name`, `emoji`, `is_template`, `created_at`, `updated_at`).
- **`categories`**: קטגוריות השייכות לחופשה (`trip_id`, `name`, `icon`, `position`).
- **`items`**: פריטים בקטגוריה (`category_id`, `name`, `packed`, `quantity`, `note`, `position`).
- **`family_members`**: חברי משפחה גלובליים (`name`, `color`, `emoji`, `position`).
- **`item_assignees`**: טבלת קישור רבים-לרבים (`item_id`, `member_id`).

---

## 🚀 הרצה מקומית ופיתוח (Local Development)

### דרישות מוקדמות
- Python 3.10 ומעלה

### שלבי הפעלה:
1. שכפל/היכנס לתיקיית הפרויקט:
   ```bash
   cd packing-list-app
   ```
2. צור סביבה וירטואלית והתקן תלויות פיתוח:
   ```bash
   python -m venv .venv
   source .venv/bin/activate       # בלינוקס/מק
   # או ב-Windows PowerShell:
   # .\.venv\Scripts\Activate.ps1

   pip install -r requirements-dev.txt
   ```
3. הפעל את השרת:
   ```bash
   python -m app
   ```
4. פתח את הדפדפן בכתובת: **[http://localhost:8000](http://localhost:8000)**  
   תיעוד ה-API האינטראקטיבי (Swagger) זמין בכתובת: **[http://localhost:8000/api/docs](http://localhost:8000/api/docs)**.

---

## 🧪 הרצת בדיקות (Automated Testing)

הפרויקט מגובה בחבילת בדיקות מקיפה המכסה CRUD מלא, לוגיקת שכפול תבניות, ייבוא/ייצוא, שגיאות ו-WebSockets:

```bash
pytest --cov=app --cov-report=term-missing
```

---

## 🐧 התקנה על Proxmox LXC (Debian 12 / 13)

הפרויקט נבנה מראש להרצה בקונטיינר LXC דל משאבים (1 ליבה, 256MB–512MB RAM, 2GB דיסק):

1. **צור קונטיינר LXC רגיל ב-Proxmox:**
   - תבנית: `Debian 12` או `Debian 13`.
   - משאבים: 1 vCPU, 512MB RAM, 2GB Disk.
2. **העתק את קוד הפרויקט לקונטיינר (או שכפל מ-GitHub):**
   ```bash
   git clone https://github.com/<your-user>/packing-list-app.git /opt/packing-app
   # או באמצעות scp:
   # scp -r . root@<LXC-IP>:/opt/packing-app
   ```
3. **הרץ את סקריפט ההתקנה האידמפוטנטי בתוך ה-LXC:**
   ```bash
   ssh root@<LXC-IP>
   cd /opt/packing-app
   chmod +x deploy/setup.sh
   ./deploy/setup.sh
   ```
   הסקריפט יתקין חבילות מערכת נדרשות, יקים משתמש שירות מבודד (`packing`), ייצור סביבת Python, יכין תיקיית נתונים ייעודית מבודדת ב-`/opt/packing-app/data/` לשמירת קובצי SQLite ו-WAL (`.db`, `-wal`, `-shm`), יגדיר קובץ סביבה ב-`/etc/packing-list/packing-list.env`, יפעיל שירות `systemd` ויבדוק תקינות.

4. **ניהול השירות:**
   - צפייה בלוגים חיים: `journalctl -u packing-list -f`
   - הפעלה מחדש: `systemctl restart packing-list`
   - בדיקת סטטוס: `systemctl status packing-list`

---

## 📄 רישיון
MIT License.
