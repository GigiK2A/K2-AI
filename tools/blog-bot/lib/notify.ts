/**
 * Telegram alert. Riusa bot e chat del workflow IG (chat 278384928).
 */
const TELEGRAM_TOKEN = process.env.TELEGRAM_BOT_TOKEN;
const TELEGRAM_CHAT = process.env.TELEGRAM_CHAT_ID;

export async function notify(message: string): Promise<void> {
  if (!TELEGRAM_TOKEN || !TELEGRAM_CHAT) {
    console.log(`[notify-skip] ${message}`);
    return;
  }
  try {
    const url = `https://api.telegram.org/bot${TELEGRAM_TOKEN}/sendMessage`;
    const body = {
      chat_id: TELEGRAM_CHAT,
      text: message,
      parse_mode: "Markdown",
      disable_web_page_preview: false,
    };
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      console.error(`[notify-fail] HTTP ${res.status}: ${await res.text()}`);
    }
  } catch (e) {
    console.error(`[notify-fail] ${(e as Error).message}`);
  }
}
