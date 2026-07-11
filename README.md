# MABUHAY Social Scheduler

Kostenlose Auto-Posting-Pipeline für Instagram + Facebook über Metas offizielle API,
gesteuert von GitHub Actions. Kein Metricool, kein Abo. Läuft in der Cloud —
unabhängig davon, ob dein Mac an ist.

## Wie es funktioniert
- `calendar.json` = der Redaktionsplan: was wird wann auf welcher Plattform gepostet.
- Eine GitHub Action läuft alle 15 Minuten, prüft den Plan und postet, was fällig ist.
- Bilder liegen im `images/`-Ordner und werden über die öffentliche GitHub-URL an
  Instagram übergeben (Instagram braucht öffentlich erreichbare Bild-URLs).
- `posted.json` merkt sich, was schon raus ist — nichts wird doppelt gepostet.

---

## Einmalige Einrichtung (ca. 10 Min)

### 1. Neues **öffentliches** GitHub-Repo anlegen
Name z. B. `mabuhay-social`. Öffentlich, weil Instagram die Bilder öffentlich
abrufen können muss. Der Token wird trotzdem NICHT sichtbar (siehe Schritt 3 —
GitHub-Secrets sind verschlüsselt, auch in öffentlichen Repos).

### 2. Diesen Ordner ins Repo pushen
Den kompletten Inhalt dieses Ordners (`mabuhay-social/`) hochladen: über die
GitHub-Weboberfläche („Add file → Upload files", den ganzen Ordnerinhalt reinziehen)
oder per Git:
```
cd mabuhay-social
git init && git add . && git commit -m "init"
git branch -M main
git remote add origin https://github.com/<DEIN-NAME>/mabuhay-social.git
git push -u origin main
```

### 3. Token als **Secret** + IDs als **Variables** hinterlegen
Im Repo: **Settings → Secrets and variables → Actions**
- Tab **Secrets** → „New repository secret":
  - Name: `META_TOKEN` · Wert: der lange System-User-Token (aus `meta-token.env`)
- Tab **Variables** → „New repository variable" (zwei Stück):
  - `PAGE_ID` = `1247622875096090`
  - `IG_BUSINESS_ID` = `17841415578467690`

### 4. Fertig
Die Action läuft automatisch alle 15 Min. Zum sofortigen Test:
**Actions → „MABUHAY Social Scheduler" → „Run workflow"**.

---

## Alltag: neue Posts einplanen

1. **Bild(er) vorbereiten**: neue Karten als PNG in den Projektordner
   `Marketing/Ready to Post` legen, dann lokal
   `python prep_images.py` laufen lassen → erzeugt optimierte JPEGs in `images/`.
   (JPEG + < 8 MB ist Pflicht für Instagram — das Script erledigt das.)
2. **Eintrag in `calendar.json`** ergänzen (Format siehe unten).
3. Beides committen/pushen. Die Action macht den Rest.

### calendar.json — Format
```json
{
  "id": "eindeutige-id",                       // frei wählbar, nur einmal verwenden
  "datetime": "2026-07-15T18:00:00+02:00",     // ISO, +02:00 = deutsche Sommerzeit
  "platforms": ["instagram", "facebook"],       // eine oder beide
  "type": "single",                             // "single" oder "carousel"
  "images": ["datei.jpg"],                      // 1 Bild (single) oder 2-10 (carousel)
  "caption": "Text …\n\n#hashtags"              // \n = Zeilenumbruch
}
```

Wichtig:
- **Vergangene `datetime`-Werte werden beim nächsten Lauf sofort gepostet.** Setze
  Zeiten immer in die Zukunft.
- IDs nie wiederverwenden — sonst denkt der Scheduler, der Post sei schon raus.
- Instagram-Limit: max. 25 API-Posts pro 24 h (für uns weit mehr als genug).

---

## Sicherheit
- Der Token steht **nur** als GitHub-Secret, nie im Code oder in `calendar.json`.
- `.gitignore` schließt jede `.env` aus — die lokale `meta-token.env` landet nie im Repo.
- Token verloren/kompromittiert? Im Meta Business Manager unter dem System-Nutzer
  „Tokens widerrufen", neuen generieren, Secret `META_TOKEN` aktualisieren.

## Dateien
| Datei | Zweck |
|---|---|
| `poster.py` | Posting-Engine (IG single/carousel, FB photo/album) |
| `run_scheduler.py` | prüft Kalender, postet Fälliges, schreibt `posted.json` |
| `prep_images.py` | PNG → Instagram-taugliches JPEG |
| `calendar.json` | der Redaktionsplan |
| `posted.json` | Zustand (wird automatisch gepflegt) |
| `.github/workflows/scheduler.yml` | der 15-Min-Cron |
