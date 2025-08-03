function showLoader() {
    const loader = document.getElementById('global-loader');
    console.log("loader SHOW");
    // console.log(loader);
    if (loader) {
        //   console.log("loader SHOW");
        // setTimeout(() => {
            console.log("loader SHOW");
            loader.style.display = 'flex'; // Gunakan flex agar center
        // }, 5000);
    }
}

function hideLoader() {
    const loader = document.getElementById('global-loader');
    if (loader) {
        // setTimeout(() => {
            console.log("loader hide");
            loader.style.display = 'none';
        // }, 5000);
    }
}

// Sembunyikan loader saat halaman selesai dimuat
window.addEventListener('load', function () {
    // setTimeout(() => {
    //     hideLoader; // Gunakan flex agar center
    // }, 5000);
    hideLoader();
});

// Jika terjadi error JS, pastikan loader tidak stuck
window.addEventListener('error', function () {
    // setTimeout(() => {
    //     hideLoader; // Gunakan flex agar center
    // }, 5000);
    hideLoader();
});