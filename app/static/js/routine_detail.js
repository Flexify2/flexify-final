let remixModal = null;
let remixState = {
    routineWorkoutId: null,
    sets: 3,
    reps: 10,
};

function escapeHtml(text) {
    return String(text || "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#39;");
}

function showToast(title, message, type = "success") {
    const titleEl = document.getElementById("toastTitle");
    const contentEl = document.getElementById("toastContent");
    const toastEl = document.getElementById("appToast");
    if (!titleEl || !contentEl || !toastEl) {
        return;
    }
    titleEl.textContent = title;
    contentEl.textContent = message;
    toastEl.className = `toast text-bg-${type}`;
    new bootstrap.Toast(toastEl).show();
}

async function fetchAlternatives(workoutId) {
    const res = await fetch(`/api/workouts/${workoutId}/alternatives`);
    if (!res.ok) {
        throw new Error("Could not fetch alternatives");
    }
    return res.json();
}

async function swapWorkout(newWorkoutId) {
    const removeRes = await fetch(`/api/routines/${ROUTINE_ID}/workouts/${remixState.routineWorkoutId}`, {
        method: "DELETE",
    });
    if (!removeRes.ok) {
        throw new Error("Could not remove existing workout");
    }

    const addRes = await fetch(`/api/routines/${ROUTINE_ID}/workouts`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            workout_id: newWorkoutId,
            sets: remixState.sets,
            reps: remixState.reps,
        }),
    });
    if (!addRes.ok) {
        throw new Error("Could not add replacement workout");
    }
}

function renderAlternatives(alternatives) {
    const remixList = document.getElementById("remixList");
    if (!remixList) {
        return;
    }

    if (!alternatives.length) {
        remixList.innerHTML = '<p class="text-muted text-center mb-0">No alternatives found right now.</p>';
        return;
    }

    remixList.innerHTML = alternatives
        .map(
            (item) => `
            <div class="border rounded p-2 d-flex align-items-center justify-content-between gap-2">
                <div>
                    <div class="fw-semibold">${escapeHtml(item.name)}</div>
                    <div class="small text-muted">${escapeHtml(item.muscle_group || "")}${item.category ? ` • ${escapeHtml(item.category)}` : ""}</div>
                </div>
                <button type="button" class="btn btn-sm btn-primary remix-swap-btn" data-new-workout-id="${item.id}">
                    Swap
                </button>
            </div>
        `,
        )
        .join("");

    remixList.querySelectorAll(".remix-swap-btn").forEach((btn) => {
        btn.addEventListener("click", async () => {
            const newWorkoutId = parseInt(btn.dataset.newWorkoutId, 10);
            if (!newWorkoutId) {
                return;
            }

            btn.disabled = true;
            btn.textContent = "Swapping...";
            try {
                await swapWorkout(newWorkoutId);
                showToast("Remixed", "Exercise swapped successfully.");
                if (remixModal) {
                    remixModal.hide();
                }
                window.location.reload();
            } catch (_) {
                btn.disabled = false;
                btn.textContent = "Swap";
                showToast("Error", "Could not swap exercise. Please try again.", "danger");
            }
        });
    });
}

async function openRemix(button) {
    const rwId = parseInt(button.dataset.rwId, 10);
    const workoutId = parseInt(button.dataset.workoutId, 10);
    const workoutName = button.dataset.workoutName || "this exercise";
    const sets = parseInt(button.dataset.sets, 10) || 3;
    const reps = parseInt(button.dataset.reps, 10) || 10;

    remixState = {
        routineWorkoutId: rwId,
        sets,
        reps,
    };

    const remixName = document.getElementById("remixWorkoutName");
    const remixList = document.getElementById("remixList");
    if (remixName) {
        remixName.textContent = workoutName;
    }
    if (remixList) {
        remixList.innerHTML = '<div class="text-center py-3"><div class="spinner-border spinner-border-sm text-primary" role="status"></div></div>';
    }

    remixModal.show();

    try {
        const alternatives = await fetchAlternatives(workoutId);
        renderAlternatives(alternatives.filter((item) => item.id !== workoutId));
    } catch (_) {
        if (remixList) {
            remixList.innerHTML = '<p class="text-danger text-center mb-0">Failed to load alternatives.</p>';
        }
    }
}

function main() {
    const modalEl = document.getElementById("remixModal");
    if (!modalEl) {
        return;
    }
    remixModal = new bootstrap.Modal(modalEl);

    document.querySelectorAll(".remix-btn").forEach((btn) => {
        btn.addEventListener("click", () => openRemix(btn));
    });
}

main();
