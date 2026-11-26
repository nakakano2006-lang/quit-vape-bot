<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Свобода от никотина</title>
  <script src="https://telegram.org/js/telegram-web-app.js"></script>
  <style>
    :root {
      --bg: var(--tg-theme-bg-color, #121417);
      --card: var(--tg-theme-secondary-bg-color, #1d2127);
      --text: var(--tg-theme-text-color, #f3f5f8);
      --hint: var(--tg-theme-hint-color, #9aa3b2);
      --accent: var(--tg-theme-button-color, #2ea6ff);
      --accent-text: var(--tg-theme-button-text-color, #ffffff);
      --danger: #e5484d;
    }

    * {
      box-sizing: border-box;
    }

    body {
      margin: 0;
      padding: 20px 16px 32px;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background: var(--bg);
      color: var(--text);
    }

    .card {
      background: var(--card);
      border-radius: 18px;
      padding: 20px;
      margin-bottom: 14px;
    }

    .label {
      font-size: 13px;
      color: var(--hint);
      margin-bottom: 8px;
    }

    .timer {
      font-size: 28px;
      font-weight: 700;
      line-height: 1.25;
      letter-spacing: -0.02em;
    }

    .sub {
      margin-top: 8px;
      font-size: 14px;
      color: var(--hint);
    }

    button {
      width: 100%;
      border: none;
      border-radius: 14px;
      padding: 15px 16px;
      font-size: 16px;
      font-weight: 600;
      cursor: pointer;
      margin-bottom: 10px;
    }

    .btn-primary {
      background: var(--accent);
      color: var(--accent-text);
    }

    .btn-danger {
      background: rgba(229, 72, 77, 0.16);
      color: #ff7b80;
    }

    .craving-box {
      display: none;
      background: var(--card);
      border-radius: 18px;
      padding: 18px;
      margin-top: 8px;
      border: 1px solid rgba(255, 255, 255, 0.08);
    }

    .craving-box.active {
      display: block;
    }

    .countdown {
      font-size: 32px;
      font-weight: 700;
      margin: 8px 0 12px;
      color: var(--accent);
    }

    .quote {
      font-size: 15px;
      line-height: 1.45;
    }
  </style>
</head>
<body>
  <div class="card">
    <div class="label">Без пара и никотина</div>
    <div class="timer" id="elapsed">0 дн. 0 ч. 0 мин. 0 сек.</div>
    <div class="sub" id="sinceText"></div>
  </div>

  <button class="btn-primary" id="cravingBtn">Тяжело (таймер 15 минут)</button>
  <button class="btn-danger" id="resetBtn">Сбросить прогресс</button>

  <div class="craving-box" id="cravingBox">
    <div class="label">Пережди волну тяги</div>
    <div class="countdown" id="countdown">15:00</div>
    <div class="quote" id="quoteText"></div>
  </div>

  <script>
    const tg = window.Telegram && window.Telegram.WebApp ? window.Telegram.WebApp : null;
    if (tg) {
      tg.ready();
      tg.expand();
    }

    const MOTIVATIONS = [
      "Тяга накрывает волной и обычно отпускает через несколько минут. Дай себе 15 минут — не нужно решать за всю жизнь прямо сейчас.",
      "Парение не снимет напряжение: никотин сначала искусственно подгоняет пульс, а потом возвращает тебя в тот же дискомфорт, только с чувством проигрыша.",
      "Вдохни глубоко на 4 секунды, задержи на 4, выдохни на 6. Сделай так 5 раз и выпей стакан прохладной воды.",
      "Ты уже вложил в это время и силы. Сделать одну затяжку — значит отмотать счётчик и снова проходить первые самые шумные дни.",
      "Мозг просто требует быстрый дофамин по старой привычке. Переключи внимание на дело руками на ближайшие 15 минут.",
      "Через полчаса, если не сорвёшься, ты скажешь себе спасибо. Держи курс — каждый трезвый час укрепляет контроль."
    ];

    const STORAGE_START_KEY = "smoke_free_start_ms";
    const STORAGE_CRAVING_END_KEY = "craving_timer_end_ms";
    const STORAGE_QUOTE_KEY = "craving_active_quote";

    let alertShownForCurrentTimer = false;

    function getStartMs() {
      let val = Number(localStorage.getItem(STORAGE_START_KEY));
      if (!val || Number.isNaN(val)) {
        val = Date.now();
        localStorage.setItem(STORAGE_START_KEY, String(val));
      }
      return val;
    }

    function updateElapsed() {
      const startMs = getStartMs();
      const diffSec = Math.max(0, Math.floor((Date.now() - startMs) / 1000));

      const days = Math.floor(diffSec / 86400);
      const hours = Math.floor((diffSec % 86400) / 3600);
      const minutes = Math.floor((diffSec % 3600) / 60);
      const seconds = diffSec % 60;

      document.getElementById("elapsed").textContent =
        `${days} дн. ${hours} ч. ${minutes} мин. ${seconds} сек.`;

      const d = new Date(startMs);
      document.getElementById("sinceText").textContent =
        `Старт: ${d.toLocaleString("ru-RU")}`;
    }

    function updateCravingTimer() {
      const endMs = Number(localStorage.getItem(STORAGE_CRAVING_END_KEY) || 0);
      const box = document.getElementById("cravingBox");
      const quoteEl = document.getElementById("quoteText");
      const cdEl = document.getElementById("countdown");

      if (!endMs) {
        box.classList.remove("active");
        return;
      }

      const leftSec = Math.ceil((endMs - Date.now()) / 1000);
      if (leftSec <= 0) {
        localStorage.removeItem(STORAGE_CRAVING_END_KEY);
        localStorage.removeItem(STORAGE_QUOTE_KEY);
        box.classList.remove("active");

        if (!alertShownForCurrentTimer) {
          alertShownForCurrentTimer = true;
          const msg = "15 минут прошли! Ты удержался — отличный шаг вперёд.";
          if (tg && typeof tg.showAlert === "function") {
            tg.showAlert(msg);
          } else {
            alert(msg);
          }
        }
        return;
      }

      box.classList.add("active");
      quoteEl.textContent = localStorage.getItem(STORAGE_QUOTE_KEY) || MOTIVATIONS[0];
      const m = String(Math.floor(leftSec / 60)).padStart(2, "0");
      const s = String(leftSec % 60).padStart(2, "0");
      cdEl.textContent = `${m}:${s}`;
    }

    document.getElementById("cravingBtn").addEventListener("click", () => {
      const quote = MOTIVATIONS[Math.floor(Math.random() * MOTIVATIONS.length)];
      const endMs = Date.now() + 15 * 60 * 1000;
      alertShownForCurrentTimer = false;
      localStorage.setItem(STORAGE_CRAVING_END_KEY, String(endMs));
      localStorage.setItem(STORAGE_QUOTE_KEY, quote);
      updateCravingTimer();
    });

    document.getElementById("resetBtn").addEventListener("click", () => {
      const runReset = () => {
        const now = Date.now();
        localStorage.setItem(STORAGE_START_KEY, String(now));
        localStorage.removeItem(STORAGE_CRAVING_END_KEY);
        localStorage.removeItem(STORAGE_QUOTE_KEY);
        alertShownForCurrentTimer = false;
        updateElapsed();
        updateCravingTimer();
        if (tg && typeof tg.sendData === "function") {
          tg.sendData(JSON.stringify({ action: "reset", start_time: new Date(now).toISOString() }));
        }
      };

      if (tg && typeof tg.showConfirm === "function") {
        tg.showConfirm("Точно сбросить прогресс и начать отсчёт заново?", (confirmed) => {
          if (confirmed) runReset();
        });
      } else if (confirm("Точно сбросить прогресс и начать отсчёт заново?")) {
        runReset();
      }
    });

    updateElapsed();
    updateCravingTimer();
    setInterval(() => {
      updateElapsed();
      updateCravingTimer();
    }, 1000);
  </script>
</body>
</html>
