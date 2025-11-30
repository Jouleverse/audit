async function loadMonthList() {
  try {
    const res = await fetch('months.json');
    if (!res.ok) return [];
    return await res.json();
  } catch { return []; }
}

async function loadReport(month) {
  const name = month ? `report_${month}.json` : 'report.json';
  try {
    const res = await fetch(name);
    if (!res.ok) throw new Error();
    return await res.json();
  } catch {
    const res = await fetch('report.json');
    return await res.json();
  }
}

async function load(initialMonth) {
  const months = await loadMonthList();
  const monthSel = document.getElementById('month');
  const now = new Date();
  const curMonth = Number(`${now.getFullYear()}${String(now.getMonth()+1).padStart(2,'0')}`);
  const defaultMonth = months.includes(curMonth) ? curMonth : (months[months.length-1]||null);
  const targetMonth = initialMonth || defaultMonth;
  monthSel.innerHTML = '';
  for (const m of months) {
    const opt = document.createElement('option');
    opt.value = m;
    opt.textContent = m;
    if (m === targetMonth) opt.selected = true;
    monthSel.appendChild(opt);
  }
  const data = await loadReport(targetMonth);
  const tbody = document.querySelector('#main tbody');
  const meta = document.getElementById('meta');
  meta.textContent = `Month ${data.month} · ${new Date(data.generatedAt).toLocaleString()}`;
  let rows = data.cores.slice();
  const search = document.getElementById('search');
  const sortBtn = document.getElementById('sortTotal');
  monthSel.onchange = async () => {
    const d = await loadReport(Number(monthSel.value));
    rows = d.cores.slice();
    meta.textContent = `Month ${d.month} · ${new Date(d.generatedAt).toLocaleString()}`;
    render(rows);
  };
  function render(list) {
    tbody.innerHTML = '';
    for (const c of list) {
      const tr = document.createElement('tr');
      tr.innerHTML = `<td>${c.coreId}</td><td>${c.totalPoints}</td><td>${c.minerTotal}</td><td>${c.witnessTotal}</td><td>${c.days}</td><td><button data-core="${c.coreId}">Detail</button></td>`;
      tbody.appendChild(tr);
      const btn = tr.querySelector('button');
      btn.addEventListener('click', () => toggleDetail(tr, c));
    }
  }
  function toggleDetail(tr, c) {
    const next = tr.nextElementSibling;
    if (next && next.classList.contains('detail')) {
      next.remove();
      return;
    }
    const dtr = document.createElement('tr');
    dtr.className = 'detail';
    const td = document.createElement('td');
    td.colSpan = 6;
    const table = document.createElement('table');
    table.className = 'sub';
    const thead = document.createElement('thead');
    thead.innerHTML = '<tr><th>date</th><th>minerLive</th><th>witnessLive</th><th>minerPoints</th><th>witnessPoints</th><th>total</th></tr>';
    table.appendChild(thead);
    const tb = document.createElement('tbody');
    for (const d of c.details) {
      const r = document.createElement('tr');
      r.innerHTML = `<td>${d.date}</td><td>${d.minerLiveness ? '✔' : '✘'}</td><td>${d.witnessLiveness ? '✔' : '✘'}</td><td>${d.minerPoints}</td><td>${d.witnessPoints}</td><td>${d.totalPoints}</td>`;
      tb.appendChild(r);
    }
    table.appendChild(tb);
    td.appendChild(table);
    dtr.appendChild(td);
    tr.after(dtr);
  }
  search.addEventListener('input', () => {
    const q = search.value.trim();
    if (!q) render(rows);
    else render(rows.filter(c => String(c.coreId).includes(q)));
  });
  sortBtn.addEventListener('click', () => {
    rows.sort((a,b) => b.totalPoints - a.totalPoints);
    render(rows);
  });
  render(rows);
}
load();
