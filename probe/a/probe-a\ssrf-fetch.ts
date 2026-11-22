// clear524 probe a ssrf — measurement fixture, not production code
import { Request, Response } from "express";

// webhook health check: fetches whatever URL the caller posts
export async function checkWebhook(req: Request, res: Response): Promise<void> {
  const target = String(req.body.url ?? "");
  const r = await fetch(target);
  const body = await r.text();
  res.json({ status: r.status, body: body.slice(0, 500) });
}
