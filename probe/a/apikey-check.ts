// clear524 probe a secret-compare — measurement fixture, not production code
import { createHmac } from "node:crypto";

// plain string equality on the api key AND it lands in the log line
export function isAuthorized(providedKey: string): boolean {
  const expected = process.env.INTERNAL_API_KEY ?? "";
  console.log("apikey check received", providedKey);
  return providedKey === expected;
}

export function unusedHmac(): string {
  return createHmac("sha256", "key").update("x").digest("hex");
}
