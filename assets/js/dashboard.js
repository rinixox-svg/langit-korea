import { supabase } from './supabase.js';
import { getCurrentUser } from './auth.js';

export async function fetchUserProfile() {
    try {
        const { data: { user } } = await getCurrentUser();
        if (!user) return null;

        const { data, error } = await supabase
            .from('profiles')
            .select('*')
            .eq('id', user.id)
            .single();

        if (error) {
            console.warn('Profile fetch failed, using metadata:', error);
            return {
                nama: user.user_metadata?.nama || user.email?.split('@')[0] || 'Pembelajar',
                level: user.user_metadata?.level || 'pemula'
            };
        }

        return data;
    } catch (e) {
        console.warn('Error fetching profile:', e);
        return null;
    }
}

export async function fetchProgressUnit() {
    try {
        const { data: { user } } = await getCurrentUser();
        if (!user) return [];

        const { data, error } = await supabase
            .from('progress_unit')
            .select('*')
            .eq('user_id', user.id)
            .order('unit_id', { ascending: true });

        if (error) {
            console.warn('Progress fetch failed:', error);
            return [];
        }

        return data || [];
    } catch (e) {
        console.warn('Error fetching progress:', e);
        return [];
    }
}

export function calculateUnitProgress(progressData) {
    const unitList = Array.from({ length: 30 }, (_, i) => 31 + i);
    
    return unitList.map(unitId => {
        const unitProgress = progressData.find(p => p.unit_id === unitId);
        
        if (!unitProgress) {
            return {
                unitId,
                unlocked: unitId === 31,
                completed: false,
                score: 0,
                progressPercent: 0
            };
        }

        const score = unitProgress.score || 0;
        const completed = unitProgress.completed || false;
        const progressPercent = Math.min(score, 100);

        return {
            unitId,
            unlocked: unitProgress.unlocked || false,
            completed,
            score,
            progressPercent,
            lastStudied: unitProgress.last_studied_at
        };
    });
}

export function getNextUnlockableUnit(calculatedProgress) {
    for (let i = 0; i < calculatedProgress.length; i++) {
        const unit = calculatedProgress[i];
        const prevUnit = i > 0 ? calculatedProgress[i - 1] : null;

        if (!unit.unlocked && prevUnit && prevUnit.completed && prevUnit.score >= 70) {
            return unit.unitId;
        }
    }
    return null;
}

export async function unlockNextUnit(currentUnitId) {
    try {
        const { data: { user } } = await getCurrentUser();
        if (!user) return { success: false, error: 'Not authenticated' };

        const nextUnitId = currentUnitId + 1;
        if (nextUnitId > 60) return { success: false, error: 'Already at max unit' };

        const { error } = await supabase
            .from('progress_unit')
            .upsert({
                user_id: user.id,
                unit_id: nextUnitId,
                unlocked: true,
                updated_at: new Date().toISOString()
            }, {
                onConflict: 'user_id,unit_id'
            });

        if (error) throw error;
        return { success: true };
    } catch (e) {
        return { success: false, error: e.message };
    }
}

export function calculateOverallStats(progressData) {
    const totalUnits = 30;
    const completedUnits = progressData.filter(p => p.completed).length;
    const totalQuestions = progressData.reduce((sum, p) => sum + (p.questions_done || 0), 0);
    const totalCorrect = progressData.reduce((sum, p) => sum + (p.correct_answers || 0), 0);
    const accuracy = totalQuestions > 0 ? Math.round((totalCorrect / totalQuestions) * 100) : 0;

    return {
        completedUnits,
        totalUnits,
        completionPercent: Math.round((completedUnits / totalUnits) * 100),
        totalQuestions,
        accuracy,
        streak: 0
    };
}

export function renderUnitGrid(containerId, unitProgress, onUnitClick) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const grid = unitProgress.map(unit => {
        const icon = unit.unlocked 
            ? (unit.completed ? '✅' : '📘') 
            : '🔒';
        const statusClass = unit.completed ? 'completed' : (unit.unlocked ? '' : 'locked');
        const clickHandler = unit.unlocked && onUnitClick 
            ? `onclick="${onUnitClick}(${unit.unitId})"` 
            : '';
        const progressBar = unit.unlocked && !unit.completed && unit.score > 0
            ? `<div class="mini-progress"><div class="mini-progress-fill" style="width:${unit.progressPercent}%"></div></div>`
            : '';

        return `
            <div class="unit-card ${statusClass}" ${clickHandler}>
                <div class="unit-number">${icon} ${unit.unitId}</div>
                <div class="unit-label">Unit ${unit.unitId}</div>
                ${progressBar}
            </div>
        `;
    }).join('');

    container.innerHTML = `<div class="unit-grid">${grid}</div>`;
}

export function renderProgressChart(stats) {
    return `
        <div class="progress-ring-container">
            <svg class="progress-ring" viewBox="0 0 120 120">
                <circle class="progress-ring-bg" cx="60" cy="60" r="50" />
                <circle class="progress-ring-fill" cx="60" cy="60" r="50" 
                    stroke-dasharray="${stats.completionPercent * 3.14} 314" />
            </svg>
            <div class="progress-ring-text">
                <div class="progress-ring-number">${stats.completionPercent}%</div>
                <div class="progress-ring-label">Selesai</div>
            </div>
        </div>
    `;
}

export function renderProgressBar(stats) {
    return `
        <div class="progress-bar">
            <div class="progress-fill" style="width: ${stats.completionPercent}%;"></div>
        </div>
        <p class="progress-text">${stats.completedUnits} / ${stats.totalUnits} unit selesai</p>
    `;
}
