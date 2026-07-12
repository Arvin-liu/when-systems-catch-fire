async function loadAtlas() {
  const res = await fetch('../../data/publication-atlas-20260712.json');
  return res.json();
}

function renderTag(text) {
  const span = document.createElement('span');
  span.className = 'tag';
  span.textContent = text;
  return span;
}

function matches(item, query, form) {
  const haystack = [item.id, item.title, item.boundary, item.evidence.join(' '), item.forms.join(' ')].join(' ').toLowerCase();
  const q = query.trim().toLowerCase();
  const okQuery = !q || haystack.includes(q);
  const okForm = !form || item.forms.includes(form);
  return okQuery && okForm;
}

loadAtlas().then((atlas) => {
  const atlasEl = document.getElementById('atlas');
  const searchEl = document.getElementById('search');
  const formEl = document.getElementById('formFilter');
  const countEl = document.getElementById('directionCount');
  const forms = [...new Set(atlas.directions.flatMap((d) => d.forms))].sort();
  forms.forEach((form) => {
    const opt = document.createElement('option');
    opt.value = form;
    opt.textContent = form;
    formEl.appendChild(opt);
  });
  countEl.textContent = String(atlas.directions.length);

  const draw = () => {
    atlasEl.innerHTML = '';
    const query = searchEl.value;
    const form = formEl.value;
    atlas.directions.filter((item) => matches(item, query, form)).forEach((item) => {
      const card = document.createElement('article');
      card.className = 'card';
      card.innerHTML = `<div class="meta">${item.id}</div><h2>${item.title}</h2>`;
      const tagRow = document.createElement('div');
      tagRow.className = 'tagrow';
      item.forms.forEach((f) => tagRow.appendChild(renderTag(f)));
      card.appendChild(tagRow);
      const boundary = document.createElement('p');
      boundary.className = 'boundary';
      boundary.textContent = item.boundary;
      card.appendChild(boundary);
      const evidence = document.createElement('div');
      evidence.className = 'evidence';
      item.evidence.forEach((ref) => {
        const a = document.createElement('a');
        a.href = `../../${ref}`;
        a.textContent = ref;
        evidence.appendChild(a);
      });
      card.appendChild(evidence);
      atlasEl.appendChild(card);
    });
  };
  searchEl.addEventListener('input', draw);
  formEl.addEventListener('change', draw);
  draw();
}).catch((error) => {
  document.body.insertAdjacentHTML('beforeend', `<pre>${String(error)}</pre>`);
});
