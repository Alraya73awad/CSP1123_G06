function levelUpAnimation(newLevel) {
    const popup = document.getElementById('level-up-popup');
    const levelSound = document.getElementById('level-up-sound');

    document.getElementById('new-level').innerText = newLevel;

    popup.classList.remove("hidden");
    levelSound.play();

    setTimeout(() => {
        popup.classList.add("hidden");
    }, 3000);
}
