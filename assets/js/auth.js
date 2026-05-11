// ==========================================
// LANGIT KOREA — Authentication Module
// ==========================================

import { supabase } from './supabase.js';

// ========== REGISTER ==========
export async function register(email, password, nama) {
  try {
    const { data, error } = await supabase.auth.signUp({
      email: email,
      password: password,
      options: {
        data: {
          nama: nama
        }
      }
    });

    if (error) throw error;
    return { success: true, user: data.user, message: 'Silakan cek email untuk verifikasi.' };
  } catch (error) {
    return { success: false, error: error.message };
  }
}

// ========== LOGIN ==========
export async function login(email, password) {
  try {
    const { data, error } = await supabase.auth.signInWithPassword({
      email: email,
      password: password
    });

    if (error) throw error;
    return { success: true, user: data.user, session: data.session };
  } catch (error) {
    return { success: false, error: error.message };
  }
}

// ========== LOGOUT ==========
export async function logout() {
  try {
    const { error } = await supabase.auth.signOut();
    if (error) throw error;
    return { success: true };
  } catch (error) {
    return { success: false, error: error.message };
  }
}

// ========== GET CURRENT USER ==========
export function getCurrentUser() {
  return supabase.auth.getUser();
}

// ========== ON AUTH STATE CHANGE ==========
export function onAuthChange(callback) {
  const { data: { subscription } } = supabase.auth.onAuthStateChange((event, session) => {
    callback(event, session);
  });
  return subscription;
}
