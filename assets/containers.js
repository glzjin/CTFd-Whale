const $ = CTFd.lib.$;

function htmlentities(str) {
    return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function copyToClipboard(event, str) {
    // Select element
    const el = document.createElement('textarea');
    el.value = str;
    el.setAttribute('readonly', '');
    el.style.position = 'absolute';
    el.style.left = '-9999px';
    document.body.appendChild(el);
    el.select();
    document.execCommand('copy');
    document.body.removeChild(el);

    $(event.target).tooltip({
        title: "Copied!",
        trigger: "manual"
    });
    $(event.target).tooltip("show");

    setTimeout(function () {
        $(event.target).tooltip("hide");
    }, 1500);
}

$(".click-copy").click(function (e) {
    copyToClipboard(e, $(this).data("copy"));
})

$(".delete-container").click(function (e) {
    e.preventDefault();
    var container_id = $(this).attr("container-id");
    var user_id = $(this).attr("user-id");

    var body = "<span>Are you sure you want to delete <strong>Container #{0}</strong>?</span>".format(
        htmlentities(container_id)
    );

    var row = $(this)
        .parent()
        .parent();

    CTFd.ui.ezq.ezQuery({
        title: "Destroy Container",
        body: body,
        success: async function () {
            let response = await CTFd.fetch("/api/v1/plugins/ctfd-whale/admin/container?user_id=" + user_id, {
                method: "DELETE",
                credentials: "same-origin",
                headers: {
                    Accept: "application/json",
                    "Content-Type": "application/json"
                }
            });
            response = await response.json();
            if (response.success !== true) {
                $(this).tooltip({
                    title: 'failed',
                    trigger: "manual"
                })
                $(this).tooltip("show");
                return;
            }
            location.reload();
        }
    });
});

$(".renew-container").click(function (e) {
    e.preventDefault();
    var container_id = $(this).attr("container-id");
    var challenge_id = $(this).attr("challenge-id");
    var user_id = $(this).attr("user-id");

    var body = "<span>Are you sure you want to renew <strong>Container #{0}</strong>?</span>".format(
        htmlentities(container_id)
    );

    CTFd.ui.ezq.ezQuery({
        title: "Renew Container",
        body: body,
        success: async function () {
            let response = await CTFd.fetch(
                "/api/v1/plugins/ctfd-whale/admin/container?user_id=" + user_id + "&challenge_id=" + challenge_id, {
                method: "PATCH",
                credentials: "same-origin",
                headers: {
                    Accept: "application/json",
                    "Content-Type": "application/json"
                }
            });
            response = await response.json();
            if (response.success === true) {
                CTFd.ui.ezq.ezAlert({
                    title: "Success",
                    body: "This instance has been renewed!",
                    button: "OK"
                })
            }
        }
    });
});