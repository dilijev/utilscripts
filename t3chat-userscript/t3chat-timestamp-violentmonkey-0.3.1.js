// ==UserScript==
// @name         T3 Chat – Message Timestamps
// @namespace    https://t3.chat/
// @version      0.3.1
// @description  Injects IndexedDB message timestamps inline (Slack-style)
// @author       Doug
// @match        https://t3.chat/*
// @grant        none
// @inject-into  page
// @run-at       document-idle
// ==/UserScript==

(function () {
  "use strict";

  const DB_NAME = "chatdb";
  const STORE = "messages";
  const ATTR = "data-message-id";
  const CLS = "t3ts";
  const LOG = "[T3Timestamps]";

  function fmt(raw) {
    try {
      const d =
        typeof raw === "string"
          ? new Date(raw)
          : raw.epochMilliseconds != null
          ? new Date(raw.epochMilliseconds)
          : new Date(raw.toString());

      if (isNaN(d)) return "?";

      const now = new Date();
      const isToday =
        d.getFullYear() === now.getFullYear() &&
        d.getMonth() === now.getMonth() &&
        d.getDate() === now.getDate();

      const t = d.toLocaleTimeString(undefined, {
        hour: "numeric",
        minute: "2-digit",
      });

      return isToday
        ? t
        : d.toLocaleDateString(undefined, { month: "short", day: "numeric" }) +
            " " +
            t;
    } catch (e) {
      console.warn(`${LOG} fmt() error for value`, raw, e);
      return String(raw);
    }
  }

  function loadAll() {
    return new Promise((resolve) => {
      console.log(`${LOG} Opening IndexedDB: "${DB_NAME}"`);
      const req = indexedDB.open(DB_NAME);

      req.onerror = (e) => {
        console.error(`${LOG} Failed to open DB`, e);
        resolve(new Map());
      };

      req.onsuccess = ({ target: { result: db } }) => {
        console.log(`${LOG} DB opened. Stores:`, [...db.objectStoreNames]);

        if (!db.objectStoreNames.contains(STORE)) {
          console.warn(`${LOG} Store "${STORE}" not found`);
          db.close();
          return resolve(new Map());
        }

        const map = new Map();
        let rowCount = 0;

        const cur = db
          .transaction(STORE, "readonly")
          .objectStore(STORE)
          .openCursor();

        cur.onsuccess = ({ target: { result: c } }) => {
          if (!c) {
            console.log(
              `${LOG} Cursor done. Scanned: ${rowCount}, mapped: ${map.size}`
            );
            db.close();
            return resolve(map);
          }

          rowCount++;
          const { id, created_at } = c.value;

          if (rowCount <= 3) {
            console.log(`${LOG} Sample record [${rowCount}]:`, c.value);
          }

          if (id != null && created_at != null) {
            map.set(id, created_at);
          } else if (rowCount <= 3) {
            console.warn(
              `${LOG} Record missing "id" or "created_at". Keys:`,
              Object.keys(c.value)
            );
          }

          c.continue();
        };

        cur.onerror = (e) => {
          console.error(`${LOG} Cursor error`, e);
          resolve(map);
        };
      };
    });
  }

  function injectStamp(el, ts) {
    if (el.querySelector(`.${CLS}`)) return;

    const span = Object.assign(document.createElement("span"), {
      className: CLS,
      textContent: fmt(ts),
    });
    span.style.cssText =
      "display:inline-block;font-size:11px;color:#888;opacity:.75;user-select:none;vertical-align:middle";

    // User message footer: inject as first element
    if (el.classList.contains("absolute") && el.classList.contains("right-0")) {
      span.style.marginRight = "8px";
      el.insertBefore(span, el.firstChild);
      console.log(`${LOG} Injected timestamp as first element in user footer`, el);
      return;
    }

    // Bot response footer: inject as last element
    if (el.classList.contains("absolute") && el.classList.contains("left-0")) {
      span.style.marginLeft = "8px";
      el.appendChild(span);
      console.log(`${LOG} Injected timestamp as last element in bot footer`, el);
      return;
    }

    // Fallback: original behavior
    const target = el.querySelector('[role="article"]') ?? el;
    target.appendChild(span);
    console.log(`${LOG} Injected timestamp (fallback) into`, target);
  }

  async function run() {
    const map = await loadAll();
    const msgEls = document.querySelectorAll(`[${ATTR}]`);

    console.log(`${LOG} DOM message elements found: ${msgEls.length}`);
    if (!msgEls.length) {
      console.warn(`${LOG} No elements with [${ATTR}] found`);
    }

    let injected = 0;
    let missing = 0;

    for (const el of msgEls) {
      const id = el.getAttribute(ATTR);
      const ts = map.get(id);
      if (ts) {
        injectStamp(el, ts);
        injected++;
      } else {
        console.warn(`${LOG} No IDB record for message id: "${id}"`);
        missing++;
      }
    }

    console.log(
      `${LOG} run() done — injected: ${injected}, missing: ${missing}`
    );
  }

  let timer = null;
  new MutationObserver(() => {
    clearTimeout(timer);
    timer = setTimeout(run, 400);
  }).observe(document.body, { childList: true, subtree: true });

  console.log(`${LOG} Script loaded, running initial pass`);
  run();
})();