if ($ === undefined) $ = CTFd.lib.$;

function update_configs(obj) {
    Object.keys(obj).forEach(function (x) {
        if (obj[x] === "true") {
            obj[x] = true;
        } else if (obj[x] === "false") {
            obj[x] = false;
        }
    });

    CTFd.fetch("/api/v1/plugins/ctfd-whale/admin/settings", {
        method: "PATCH",
        credentials: "same-origin",
        headers: {
            "Accept": "application/json",
            "Content-Type": "application/json"
        },
        body: JSON.stringify(obj)
    })
        .then(function (response) {
            return response.json();
        })
        .then(function (data) {
            window.location.reload();
        });
}

$(function () {
    $(".config-section > form:not(.form-upload)").submit(function (e) {
        e.preventDefault();
        update_configs($(this).serializeJSON());
    });
});