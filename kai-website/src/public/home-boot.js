(function () {
  try {
    var introSeen = sessionStorage.getItem('kai-home-intro-seen') === '1';
    var referrer = document.referrer ? new URL(document.referrer) : null;
    var current = window.location;
    var cameFromInternalPage =
      referrer &&
      referrer.origin === current.origin &&
      referrer.pathname !== current.pathname;

    if (introSeen || cameFromInternalPage) {
      sessionStorage.setItem('kai-home-intro-seen', '1');
      document.documentElement.classList.add('skip-home-intro');
    }
  } catch (error) {
    console.error('Home boot error:', error);
  }
})();
