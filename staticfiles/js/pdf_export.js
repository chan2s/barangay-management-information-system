// pdf_export.js - PDF Export Functionality for Certificates

function exportToPDF(elementId, filename) {
    const element = document.getElementById(elementId);
    if (!element) {
        console.error('Element not found:', elementId);
        return;
    }

    const opt = {
        margin: [0.5, 0.5, 0.5, 0.5],
        filename: filename || 'certificate.pdf',
        image: { type: 'jpeg', quality: 0.98 },
        html2canvas: {
            scale: 2,
            letterRendering: true,
            useCORS: true,
            logging: false
        },
        jsPDF: {
            unit: 'in',
            format: 'letter',
            orientation: 'portrait'
        }
    };

    // Show loading indicator
    const btn = event?.target;
    const originalText = btn?.innerHTML;
    if (btn) {
        btn.innerHTML = '⏳ Generating PDF...';
        btn.disabled = true;
    }

    // Generate PDF
    html2pdf().set(opt).from(element).save().then(() => {
        if (btn) {
            btn.innerHTML = originalText;
            btn.disabled = false;
        }
    }).catch(error => {
        console.error('PDF generation error:', error);
        if (btn) {
            btn.innerHTML = originalText;
            btn.disabled = false;
            alert('Error generating PDF. Please try again.');
        }
    });
}

// Print with optimized settings
function optimizedPrint() {
    const originalTitle = document.title;
    document.title = 'Certificate - BIMS';
    window.print();
    document.title = originalTitle;
}

// Add keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl + P for print
    if (e.ctrlKey && e.key === 'p') {
        e.preventDefault();
        window.print();
    }
    // Ctrl + Shift + P for PDF
    if (e.ctrlKey && e.shiftKey && e.key === 'P') {
        e.preventDefault();
        const certElement = document.getElementById('certificateContent');
        if (certElement) {
            exportToPDF('certificateContent', 'certificate.pdf');
        }
    }
});