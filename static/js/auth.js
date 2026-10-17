/**
 * auth.js
 * Handles Google Sign-In with Firebase, session synchronization with Flask backend,
 * and user state management across MEDexplain AI.
 */

document.addEventListener('DOMContentLoaded', () => {
  const googleLoginBtn = document.getElementById('google-login-btn');
  const googleLoginNavBtn = document.getElementById('google-login-nav-btn');
  const logoutBtn = document.getElementById('logout-btn');

  // Attach Google Sign-In handlers
  if (googleLoginBtn) {
    googleLoginBtn.addEventListener('click', handleGoogleSignIn);
  }
  if (googleLoginNavBtn) {
    googleLoginNavBtn.addEventListener('click', handleGoogleSignIn);
  }
  if (logoutBtn) {
    logoutBtn.addEventListener('click', handleSignOut);
  }

  // Observe Firebase Auth State if available
  if (typeof auth !== 'undefined' && auth) {
    auth.onAuthStateChanged((user) => {
      if (user) {
        updateNavbarUser(user);
      }
    });
  }
});

/**
 * Executes Google Sign-in with Firebase popup and syncs session with Flask backend.
 */
async function handleGoogleSignIn(e) {
  if (e) e.preventDefault();
  
  const loginBtn = document.getElementById('google-login-btn') || document.getElementById('google-login-nav-btn');
  if (loginBtn) {
    loginBtn.disabled = true;
    loginBtn.innerHTML = `
      <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
      Connecting to Google...
    `;
  }

  try {
    if (typeof auth === 'undefined' || !auth) {
      throw new Error("Firebase Auth is not initialized. Check your network or configuration.");
    }

    const result = await auth.signInWithPopup(googleProvider);
    const user = result.user;
    const idToken = await user.getIdToken();

    // Synchronize session with backend Flask API
    const response = await fetch('/auth/session', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        uid: user.uid,
        displayName: user.displayName,
        email: user.email,
        photoURL: user.photoURL,
        idToken: idToken
      })
    });

    const data = await response.json();
    if (data.success) {
      window.location.href = data.redirect || '/dashboard';
    } else {
      showToast(data.error || 'Authentication synchronization failed.', 'danger');
      resetLoginBtn(loginBtn);
    }
  } catch (error) {
    console.error("Google Sign-In Error:", error);
    let errorMsg = "Failed to sign in with Google. ";
    if (error.code === 'auth/popup-closed-by-user') {
      errorMsg += "The sign-in window was closed before finishing.";
    } else if (error.code === 'auth/network-request-failed') {
      errorMsg += "A network error occurred. Please check your internet connection.";
    } else {
      errorMsg += error.message || "";
    }
    showToast(errorMsg, 'warning');
    resetLoginBtn(loginBtn);
  }
}

/**
 * Signs out from Firebase and clears Flask session.
 */
async function handleSignOut(e) {
  if (e) e.preventDefault();

  try {
    if (typeof auth !== 'undefined' && auth) {
      await auth.signOut();
    }
    const response = await fetch('/auth/logout', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });
    const data = await response.json();
    window.location.href = data.redirect || '/';
  } catch (error) {
    console.error("Logout Error:", error);
    window.location.href = '/';
  }
}

function resetLoginBtn(btn) {
  if (!btn) return;
  btn.disabled = false;
  btn.innerHTML = `
    <svg width="20" height="20" viewBox="0 0 24 24" class="google-icon">
      <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
      <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
      <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"/>
      <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"/>
    </svg>
    Continue with Google
  `;
}

function updateNavbarUser(user) {
  const profileAvatar = document.getElementById('nav-user-avatar');
  const profileName = document.getElementById('nav-user-name');
  if (profileAvatar && user.photoURL) {
    profileAvatar.src = user.photoURL;
  }
  if (profileName && user.displayName) {
    profileName.textContent = user.displayName.split(' ')[0];
  }
}

/**
 * Toast notification helper
 */
function showToast(message, type = 'info') {
  let toastContainer = document.getElementById('toast-container');
  if (!toastContainer) {
    toastContainer = document.createElement('div');
    toastContainer.id = 'toast-container';
    toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
    document.body.appendChild(toastContainer);
  }

  const toastId = 'toast-' + Date.now();
  const alertBg = type === 'danger' ? 'bg-danger text-white' : (type === 'warning' ? 'bg-warning text-dark' : 'bg-primary text-white');

  const toastHtml = `
    <div id="${toastId}" class="toast align-items-center ${alertBg} border-0 show shadow-lg" role="alert" aria-live="assertive" aria-atomic="true">
      <div class="d-flex">
        <div class="toast-body">
          ${message}
        </div>
        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close" onclick="this.closest('.toast').remove()"></button>
      </div>
    </div>
  `;
  toastContainer.insertAdjacentHTML('beforeend', toastHtml);

  setTimeout(() => {
    const el = document.getElementById(toastId);
    if (el) el.remove();
  }, 6000);
}
