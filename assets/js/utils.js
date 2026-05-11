// ==========================================
// LANGIT KOREA — Utility Functions
// ==========================================

// ========== NAVIGATION ==========
export function navigateTo(page) {
  document.body.style.opacity = '0';
  document.body.style.transition = 'opacity 0.25s ease';
  setTimeout(() => {
    window.location.href = page;
  }, 250);
}

// ========== SHOW TOAST NOTIFICATION ==========
export function showToast(message, type = 'info') {
  const container = document.getElementById('toastContainer') || createToastContainer();
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.textContent = message;
  container.appendChild(toast);

  setTimeout(() => {
    toast.remove();
  }, 3000);
}

function createToastContainer() {
  const container = document.createElement('div');
  container.id = 'toastContainer';
  container.className = 'toast-container';
  document.body.appendChild(container);
  return container;
}

// ========== SHOW LOADING ==========
export function showLoading(elementId, text = 'Memuat...') {
  const el = document.getElementById(elementId);
  if (el) {
    el.innerHTML = `
      <div class="loading">
        <div class="spinner"></div>
        <p id="loadingText">${text}</p>
      </div>
    `;
  }
}

// ========== HIDE LOADING ==========
export function hideLoading(elementId, html = '') {
  const el = document.getElementById(elementId);
  if (el) {
    el.innerHTML = html;
  }
}

// ========== FORMAT NUMBER ==========
export function formatNumber(num) {
  return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, '.');
}

// ========== GET URL PARAMETER ==========
export function getUrlParam(param) {
  const urlParams = new URLSearchParams(window.location.search);
  return urlParams.get(param);
}

// ========== CHECK AUTH & REDIRECT ==========
export async function checkAuth(redirectTo = 'onboarding.html') {
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) {
    navigateTo(redirectTo);
    return null;
  }
  return user;
}

// ========== STORE PROGRESS ==========
export function saveProgress(key, value) {
  try {
    localStorage.setItem(`langitkorea_${key}`, JSON.stringify(value));
  } catch (e) {
    console.warn('Gagal menyimpan progress:', e);
  }
}

export function loadProgress(key) {
  try {
    const data = localStorage.getItem(`langitkorea_${key}`);
    return data ? JSON.parse(data) : null;
  } catch (e) {
    console.warn('Gagal memuat progress:', e);
    return null;
  }
}

// ========== DEBOUNCE ==========
export function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

// ========== RENDER STAR RATING ==========
export function renderStars(rating, maxStars = 5) {
  let stars = '';
  for (let i = 1; i <= maxStars; i++) {
    stars += i <= rating ? '⭐' : '☆';
  }
  return stars;
}

// ========== SHUFFLE ARRAY ==========
export function shuffleArray(array) {
  const shuffled = [...array];
  for (let i = shuffled.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
  }
  return shuffled;
}
