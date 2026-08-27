document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".alert").forEach(function (alert) {
        setTimeout(function () {
            alert.classList.add("fade");
            alert.style.opacity = "0";
        }, 6000);
    });
});
