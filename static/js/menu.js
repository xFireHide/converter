;(function(){
  const btn = document.getElementById('menu-toggle');
  const sidebar = document.getElementById('sidebar');
  if(!btn || !sidebar) return;

  // estado: visível quando tem classe 'open'
  function open(){ sidebar.classList.add('open'); }
  function close(){ sidebar.classList.remove('open'); }
  function toggle(){ sidebar.classList.toggle('open'); }

  btn.addEventListener('click', toggle);

  // fecha ao clicar fora (mobile)
  document.addEventListener('click', function(ev){
    const within = sidebar.contains(ev.target) || btn.contains(ev.target);
    if(!within){ close(); }
  });
})();







console.log('menu.js loaded');


