/**
 * Holographic 3D Particle Background
 * Tiny floating particles with depth, glow, and parallax effects
 */

class HolographicParticles {
    constructor() {
        // Create canvas
        this.canvas = document.createElement('canvas');
        this.canvas.id = 'particle-canvas';
        this.canvas.style.position = 'fixed';
        this.canvas.style.top = '0';
        this.canvas.style.left = '0';
        this.canvas.style.width = '100%';
        this.canvas.style.height = '100%';
        this.canvas.style.zIndex = '0';
        this.canvas.style.pointerEvents = 'none';
        document.body.appendChild(this.canvas);

        this.ctx = this.canvas.getContext('2d');
        this.resize();

        // 3D settings
        this.focalLength = 400;
        this.zRange = 1500;

        // Holographic neon colors
        this.colors = [
            '#00ffff', // cyan
            '#ff00ff', // magenta
            '#9d00ff', // purple
            '#0080ff', // blue
            '#ff0080', // pink
            '#00ff88', // teal
            '#ff0099', // hot pink
            '#00ccff'  // light blue
        ];

        this.createParticles();

        window.addEventListener('resize', () => this.resize());

        this.animate();
    }

    resize() {
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
        this.cx = this.canvas.width / 2;
        this.cy = this.canvas.height / 2;
    }

    createParticles() {
        // Create hundreds of tiny particles
        const particleCount = Math.floor((this.canvas.width * this.canvas.height) / 1200);
        this.particles = [];

        for (let i = 0; i < particleCount; i++) {
            this.particles.push({
                x: (Math.random() - 0.5) * this.canvas.width * 2,
                y: (Math.random() - 0.5) * this.canvas.height * 2,
                z: Math.random() * this.zRange,
                vx: (Math.random() - 0.5) * 0.6,
                vy: (Math.random() - 0.5) * 0.6,
                vz: (Math.random() - 0.5) * 1.5,
                color: this.colors[Math.floor(Math.random() * this.colors.length)],
                baseSize: Math.random() * 1 + 1.2, // 1.2-2.2px (slightly larger)
                phase: Math.random() * Math.PI * 2,
                blinkSpeed: Math.random() * 0.03 + 0.02,
                glowIntensity: Math.random() * 0.5 + 0.5
            });
        }
        console.log(`Created ${particleCount} holographic particles`);
    }

    update() {
        this.particles.forEach(p => {
            // Random drifting movement in all directions
            p.x += p.vx;
            p.y += p.vy;
            p.z += p.vz;

            // Blinking/pulsing effect
            p.phase += p.blinkSpeed;

            // Wrap around when particles go out of bounds
            const maxDist = Math.max(this.canvas.width, this.canvas.height) * 2;
            
            if (p.z < 1) {
                p.z = this.zRange;
                p.x = (Math.random() - 0.5) * maxDist;
                p.y = (Math.random() - 0.5) * maxDist;
            } else if (p.z > this.zRange) {
                p.z = 1;
                p.x = (Math.random() - 0.5) * maxDist;
                p.y = (Math.random() - 0.5) * maxDist;
            }

            if (Math.abs(p.x) > maxDist) {
                p.x = (Math.random() - 0.5) * maxDist;
            }
            if (Math.abs(p.y) > maxDist) {
                p.y = (Math.random() - 0.5) * maxDist;
            }
        });
    }

    draw() {
        // Clear canvas completely
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        // Additive blending for holographic glow
        this.ctx.globalCompositeOperation = 'lighter';

        // Sort particles by z-depth (far to near)
        const sorted = [...this.particles].sort((a, b) => b.z - a.z);

        sorted.forEach(p => {
            // 3D perspective projection
            const scale = this.focalLength / (this.focalLength + p.z);

            // Project to 2D without mouse parallax
            const x2d = this.cx + p.x * scale;
            const y2d = this.cy + p.y * scale;

            // Skip if off screen
            if (x2d < -50 || x2d > this.canvas.width + 50 || 
                y2d < -50 || y2d > this.canvas.height + 50) return;

            // Depth-of-field: closer particles are brighter
            const depthFade = 1 - (p.z / this.zRange);
            const alpha = Math.max(0.5, depthFade * 1.2);

            // Pulsing brightness
            const brightness = 0.7 + Math.sin(p.phase) * 0.3;

            // Particle size with perspective
            const size = p.baseSize * scale * (1 + brightness * 0.5);

            // Parse color to RGB
            const r = parseInt(p.color.slice(1, 3), 16);
            const g = parseInt(p.color.slice(3, 5), 16);
            const b = parseInt(p.color.slice(5, 7), 16);

            // Draw soft glow - reduced spread but vibrant
            const glowSize = size * 6 * p.glowIntensity;
            const gradient = this.ctx.createRadialGradient(x2d, y2d, 0, x2d, y2d, glowSize);
            gradient.addColorStop(0, `rgba(${r}, ${g}, ${b}, ${alpha * brightness})`);
            gradient.addColorStop(0.3, `rgba(${r}, ${g}, ${b}, ${alpha * brightness * 0.7})`);
            gradient.addColorStop(0.7, `rgba(${r}, ${g}, ${b}, ${alpha * 0.3})`);
            gradient.addColorStop(1, `rgba(${r}, ${g}, ${b}, 0)`);

            this.ctx.fillStyle = gradient;
            this.ctx.beginPath();
            this.ctx.arc(x2d, y2d, glowSize, 0, Math.PI * 2);
            this.ctx.fill();

            // Draw bright vibrant core
            this.ctx.fillStyle = `rgba(255, 255, 255, ${alpha * brightness * 1.1})`;
            this.ctx.beginPath();
            this.ctx.arc(x2d, y2d, size * 0.8, 0, Math.PI * 2);
            this.ctx.fill();
        });

        this.ctx.globalCompositeOperation = 'source-over';
    }

    animate() {
        this.update();
        this.draw();
        requestAnimationFrame(() => this.animate());
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        new HolographicParticles();
    });
} else {
    new HolographicParticles();
}
