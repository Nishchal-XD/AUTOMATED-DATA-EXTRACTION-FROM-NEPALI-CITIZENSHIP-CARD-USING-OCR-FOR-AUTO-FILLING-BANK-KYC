// ========== IMAGE PREVIEW WITH DRAG & DROP ==========

function previewImage(input, previewId) {
    const preview = document.getElementById(previewId);
    const file = input.files[0];

    if (file) {
        // Validate file size (max 10MB)
        if (file.size > 10 * 1024 * 1024) {
            alert("❌ File must be less than 10MB");
            input.value = "";
            return;
        }

        const reader = new FileReader();
        reader.onload = () => {
            preview.src = reader.result;
            preview.style.display = 'block';
            
            // Hide the drop zone content
            const dropZone = input.closest('.drop-zone');
            if (dropZone) {
                const icon = dropZone.querySelector('.drop-zone-icon');
                const h3 = dropZone.querySelector('h3');
                const p = dropZone.querySelectorAll('p');
                const browseBtn = dropZone.querySelector('.browse-btn');
                
                if (icon) icon.style.display = 'none';
                if (h3) h3.style.display = 'none';
                p.forEach(el => el.style.display = 'none');
                if (browseBtn) browseBtn.style.display = 'none';
            }
        };
        reader.readAsDataURL(file);
    }
}

// ========== DRAG & DROP UPLOAD ==========

document.querySelectorAll(".drop-zone").forEach(zone => {
    const input = zone.querySelector("input[type='file']");
    const previewId = zone.dataset.preview;

    zone.addEventListener("dragover", e => {
        e.preventDefault();
        zone.classList.add("drag-over");
    });

    zone.addEventListener("dragleave", () => {
        zone.classList.remove("drag-over");
    });

    zone.addEventListener("drop", e => {
        e.preventDefault();
        zone.classList.remove("drag-over");

        const files = e.dataTransfer.files;
        if (files.length > 0) {
            input.files = files;
            
            // Validate file size
            if (files[0].size > 10 * 1024 * 1024) {
                alert("❌ File must be less than 10MB");
                input.value = "";
                return;
            }

            if (previewId) {
                const preview = document.getElementById(previewId);
                const reader = new FileReader();
                reader.onload = () => {
                    preview.src = reader.result;
                    preview.style.display = 'block';
                    
                    // Hide drop zone content
                    const icon = zone.querySelector('.drop-zone-icon');
                    const h3 = zone.querySelector('h3');
                    const p = zone.querySelectorAll('p');
                    const browseBtn = zone.querySelector('.browse-btn');
                    
                    if (icon) icon.style.display = 'none';
                    if (h3) h3.style.display = 'none';
                    p.forEach(el => el.style.display = 'none');
                    if (browseBtn) browseBtn.style.display = 'none';
                };
                reader.readAsDataURL(files[0]);
            }
        }
    });
});

// ========== REMOVE FILE FUNCTION ==========

window.removeFile = function(inputId, previewId, zoneSelector) {
    const input = document.getElementById(inputId);
    const preview = document.getElementById(previewId);
    const dropZone = document.querySelector(zoneSelector);
    
    if (input) input.value = '';
    if (preview) {
        preview.src = '';
        preview.style.display = 'none';
    }
    
    // Show drop zone content again
    if (dropZone) {
        const icon = dropZone.querySelector('.drop-zone-icon');
        const h3 = dropZone.querySelector('h3');
        const p = dropZone.querySelectorAll('p');
        const browseBtn = dropZone.querySelector('.browse-btn');
        
        if (icon) icon.style.display = 'block';
        if (h3) h3.style.display = 'block';
        p.forEach(el => el.style.display = 'block');
        if (browseBtn) browseBtn.style.display = 'inline-block';
    }
};

// ========== ACCOUNT NUMBER AUTO MOVE ==========

document.querySelectorAll(".acc-input").forEach((input, i, arr) => {
    input.addEventListener("input", () => {
        if (input.value.length === input.maxLength && arr[i + 1]) {
            arr[i + 1].focus();
        }
        updateFullAccount();
    });

    input.addEventListener("keydown", e => {
        if (e.key === "Backspace" && !input.value && arr[i - 1]) {
            arr[i - 1].focus();
        }
    });
});

function updateFullAccount() {
    const accInputs = document.querySelectorAll('.acc-input');
    const fullAccount = Array.from(accInputs).map(i => i.value || '').join('');
    const hiddenField = document.getElementById('fullAccount');
    if (hiddenField) hiddenField.value = fullAccount;
}

// ========== DATE INPUTS AUTO MOVE ==========

document.querySelectorAll(".date-box").forEach((input, i, arr) => {
    input.addEventListener("input", () => {
        if (input.value.length === input.maxLength && arr[i + 1]) {
            arr[i + 1].focus();
        }
    });
});

// ========== FORM VALIDATION ==========

document.getElementById("kycForm")?.addEventListener("submit", e => {
    const required = document.querySelectorAll("[required]");
    let valid = true;

    required.forEach(field => {
        if (!field.value) {
            field.style.border = "2px solid var(--nic-red)";
            valid = false;
        } else {
            field.style.border = "2px solid #e0e0e0";
        }
    });

    if (!valid) {
        e.preventDefault();
        alert("⚠ Please fill all required fields!");
    }
});

// ========== MOBILE NUMBER CHECK ==========

document.getElementById("mobile")?.addEventListener("input", e => {
    e.target.value = e.target.value.replace(/\D/g, '').slice(0, 10);
});

// ========== FILE SIZE VALIDATION ==========

document.querySelectorAll("input[type='file']").forEach(input => {
    input.addEventListener("change", function() {
        if (this.files[0] && this.files[0].size > 10 * 1024 * 1024) {
            alert("❌ File must be less than 10MB");
            this.value = "";
            
            // Reset preview if exists
            const previewId = this.closest('.drop-zone')?.dataset.preview;
            if (previewId) {
                const preview = document.getElementById(previewId);
                if (preview) {
                    preview.src = '';
                    preview.style.display = 'none';
                }
            }
        }
    });
});

// ========== DATE AUTO TODAY ==========

document.getElementById("date")?.valueAsDate = new Date();

// ========== SAME AS PERMANENT ADDRESS TOGGLE ==========

window.toggleAddress = function() {
    const checkbox = document.getElementById('sameAsPermanent');
    const currentAddress = document.getElementById('currentAddress');
    
    if (checkbox && currentAddress) {
        if (checkbox.checked) {
            currentAddress.style.display = 'none';
        } else {
            currentAddress.style.display = 'grid';
        }
    }
};

// ========== INITIALIZE ON PAGE LOAD ==========

document.addEventListener('DOMContentLoaded', function() {
    // Set default nationality if not set
    const nationalityInput = document.getElementById("nationality");
    if (nationalityInput && !nationalityInput.value) {
        nationalityInput.value = "Nepali";
    }
    
    // Initialize any other components
    updateFullAccount();
});