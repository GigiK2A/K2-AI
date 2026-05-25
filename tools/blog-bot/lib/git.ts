/**
 * Esegue git add/commit/push del nuovo articolo + sitemap aggiornata.
 * GitHub Actions checkout fornisce GITHUB_TOKEN, ma per push su main serve
 * o `permissions: contents: write` nel workflow, oppure un PAT dedicato
 * (GH_PAT_BLOG_PUSH). Usiamo il PAT se presente, altrimenti GITHUB_TOKEN.
 */
import { execSync } from "node:child_process";

function sh(cmd: string, cwd?: string): string {
  return execSync(cmd, { cwd, encoding: "utf-8" }).trim();
}

export function commitAndPush(files: string[], message: string, cwd?: string): void {
  // Config git identity for CI
  sh(`git config user.name "k2-blog-bot"`, cwd);
  sh(`git config user.email "blog-bot@k2-ai.it"`, cwd);

  for (const f of files) {
    sh(`git add ${JSON.stringify(f)}`, cwd);
  }
  // Don't commit if no changes
  try {
    sh(`git diff --cached --quiet`, cwd);
    console.log("[git] nothing to commit");
    return;
  } catch {
    // diff returns non-zero when there ARE changes — proceed
  }
  sh(`git commit -m ${JSON.stringify(message)}`, cwd);
  // Push
  sh(`git push origin HEAD:main`, cwd);
}
