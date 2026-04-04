# GitHub Setup

## Repository

**URL:** `https://github.com/christruediger/LEDFX-Hassio`

---

## Dateien pushen (Git CLI)

```bash
cd /path/to/ledfx_integration

git init
git add .
git commit -m "v1.1.0 – Color Lock, Light entity, Number sliders"
git remote add origin https://github.com/christruediger/LEDFX-Hassio.git
git branch -M main
git push -u origin main
```

---

## Release erstellen (für HACS erforderlich)

1. GitHub → Repository → **Releases** → **Create a new release**
2. Tag: `v1.1.0`
3. Title: `v1.1.0 – Color Lock & expanded controls`
4. Description:

```
## What's new in v1.1.0

- **Color Lock** — Set a color via the light entity and it persists across all effect changes
- **Light entity** — Full RGB color picker + brightness control per virtual
- **Number sliders** — Speed, blur, and intensity sliders for each virtual
- **Faster sync** — Polling interval reduced from 30s to 5s
- **Performance** — Effects schema cached at startup, no redundant API calls
- **Fixed** — Default config extraction when switching effects
```

5. **Publish release**

---

## HACS einrichten

1. Home Assistant → HACS → Integrations
2. Drei Punkte oben rechts → **Custom repositories**
3. URL: `https://github.com/christruediger/LEDFX-Hassio`
4. Kategorie: **Integration**
5. **Add** → in HACS nach **LEDFX** suchen → Download

---

## Updates veröffentlichen

1. Änderungen committen und pushen
2. Neue Release erstellen mit erhöhter Versionsnummer (`v1.1.1`, `v1.2.0`, …)
3. Version in `manifest.json` und `hacs.json` aktuell halten
4. HACS-Nutzer sehen das Update automatisch
