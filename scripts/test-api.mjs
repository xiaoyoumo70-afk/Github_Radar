const base = process.env.GITHUB_RADAR_URL || 'http://localhost:4420';
async function must(path) {
  const r = await fetch(base + path);
  if (!r.ok) throw new Error(`${path}: HTTP ${r.status}`);
  return r.json();
}
const projects = await must('/api/projects');
console.log(`projects=${projects.length}`);
const settings = await must('/api/settings');
console.log(`model=${settings.file.llm_model}`);
if (projects[0]) {
  const detail = await must(`/api/projects/${projects[0].safe_name}`);
  console.log(`detail=${detail.full_name}; markdown=${(detail.markdown || '').length}`);
}
console.log('api-ok');
