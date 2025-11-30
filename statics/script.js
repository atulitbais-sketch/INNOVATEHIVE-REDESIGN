// Carousel, form submit to Flask, and scroll animations

document.addEventListener('DOMContentLoaded', function () {

  /* ---------------------- CAROUSEL ---------------------- */
  const track = document.querySelector('.carousel-track');
  const items = document.querySelectorAll('.carousel-item');
  const prevBtn = document.querySelector('.carousel-btn.prev');
  const nextBtn = document.querySelector('.carousel-btn.next');
  let index = 0;

  function updateCarousel() {
    const width = document.querySelector('.carousel').offsetWidth;
    track.style.transform = `translateX(-${index * width}px)`;
  }

  nextBtn.addEventListener('click', () => {
    index = (index + 1) % items.length;
    updateCarousel();
  });

  prevBtn.addEventListener('click', () => {
    index = (index - 1 + items.length) % items.length;
    updateCarousel();
  });

  window.addEventListener('resize', updateCarousel);
  updateCarousel();


  /* ---------------------- CONTACT FORM → FLASK ---------------------- */
  const form = document.getElementById('contactForm');
  const formMsg = document.getElementById('formMsg');

  form.addEventListener('submit', async (e) => {
  e.preventDefault();

  formMsg.textContent = "Sending...";
  formMsg.style.color = "";

  const formData = new FormData(form);

  try {
    const res = await fetch("/contact", {
      method: "POST",
      body: formData,
      headers: { "X-Requested-With": "XMLHttpRequest" }
    });

    // Safely read response
    const text = await res.text();
    let data = null;
    try {
      data = JSON.parse(text);
    } catch (e) {
      // Not JSON → probably HTML error page
    }

    if (res.ok && data?.ok) {
      formMsg.textContent = data.message || "Thank you! We'll be in touch soon.";
      formMsg.style.color = "#4ade80";
      form.reset();
    } else {
      const errorMsg = data?.errors?.join(', ') || "Something went wrong. Please try again.";
      formMsg.textContent = errorMsg;
      formMsg.style.color = "#f87171";
    }
  } catch (err) {
    formMsg.textContent = "Connection failed. Please check your internet.";
    formMsg.style.color = "#f87171";
  }

  setTimeout(() => {
    formMsg.textContent = "";
  }, 8000);
});

  /* ---------------------- FADE UP ANIMATIONS ---------------------- */
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(ent => {
      if (ent.isIntersecting) ent.target.classList.add('in-view');
    });
  }, { threshold: 0.12 });

  document.querySelectorAll('.fade-up').forEach(el => observer.observe(el));
});
