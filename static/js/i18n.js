const I18N_FILES = {
  pt: {},
  en: '/static/js/i18n-en.json'
};

let currentLang = 'pt';
let translations = {};
let originalTexts = new Map(); // Armazena textos originais em português

function storeOriginalTexts() {
  // Armazena os textos originais de todos os elementos com data-i18n
  document.querySelectorAll('[data-i18n], [data-i18n-template]').forEach((el) => {
    const key = el.getAttribute('data-i18n') || el.getAttribute('data-i18n-template');
    if (key && !originalTexts.has(key)) {
      originalTexts.set(key, el.textContent.trim());
    }
  });
}

function applyTranslations() {
  document.documentElement.lang = currentLang === 'en' ? 'en' : 'pt-BR';
  document.documentElement.setAttribute('data-lang', currentLang);
  
  // Process templates first (they might contain nested i18n)
  document
    .querySelectorAll('[data-i18n-template]')
    .forEach((el) => {
      const key = el.getAttribute('data-i18n-template');
      let text;
      if (currentLang === 'pt') {
        // Restaura texto original em português
        text = originalTexts.get(key);
        if (!text) return;
      } else {
        const template = translations[key];
        if (!template) return;
        text = template;
      }
      
      const args = {};
      Array.from(el.attributes)
        .filter((attr) => attr.name.startsWith('data-i18n-arg-'))
        .forEach((attr) => {
          const argName = attr.name.replace('data-i18n-arg-', '');
          args[argName] = attr.value;
        });
      
      Object.entries(args).forEach(([name, value]) => {
        text = text.replace(new RegExp(`{${name}}`, 'g'), value);
      });
      el.textContent = text;
    });
  
  // Then process regular i18n (but skip elements that are children of already translated elements)
  const processed = new Set();
  document
    .querySelectorAll('[data-i18n]')
    .forEach((el) => {
      // Skip if parent was already processed
      let parent = el.parentElement;
      while (parent) {
        if (processed.has(parent)) {
          return;
        }
        parent = parent.parentElement;
      }
      
      const key = el.getAttribute('data-i18n');
      let value;
      if (currentLang === 'pt') {
        // Restaura texto original em português
        value = originalTexts.get(key);
      } else {
        value = translations[key];
      }
      
      if (value) {
        el.textContent = value;
        processed.add(el);
      }
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
  // Primeiro, armazena os textos originais em português
  storeOriginalTexts();
  
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
