const I18N_FILES = {
  pt: {},
  en: '/static/js/i18n-en.json'
};

let currentLang = 'pt';
let translations = {};

function applyTranslations() {
  document.documentElement.lang = currentLang;
  document
    .querySelectorAll('[data-i18n]')
    .forEach((el) => {
      const key = el.getAttribute('data-i18n');
      const value = translations[key];
      if (value) el.textContent = value;
    });

  document
    .querySelectorAll('[data-i18n-template]')
    .forEach((el) => {
      const key = el.getAttribute('data-i18n-template');
      const template = translations[key];
      if (!template) return;
      const args = {};
      Array.from(el.attributes)
        .filter((attr) => attr.name.startsWith('data-i18n-arg-'))
        .forEach((attr) => {
          const argName = attr.name.replace('data-i18n-arg-', '');
          args[argName] = attr.value;
        });
      let text = template;
      Object.entries(args).forEach(([name, value]) => {
        text = text.replace(new RegExp(`{${name}}`, 'g'), value);
      });
      el.textContent = text;
    });
}

async function setLanguage(lang) {
  if (lang === 'pt') {
    translations = {};
    currentLang = 'pt';
    applyTranslations();
    localStorage.removeItem('firetools-lang');
    return;
  }
  if (lang === currentLang) return;
  const file = I18N_FILES[lang];
  if (!file) return;
  try {
    const response = await fetch(file, { cache: 'no-store' });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    translations = await response.json();
    currentLang = lang;
    localStorage.setItem('firetools-lang', lang);
    applyTranslations();
  } catch (err) {
    console.error('Failed to load translations', err);
  }
}

function initI18n() {
  const saved = localStorage.getItem('firetools-lang');
  const initial = saved || 'pt';
  if (initial !== 'pt') {
    setLanguage(initial);
  } else {
    applyTranslations();
  }
  const toggle = document.getElementById('language-toggle');
  if (toggle) {
    const updateToggleLabel = () => {
      toggle.textContent = currentLang === 'pt' ? 'EN' : 'PT';
    };
    updateToggleLabel();
    toggle.addEventListener('click', () => {
      const next = currentLang === 'pt' ? 'en' : 'pt';
      setLanguage(next).then(updateToggleLabel);
    });
  }
}

document.addEventListener('DOMContentLoaded', initI18n);
