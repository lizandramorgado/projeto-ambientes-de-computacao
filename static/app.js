// Basic JS to call the controller endpoint and render result.
const $ = (id) => document.getElementById(id);

const endpoint = (pdb) => `/pdb/${encodeURIComponent(pdb)}`;

async function fetchPdb(pdb) {
  const errEl = $('error');
  errEl.textContent = '';
  $('result').hidden = true;

  try {
    const res = await fetch(endpoint(pdb));
    if (!res.ok) {
      const err = await res.json().catch(()=>({error:res.statusText}));
      throw new Error(err.error || JSON.stringify(err));
    }
    return await res.json();
  } catch (e) {
    throw e;
  }
}

function render(data) {
  $('result').hidden = false;
  $('title').textContent = data.title || data.pdbid || '';
  $('classification').textContent = data.classification || '';
  $('organism').textContent = data.organism || '';
  $('method').textContent = data.method || '';
  $('resolution').textContent = data.resolution || '';
  $('publication_title').textContent = data.publication_title || '';
  const doiEl = $('doi');
  if (data.doi) {
    doiEl.textContent = data.doi;
    const doiUrl = data.doi.startsWith('http') ? data.doi : `https://doi.org/${data.doi}`;
    doiEl.href = doiUrl;
  } else {
    doiEl.textContent = '';
    doiEl.href = '#';
  }
  $('authors').textContent = Array.isArray(data.authors) ? data.authors.join(', ') : (data.authors || '');
  if (Array.isArray(data.related_structures)) {
    $('related').innerHTML = data.related_structures.map(s =>
      `<a href="https://www.rcsb.org/structure/${encodeURIComponent(s)}" target="_blank">${s}</a>`
    ).join(', ');
  } else {
    $('related').textContent = data.related_structures || '';
  }
  $('abstract').textContent = data.abstract || '';
  // Raw JSON element removed from the HTML; don't write raw output here.

  // Use known CDN image URL for display (the controller's local_image path is a filesystem path)
  const pdbid = data.pdbid || '';
  const img = $('structureImage');
  img.src = pdbid ? `https://cdn.rcsb.org/images/structures/${pdbid}_assembly-1.jpeg` : '';
  img.alt = `Structure image for ${pdbid}`;
}

document.getElementById('fetch').addEventListener('click', async () => {
  const pdb = $('pdbid').value.trim();
  if (!pdb) {
    $('error').textContent = 'Please enter a PDB id.';
    return;
  }
  try {
    const data = await fetchPdb(pdb);
    render(data);
  } catch (e) {
    $('error').textContent = 'Error: ' + e.message;
    console.error(e);
  }
});

// allow Enter to trigger fetch
$('pdbid').addEventListener('keydown', (ev) => {
  if (ev.key === 'Enter') document.getElementById('fetch').click();
});