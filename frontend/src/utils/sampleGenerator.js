// Client-side high-fidelity sample image generator for instant Viva/Defense testing.
// Generates realistic canvas images for any category with and without defects.

export const generateSampleImageFile = async (category = 'bottle', kind = 'defect') => {
    const canvas = document.createElement('canvas');
    canvas.width = 512;
    canvas.height = 512;
    const ctx = canvas.getContext('2d');

    // Background gradient (industrial inspection booth)
    const bgGradient = ctx.createLinearGradient(0, 0, 512, 512);
    bgGradient.addColorStop(0, '#1a1e29');
    bgGradient.addColorStop(1, '#0c0f17');
    ctx.fillStyle = bgGradient;
    ctx.fillRect(0, 0, 512, 512);

    // Subtle grid lines (conveyor belt texture)
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.04)';
    ctx.lineWidth = 1;
    for (let i = 0; i < 512; i += 32) {
        ctx.beginPath();
        ctx.moveTo(i, 0);
        ctx.lineTo(i, 512);
        ctx.stroke();
        ctx.beginPath();
        ctx.moveTo(0, i);
        ctx.lineTo(512, i);
        ctx.stroke();
    }

    // Centered object rendering based on category
    ctx.save();
    ctx.translate(256, 256);

    if (category === 'bottle') {
        // Glass bottle body
        ctx.fillStyle = '#2a4365';
        ctx.strokeStyle = '#63b3ed';
        ctx.lineWidth = 3;
        
        // Bottle silhouette
        ctx.beginPath();
        ctx.moveTo(-40, 180);
        ctx.lineTo(40, 180);
        ctx.lineTo(45, -40);
        ctx.quadraticCurveTo(45, -100, 20, -130);
        ctx.lineTo(20, -180);
        ctx.lineTo(-20, -180);
        ctx.lineTo(-20, -130);
        ctx.quadraticCurveTo(-45, -100, -45, -40);
        ctx.closePath();
        ctx.fill();
        ctx.stroke();

        // Liquid level
        ctx.fillStyle = '#3182ce';
        ctx.beginPath();
        ctx.moveTo(-42, 175);
        ctx.lineTo(42, 175);
        ctx.lineTo(43, 20);
        ctx.lineTo(-43, 20);
        ctx.closePath();
        ctx.fill();

        // Bottle cap
        ctx.fillStyle = '#ecc94b';
        ctx.fillRect(-22, -195, 44, 18);

        if (kind === 'defect') {
            // Crack & contamination on bottle body
            ctx.strokeStyle = '#feb2b2';
            ctx.lineWidth = 3;
            ctx.beginPath();
            ctx.moveTo(5, -20);
            ctx.lineTo(25, 20);
            ctx.lineTo(15, 60);
            ctx.lineTo(32, 95);
            ctx.stroke();

            // Dark foreign particle/stain
            ctx.fillStyle = '#1a202c';
            ctx.beginPath();
            ctx.ellipse(-15, 80, 12, 18, Math.PI / 4, 0, Math.PI * 2);
            ctx.fill();
        }
    } else if (category === 'capsule') {
        // Pill capsule
        ctx.rotate(Math.PI / 6);
        ctx.lineWidth = 4;
        
        // Left half (Red)
        ctx.fillStyle = '#e53e3e';
        ctx.beginPath();
        ctx.arc(-50, 0, 45, Math.PI / 2, Math.PI * 1.5);
        ctx.lineTo(0, -45);
        ctx.lineTo(0, 45);
        ctx.closePath();
        ctx.fill();
        ctx.strokeStyle = '#fc8181';
        ctx.stroke();

        // Right half (Yellow)
        ctx.fillStyle = '#ecc94b';
        ctx.beginPath();
        ctx.arc(50, 0, 45, -Math.PI / 2, Math.PI / 2);
        ctx.lineTo(0, 45);
        ctx.lineTo(0, -45);
        ctx.closePath();
        ctx.fill();
        ctx.strokeStyle = '#f6e05e';
        ctx.stroke();

        if (kind === 'defect') {
            // Split shell dent & crack
            ctx.strokeStyle = '#742a2a';
            ctx.lineWidth = 4;
            ctx.beginPath();
            ctx.moveTo(-15, -45);
            ctx.lineTo(10, -20);
            ctx.lineTo(-5, 10);
            ctx.lineTo(12, 45);
            ctx.stroke();

            // Puncture dent
            ctx.fillStyle = '#2d3748';
            ctx.beginPath();
            ctx.arc(-30, 15, 8, 0, Math.PI * 2);
            ctx.fill();
        }
    } else if (category === 'metal_nut') {
        // Hexagonal metal nut
        ctx.fillStyle = '#718096';
        ctx.strokeStyle = '#cbd5e0';
        ctx.lineWidth = 4;
        
        ctx.beginPath();
        for (let i = 0; i < 6; i++) {
            const angle = (i * Math.PI) / 3;
            const x = 110 * Math.cos(angle);
            const y = 110 * Math.sin(angle);
            if (i === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        }
        ctx.closePath();
        ctx.fill();
        ctx.stroke();

        // Center threaded hole
        ctx.fillStyle = '#1a202c';
        ctx.beginPath();
        ctx.arc(0, 0, 50, 0, Math.PI * 2);
        ctx.fill();
        ctx.strokeStyle = '#a0aec0';
        ctx.lineWidth = 2;
        ctx.stroke();

        if (kind === 'defect') {
            // Deep gouge / surface scratch
            ctx.strokeStyle = '#fed7d7';
            ctx.lineWidth = 5;
            ctx.beginPath();
            ctx.moveTo(-80, -40);
            ctx.lineTo(-20, 20);
            ctx.lineTo(-40, 70);
            ctx.stroke();

            // Broken tooth thread
            ctx.fillStyle = '#e53e3e';
            ctx.fillRect(40, -10, 20, 15);
        }
    } else if (category === 'cable') {
        // Industrial insulated cable
        ctx.strokeStyle = '#3182ce';
        ctx.lineWidth = 44;
        ctx.lineCap = 'round';
        ctx.beginPath();
        ctx.moveTo(-160, -120);
        ctx.bezierCurveTo(-50, -160, 50, 160, 160, 120);
        ctx.stroke();

        if (kind === 'defect') {
            // Stripped insulation with exposed copper wire
            ctx.strokeStyle = '#dd6b20';
            ctx.lineWidth = 36;
            ctx.beginPath();
            ctx.moveTo(-20, -20);
            ctx.lineTo(20, 20);
            ctx.stroke();

            // Cut/Burn marks
            ctx.strokeStyle = '#e53e3e';
            ctx.lineWidth = 5;
            ctx.beginPath();
            ctx.moveTo(-35, -40);
            ctx.lineTo(5, 5);
            ctx.stroke();
        }
    } else {
        // Generic Pill / Tablet
        ctx.fillStyle = '#edf2f7';
        ctx.strokeStyle = '#cbd5e0';
        ctx.lineWidth = 4;
        ctx.beginPath();
        ctx.arc(0, 0, 95, 0, Math.PI * 2);
        ctx.fill();
        ctx.stroke();

        // Center split line
        ctx.strokeStyle = '#a0aec0';
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.moveTo(0, -90);
        ctx.lineTo(0, 90);
        ctx.stroke();

        if (kind === 'defect') {
            // Chipped edge
            ctx.fillStyle = '#1a202c';
            ctx.beginPath();
            ctx.arc(80, -40, 25, 0, Math.PI * 2);
            ctx.fill();

            // Discoloration stain
            ctx.fillStyle = 'rgba(183, 121, 31, 0.7)';
            ctx.beginPath();
            ctx.ellipse(-30, 25, 18, 12, Math.PI / 3, 0, Math.PI * 2);
            ctx.fill();
        }
    }

    ctx.restore();

    // Inspection timestamp & category watermark in corner
    ctx.font = '11px monospace';
    ctx.fillStyle = 'rgba(255, 255, 255, 0.4)';
    ctx.fillText(`EVT-CLIP++ TEST BENCH: ${category.toUpperCase()} [${kind.toUpperCase()}]`, 16, 496);

    return new Promise((resolve) => {
        canvas.toBlob((blob) => {
            const fileName = `demo_${category}_${kind}.png`;
            const file = new File([blob], fileName, { type: 'image/png' });
            resolve(file);
        }, 'image/png');
    });
};
