if ($ === undefined) $ = CTFd.lib.$;

function update_configs(obj) {
    var target = "/plugins/ctfd-whale/admin/settings";
    var method = "PATCH";

    var params = {};

    Object.keys(obj).forEach(function(x) {
        if (obj[x] === "true") {
            params[x] = true;
        } else if (obj[x] === "false") {
            params[x] = false;
        } else {
            params[x] = obj[x];
        }
    });

    CTFd.fetch(target, {
            method: method,
            credentials: "same-origin",
            headers: {
                Accept: "application/json",
                "Content-Type": "application/json"
            },
            body: JSON.stringify(params)
        })
        .then(function(response) {
            return response.json();
        })
        .then(function(data) {
            window.location.reload();
        });
}
$(function() {
    $(".config-section > form:not(.form-upload)").submit(function(e) {
        e.preventDefault();
        var obj = $(this).serializeJSON();
        update_configs(obj);
    });
});