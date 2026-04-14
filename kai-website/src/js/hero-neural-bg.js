const canvas = document.getElementById('hero-neural-canvas');

if (canvas) {
  const ctx = canvas.getContext('2d');
  const reducedMotionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');

  let width = 0;
  let height = 0;
  let rafId = 0;
  let frame = 0;
  let started = false;
  let neurons = [];
  let pulses = [];

  function prng(seed) {
    let state = (seed ^ 0xDEADBEEF) >>> 0 || 1;
    const next = () => {
      state ^= state << 13;
      state ^= state >> 17;
      state ^= state << 5;
      return (state >>> 0) / 0xFFFFFFFF;
    };

    return {
      next,
      r: (min, max) => min + next() * (max - min),
      i: (min, max) => Math.floor(min + next() * (max - min + 0.9999)),
    };
  }

  function quadPoint(p0, p1, p2, t) {
    const u = 1 - t;
    return {
      x: (u * u * p0.x) + (2 * u * t * p1.x) + (t * t * p2.x),
      y: (u * u * p0.y) + (2 * u * t * p1.y) + (t * t * p2.y),
    };
  }

  function cubicPoint(p0, p1, p2, p3, t) {
    const u = 1 - t;
    return {
      x: (u * u * u * p0.x)
        + (3 * u * u * t * p1.x)
        + (3 * u * t * t * p2.x)
        + (t * t * t * p3.x),
      y: (u * u * u * p0.y)
        + (3 * u * u * t * p1.y)
        + (3 * u * t * t * p2.y)
        + (t * t * t * p3.y),
    };
  }

  function makeBranch(rng, originX, originY, angle, depth) {
    const length = rng.r(28, 78) * Math.pow(0.60, depth);
    const splay = rng.r(-0.58, 0.58);
    const midAngle = angle + splay;

    const startX = originX;
    const startY = originY;
    const midX = startX + (Math.cos(midAngle) * length * 0.5) + rng.r(-10, 10);
    const midY = startY + (Math.sin(midAngle) * length * 0.5) + rng.r(-10, 10);
    const endX = startX + (Math.cos(midAngle) * length);
    const endY = startY + (Math.sin(midAngle) * length);

    const branch = {
      startX,
      startY,
      midX,
      midY,
      endX,
      endY,
      width: Math.max(0.35, rng.r(2.0, 3.8) - (depth * 0.78)),
      children: [],
    };

    if (depth < 3) {
      const childCount = depth < 1 ? rng.i(1, 3) : rng.i(0, 2);
      for (let i = 0; i < childCount; i += 1) {
        const t = rng.r(0.45, 1.0);
        const split = quadPoint(
          { x: startX, y: startY },
          { x: midX, y: midY },
          { x: endX, y: endY },
          t,
        );

        branch.children.push(
          makeBranch(rng, split.x, split.y, angle + rng.r(-0.9, 0.9), depth + 1),
        );
      }
    }

    return branch;
  }

  function drawBranch(branch, alpha) {
    ctx.beginPath();
    ctx.moveTo(branch.startX, branch.startY);
    ctx.quadraticCurveTo(branch.midX, branch.midY, branch.endX, branch.endY);

    const value = Math.round(255 * alpha);
    ctx.strokeStyle = `rgb(${value}, ${value}, ${value})`;
    ctx.lineWidth = branch.width;
    ctx.stroke();

    for (const child of branch.children) {
      drawBranch(child, alpha * 0.70);
    }

    if (!branch.children.length) {
      ctx.beginPath();
      ctx.arc(branch.endX, branch.endY, branch.width * 0.9, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(255, 255, 255, ${alpha * 0.5})`;
      ctx.fill();
    }
  }

  class Neuron {
    constructor(x, y, seed) {
      this.x = x;
      this.y = y;

      const rng = prng(seed);
      this.somaRadius = rng.r(9, 22);
      this.brightness = rng.r(0.42, 1.0);
      this.pulsePhase = rng.r(0, Math.PI * 2);
      this.pulseSpeed = rng.r(0.22, 0.85);

      const dendriteCount = rng.i(5, 9);
      this.dendrites = [];
      const baseAngle = rng.r(0, Math.PI * 2);

      for (let i = 0; i < dendriteCount; i += 1) {
        const angle = baseAngle + ((i / dendriteCount) * Math.PI * 2) + rng.r(-0.30, 0.30);
        this.dendrites.push(makeBranch(rng, x, y, angle, 0));
      }

      const axonAngle = rng.r(0, Math.PI * 2);
      const axonLength = rng.r(65, 175);
      const p0 = {
        x: x + (Math.cos(axonAngle) * this.somaRadius),
        y: y + (Math.sin(axonAngle) * this.somaRadius),
      };

      const bend1 = axonAngle + rng.r(-0.4, 0.4);
      const bend2 = axonAngle + rng.r(-0.7, 0.7);

      this.axon = {
        p0,
        p1: {
          x: p0.x + (Math.cos(bend1) * axonLength * 0.33),
          y: p0.y + (Math.sin(bend1) * axonLength * 0.33),
        },
        p2: {
          x: p0.x + (Math.cos(bend2) * axonLength * 0.66),
          y: p0.y + (Math.sin(bend2) * axonLength * 0.66),
        },
        p3: {
          x: p0.x + (Math.cos(axonAngle) * axonLength),
          y: p0.y + (Math.sin(axonAngle) * axonLength),
        },
        terminalRadius: rng.r(2.5, 5),
        width: rng.r(0.8, 1.6),
      };
    }

    draw(time) {
      const pulse = 0.82 + (0.18 * Math.sin((time * this.pulseSpeed) + this.pulsePhase));
      const alpha = this.brightness * pulse;

      ctx.save();
      ctx.lineCap = 'round';
      ctx.lineJoin = 'round';

      const haloRadius = this.somaRadius * (3.8 + (pulse * 1.4));
      const haloGradient = ctx.createRadialGradient(this.x, this.y, 0, this.x, this.y, haloRadius);
      haloGradient.addColorStop(0, `rgba(255, 255, 255, ${alpha * 0.20})`);
      haloGradient.addColorStop(0.35, `rgba(200, 200, 200, ${alpha * 0.08})`);
      haloGradient.addColorStop(1, 'rgba(0, 0, 0, 0)');

      ctx.beginPath();
      ctx.arc(this.x, this.y, haloRadius, 0, Math.PI * 2);
      ctx.fillStyle = haloGradient;
      ctx.fill();

      for (const dendrite of this.dendrites) {
        drawBranch(dendrite, alpha * 0.86);
      }

      const { axon } = this;
      ctx.beginPath();
      ctx.moveTo(axon.p0.x, axon.p0.y);
      ctx.bezierCurveTo(axon.p1.x, axon.p1.y, axon.p2.x, axon.p2.y, axon.p3.x, axon.p3.y);
      ctx.strokeStyle = `rgba(255, 255, 255, ${alpha * 0.52})`;
      ctx.lineWidth = axon.width;
      ctx.stroke();

      const terminalGradient = ctx.createRadialGradient(
        axon.p3.x,
        axon.p3.y,
        0,
        axon.p3.x,
        axon.p3.y,
        axon.terminalRadius * 2.5,
      );
      terminalGradient.addColorStop(0, `rgba(255, 255, 255, ${alpha * 0.9})`);
      terminalGradient.addColorStop(1, 'rgba(0, 0, 0, 0)');

      ctx.beginPath();
      ctx.arc(axon.p3.x, axon.p3.y, axon.terminalRadius * 2.5, 0, Math.PI * 2);
      ctx.fillStyle = terminalGradient;
      ctx.fill();

      ctx.beginPath();
      ctx.arc(axon.p3.x, axon.p3.y, axon.terminalRadius, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(255, 255, 255, ${alpha * 0.85})`;
      ctx.fill();

      const somaGradient = ctx.createRadialGradient(
        this.x - (this.somaRadius * 0.28),
        this.y - (this.somaRadius * 0.28),
        0,
        this.x,
        this.y,
        this.somaRadius,
      );
      somaGradient.addColorStop(0, `rgba(255, 255, 255, ${alpha})`);
      somaGradient.addColorStop(0.55, `rgba(215, 215, 215, ${alpha * 0.85})`);
      somaGradient.addColorStop(1, `rgba(130, 130, 130, ${alpha * 0.3})`);

      ctx.beginPath();
      ctx.arc(this.x, this.y, this.somaRadius, 0, Math.PI * 2);
      ctx.fillStyle = somaGradient;
      ctx.fill();

      const nucleusGradient = ctx.createRadialGradient(
        this.x - (this.somaRadius * 0.18),
        this.y - (this.somaRadius * 0.18),
        0,
        this.x,
        this.y,
        this.somaRadius * 0.44,
      );
      nucleusGradient.addColorStop(0, `rgba(255, 255, 255, ${alpha * 0.95})`);
      nucleusGradient.addColorStop(1, `rgba(170, 170, 170, ${alpha * 0.3})`);

      ctx.beginPath();
      ctx.arc(this.x, this.y, this.somaRadius * 0.44, 0, Math.PI * 2);
      ctx.fillStyle = nucleusGradient;
      ctx.fill();

      ctx.restore();
    }
  }

  class Pulse {
    constructor(neuron) {
      this.neuron = neuron;
      this.t = 0;
      this.speed = 0.004 + (Math.random() * 0.012);
      this.alpha = 0.55 + (Math.random() * 0.45);
      this.size = 3 + (Math.random() * 7);
    }

    update() {
      this.t += this.speed;
      return this.t <= 1;
    }

    draw() {
      const point = cubicPoint(
        this.neuron.axon.p0,
        this.neuron.axon.p1,
        this.neuron.axon.p2,
        this.neuron.axon.p3,
        this.t,
      );

      const glow = ctx.createRadialGradient(point.x, point.y, 0, point.x, point.y, this.size * 5);
      glow.addColorStop(0, `rgba(255, 255, 255, ${this.alpha})`);
      glow.addColorStop(0.22, `rgba(235, 235, 235, ${this.alpha * 0.5})`);
      glow.addColorStop(1, 'rgba(0, 0, 0, 0)');

      ctx.beginPath();
      ctx.arc(point.x, point.y, this.size * 5, 0, Math.PI * 2);
      ctx.fillStyle = glow;
      ctx.fill();

      ctx.beginPath();
      ctx.arc(point.x, point.y, this.size * 0.65, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(255, 255, 255, ${this.alpha})`;
      ctx.fill();
    }
  }

  function spawnPulse() {
    if (!neurons.length) return;
    const neuron = neurons[Math.floor(Math.random() * neurons.length)];
    pulses.push(new Pulse(neuron));
  }

  function initNetwork() {
    neurons = [];
    pulses = [];

    const cellW = 148;
    const cellH = 140;
    const cols = Math.ceil(width / cellW) + 1;
    const rows = Math.ceil(height / cellH) + 1;

    let seed = 7919;
    for (let row = 0; row < rows; row += 1) {
      for (let col = 0; col < cols; col += 1) {
        const rng = prng(seed);
        seed += 1;

        if (rng.next() < 0.18) continue;

        const x = ((col - 0.5) * cellW) + rng.r(10, cellW - 10);
        const y = ((row - 0.5) * cellH) + rng.r(10, cellH - 10);
        const neuronSeed = (seed * 251) + (col * 1009) + (row * 3571);
        neurons.push(new Neuron(x, y, neuronSeed));
      }
    }

    for (let i = 0; i < 30; i += 1) {
      spawnPulse();
    }
  }

  function render(timestamp) {
    if (document.hidden || reducedMotionQuery.matches) {
      rafId = 0;
      return;
    }

    frame += 1;
    ctx.fillStyle = 'rgba(0, 0, 0, 0.20)';
    ctx.fillRect(0, 0, width, height);

    const time = timestamp * 0.001;
    for (const neuron of neurons) {
      neuron.draw(time);
    }

    pulses = pulses.filter((pulse) => {
      const isAlive = pulse.update();
      if (isAlive) pulse.draw();
      return isAlive;
    });

    if (frame % 14 === 0) spawnPulse();
    if (pulses.length < neurons.length * 0.5) spawnPulse();

    rafId = window.requestAnimationFrame(render);
  }

  function resizeCanvas() {
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const bounds = canvas.getBoundingClientRect();

    width = Math.max(1, Math.floor(bounds.width * dpr));
    height = Math.max(1, Math.floor(bounds.height * dpr));

    canvas.width = width;
    canvas.height = height;
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.scale(dpr, dpr);

    width = Math.floor(bounds.width);
    height = Math.floor(bounds.height);

    ctx.fillStyle = '#000';
    ctx.fillRect(0, 0, width, height);

    frame = 0;
    initNetwork();
  }

  function startLoop() {
    if (rafId || reducedMotionQuery.matches) return;
    if (!started) {
      canvas.parentElement?.classList.add('neural-ready');
      started = true;
    }
    rafId = window.requestAnimationFrame(render);
  }

  function stopLoop() {
    if (!rafId) return;
    window.cancelAnimationFrame(rafId);
    rafId = 0;
  }

  function handleVisibility() {
    if (document.hidden) {
      stopLoop();
      return;
    }

    resizeCanvas();
    startLoop();
  }

  function handleReducedMotionChange() {
    if (reducedMotionQuery.matches) {
      stopLoop();
      return;
    }

    resizeCanvas();
    startLoop();
  }

  if (ctx) {
    resizeCanvas();
    startLoop();

    window.addEventListener('resize', resizeCanvas, { passive: true });
    document.addEventListener('visibilitychange', handleVisibility);
    reducedMotionQuery.addEventListener('change', handleReducedMotionChange);
  }
}
