const assignmentList = document.querySelector('#assignments');
const statusText = {
  'overdue': 'Overdue',
  'due-soon': 'Due soon',
  'upcoming': 'Upcoming',
  'completed': 'Done',
};

async function refresh() {
  const [assignmentsResponse, summaryResponse] = await Promise.all([
    fetch('/api/assignments'), fetch('/api/summary'),
  ]);
  const assignments = await assignmentsResponse.json();
  const summary = await summaryResponse.json();
  document.querySelector('#total').textContent = summary.total;
  document.querySelector('#soon').textContent = summary.due_soon;
  document.querySelector('#overdue').textContent = summary.overdue;
  document.querySelector('#done').textContent = summary.completed;
  document.querySelector('#assignment-count').textContent = `${assignments.length} tracked`;
  assignmentList.replaceChildren();
  if (!assignments.length) {
    const message = document.createElement('p');
    message.className = 'empty';
    message.textContent = 'Your list is empty. Add your first assignment!';
    assignmentList.append(message);
    return;
  }
  for (const item of assignments) {
    const row = document.createElement('article');
    row.className = `assignment ${item.completed_at ? 'done' : ''}`;
    const box = document.createElement('input');
    box.type = 'checkbox';
    box.checked = !!item.completed_at;
    box.setAttribute('aria-label', `Mark ${item.title} complete`);
    box.addEventListener('change', async () => {
      const result = await fetch(`/api/assignments/${item.id}`, {
        method: 'PATCH', headers: {'Content-Type':'application/json'},
        body: JSON.stringify({completed: box.checked}),
      });
      if (!result.ok) alert('Could not update assignment.');
      await refresh();
    });
    const info = document.createElement('div');
    info.className = 'assignment-info';
    const title = document.createElement('strong'); title.textContent = item.title;
    const meta = document.createElement('small');
    meta.textContent = `${item.course} · Due ${item.due_date}`;
    info.append(title, meta);
    const status = document.createElement('span');
    status.className = `status ${item.urgency}`;
    status.textContent = statusText[item.urgency];
    row.append(box, info, status);
    assignmentList.append(row);
  }
}

document.querySelector('#new-assignment').addEventListener('submit', async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const values = Object.fromEntries(new FormData(form).entries());
  const response = await fetch('/api/assignments', {
    method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(values),
  });
  const data = await response.json();
  const message = document.querySelector('#form-message');
  if (!response.ok) { message.textContent = data.error || 'Could not add assignment.'; return; }
  form.reset(); message.textContent = '';
  await refresh();
});
refresh().catch(() => { assignmentList.textContent = 'Could not load assignments.'; });
