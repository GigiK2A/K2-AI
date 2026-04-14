const HERO_VIDEO_PLAYBACK_RATE = 1.15;
const HERO_VIDEO_VERSION = '20260414-3';
const HERO_MEDIA = {
  mobileVideo: `/hero-mobile.mp4?v=${HERO_VIDEO_VERSION}`,
  portraitVideo: `/hero-portrait-k2.mp4?v=${HERO_VIDEO_VERSION}`,
  landscapeVideo: `/hero-landscape-k2.mp4?v=${HERO_VIDEO_VERSION}`,
  mobilePoster: '/hero-mobile-static.png',
  portraitPoster: '/hero-portrait-k2-static.png',
  landscapePoster: '/hero-landscape-k2-static.png'
};

document.addEventListener('DOMContentLoaded', () => {
  const section = document.querySelector('.hero-video-section');
  const video = document.getElementById('hero-video');
  const staticFrameImg = section?.querySelector('.hero-static-frame img');
  const content = document.getElementById('hero-content');
  const navbar = document.getElementById('navbar');

  if (!content || !navbar) return;

  let hasShownContent = false;
  let videoFallback = null;

  function showContent() {
    if (hasShownContent) return;
    hasShownContent = true;
    content.classList.add('visible');
    navbar.classList.add('visible');
  }

  function cleanupVideo() {
    if (!video) return;

    video.pause();
    video.removeAttribute('src');
    video.querySelectorAll('source').forEach((source) => source.removeAttribute('src'));
    video.load();
  }

  function isPortraitViewport() {
    return window.matchMedia('(orientation: portrait)').matches || window.innerHeight > window.innerWidth;
  }

  function isMobileViewport() {
    return window.matchMedia('(max-width: 900px)').matches;
  }

  function applyHeroMedia() {
    if (!video) return;
    const portrait = isPortraitViewport();
    const mobile = isMobileViewport();
    let nextVideo = HERO_MEDIA.landscapeVideo;
    let nextPoster = HERO_MEDIA.landscapePoster;

    if (mobile && portrait) {
      nextVideo = HERO_MEDIA.mobileVideo;
      nextPoster = HERO_MEDIA.mobilePoster;
    } else if (portrait) {
      nextVideo = HERO_MEDIA.portraitVideo;
      nextPoster = HERO_MEDIA.portraitPoster;
    }

    if (staticFrameImg) {
      staticFrameImg.src = nextPoster;
    }

    if (video.dataset.mediaSrc === nextVideo) {
      return;
    }

    video.dataset.mediaSrc = nextVideo;
    video.poster = nextPoster;
    video.setAttribute('poster', nextPoster);
    video.src = nextVideo;
    video.load();
  }

  function skipIntro() {
    document.documentElement.classList.add('skip-home-intro');
    section?.classList.add('is-static');
    cleanupVideo();
    showContent();
  }

  if (!video) {
    showContent();
    return;
  }

  applyHeroMedia();

  if (document.documentElement.classList.contains('skip-home-intro')) {
    skipIntro();
    return;
  }

  video.muted = true;
  video.playsInline = true;
  video.playbackRate = HERO_VIDEO_PLAYBACK_RATE;
  video.loop = false;

  video.addEventListener('error', skipIntro, { once: true });

  video.addEventListener('ended', showContent, { once: true });

  video.addEventListener('playing', () => {
    window.clearTimeout(videoFallback);
    const remainingSeconds = Number.isFinite(video.duration) && video.duration > 0
      ? Math.max(1, (video.duration - video.currentTime) / Math.max(0.1, video.playbackRate))
      : 8;
    videoFallback = window.setTimeout(showContent, Math.ceil((remainingSeconds + 1) * 1000));
  }, { once: true });

  video.preload = 'auto';
  const onViewportChange = () => {
    if (!document.documentElement.classList.contains('skip-home-intro') && !section?.classList.contains('is-static')) {
      applyHeroMedia();
    }
  };
  window.addEventListener('resize', onViewportChange, { passive: true });

  const playPromise = video.play();
  if (playPromise && typeof playPromise.catch === 'function') {
    playPromise.catch(showContent);
  }
});
