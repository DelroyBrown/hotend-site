const items = document.querySelectorAll('.list li');

setTimeout(() => {
  items.forEach((item, index) => {
    setTimeout(() => {
      item.classList.add('visible');
    }, index * 200);
  });
}, 500);
